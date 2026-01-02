"""
WebSocket API路由
处理实时屏幕流、设备连接等WebSocket通信
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional, Dict, Set
import asyncio
import json
import time
import sys

router = APIRouter()

def _get_stream():
    """获取流管理器实例"""
    if 'main' in sys.modules:
        return sys.modules['main'].screen_stream_manager
    import main
    return main.screen_stream_manager

def _get_config():
    """获取StreamConfig和StreamQuality类"""
    from core.screen_stream import StreamConfig, StreamQuality
    return StreamConfig, StreamQuality

# 全局WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # device_id -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._stream_manager = None

    def set_stream_manager(self, stream_manager):
        """设置流管理器"""
        self._stream_manager = stream_manager

    async def connect(self, websocket: WebSocket, device_id: str):
        """接受新连接"""
        await websocket.accept()

        if device_id not in self._connections:
            self._connections[device_id] = set()
        self._connections[device_id].add(websocket)

    def disconnect(self, websocket: WebSocket, device_id: str):
        """断开连接"""
        if device_id in self._connections:
            self._connections[device_id].discard(websocket)
            if not self._connections[device_id]:
                del self._connections[device_id]

    async def broadcast_to_device(self, device_id: str, message: dict):
        """向设备的所有连接广播消息"""
        if device_id not in self._connections:
            return

        # 复制集合避免迭代时修改
        connections_copy = set(self._connections[device_id])
        dead_connections = set()

        for websocket in connections_copy:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # 清理失效连接
        if dead_connections and device_id in self._connections:
            self._connections[device_id] -= dead_connections

    def get_connection_count(self, device_id: str) -> int:
        """获取设备连接数"""
        return len(self._connections.get(device_id, set()))


# 全局连接管理器实例
manager = ConnectionManager()


def get_stream_manager():
    """获取流管理器（延迟导入避免循环依赖）"""
    return _get_stream()


@router.websocket("/ws/screen/{device_id}")
async def screen_stream_websocket(
    websocket: WebSocket,
    device_id: str
):
    """
    实时屏幕流WebSocket端点

    消息格式:
    - 帧数据: {"type": "frame", "device_id": "...", "data": "base64...", "changed": true}
    - 统计: {"type": "stats", "fps": 20, "latency_ms": 50}
    - 错误: {"type": "error", "message": "..."}

    客户端命令:
    - {"cmd": "pause"} - 暂停流
    - {"cmd": "resume"} - 恢复流
    - {"cmd": "quality", "value": "high"} - 更改质量
    - {"cmd": "fps", "value": 30} - 更改帧率
    """
    # 从WebSocket URL解析query参数
    query_params = dict(websocket.query_params)
    quality = query_params.get("quality", "medium")
    try:
        fps = int(query_params.get("fps", 20))
    except (ValueError, TypeError):
        fps = 20

    await manager.connect(websocket, device_id)

    device_stream = None
    on_frame = None

    try:
        stream_manager = get_stream_manager()
        StreamConfig, StreamQuality = _get_config()

        # 解析质量配置
        quality_map = {
            "low": StreamQuality.LOW,
            "medium": StreamQuality.MEDIUM,
            "high": StreamQuality.HIGH
        }
        stream_quality = quality_map.get(quality.lower(), StreamQuality.MEDIUM)
        config = StreamConfig.from_quality(stream_quality)
        config.target_fps = min(fps, 30)  # 限制最大帧率

        # 创建设备流
        device_stream = stream_manager.create_stream(device_id, config)

        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "device_id": device_id,
            "config": {
                "quality": quality,
                "target_fps": config.target_fps,
                "jpeg_quality": config.jpeg_quality
            }
        })

        # 发送最后一帧（如果有）快速响应 - 使用二进制
        last_frame = stream_manager.get_cached_frame(device_id)
        if last_frame:
            # 先发送元数据
            await websocket.send_json({
                "type": "frame_meta",
                "device_id": device_id,
                "size": len(last_frame),
                "changed": False,
                "cached": True
            })
            # 再发送二进制帧
            await websocket.send_bytes(last_frame)

        # 订阅帧更新 - 新的二进制回调
        async def on_frame(metadata: dict, frame_data: bytes):
            try:
                # 先发送元数据JSON
                await websocket.send_json(metadata)
                # 再发送二进制帧数据
                await websocket.send_bytes(frame_data)
            except Exception:
                device_stream.unsubscribe(on_frame)

        device_stream.subscribe(on_frame)

        # 处理客户端消息
        while True:
            try:
                # 接收客户端命令
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30秒心跳超时
                )

                try:
                    cmd = json.loads(data)

                    if cmd.get("cmd") == "pause":
                        device_stream.unsubscribe(on_frame)
                        await websocket.send_json({"type": "paused"})

                    elif cmd.get("cmd") == "resume":
                        device_stream.subscribe(on_frame)
                        await websocket.send_json({"type": "resumed"})

                    elif cmd.get("cmd") == "quality":
                        new_quality = quality_map.get(cmd.get("value", "medium"), StreamQuality.MEDIUM)
                        new_config = StreamConfig.from_quality(new_quality)
                        device_stream.update_config(new_config)
                        await websocket.send_json({
                            "type": "config_updated",
                            "quality": cmd.get("value")
                        })

                    elif cmd.get("cmd") == "fps":
                        new_fps = max(1, min(int(cmd.get("value", 20)), 30))  # 限制1-30
                        device_stream.config.target_fps = new_fps
                        device_stream._frame_interval = 1.0 / new_fps
                        await websocket.send_json({
                            "type": "config_updated",
                            "fps": new_fps
                        })

                    elif cmd.get("cmd") == "stats":
                        await websocket.send_json({
                            "type": "stats",
                            **device_stream.stats.to_dict()
                        })

                    elif cmd.get("cmd") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": time.time()
                        })

                except json.JSONDecodeError:
                    pass  # 忽略无效JSON

            except asyncio.TimeoutError:
                # 发送心跳
                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": time.time()
                    })
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except Exception:
            pass
    finally:
        # 清理订阅，避免向已关闭的websocket发送数据
        if device_stream and on_frame:
            try:
                device_stream.unsubscribe(on_frame)
            except Exception:
                pass
        manager.disconnect(websocket, device_id)


@router.websocket("/ws/events/{device_id}")
async def device_events_websocket(
    websocket: WebSocket,
    device_id: str
):
    """
    设备事件WebSocket端点
    用于接收设备状态变化、UI更新等事件
    """
    await manager.connect(websocket, device_id)

    try:
        await websocket.send_json({
            "type": "connected",
            "device_id": device_id
        })

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )

                # 处理客户端事件
                try:
                    event = json.loads(data)

                    if event.get("type") == "click":
                        # 处理点击事件
                        x, y = event.get("x", 0), event.get("y", 0)
                        await websocket.send_json({
                            "type": "click_ack",
                            "x": x,
                            "y": y,
                            "status": "received"
                        })

                    elif event.get("type") == "refresh":
                        # 触发刷新
                        await websocket.send_json({
                            "type": "refresh_started"
                        })

                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # 心跳
                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": time.time()
                    })
                except Exception:
                    break  # 发送失败则退出循环

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket, device_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计"""
    stream_manager = get_stream_manager()

    return {
        "active_streams": stream_manager.get_all_stats() if stream_manager else {},
        "connections": {
            device_id: manager.get_connection_count(device_id)
            for device_id in manager._connections.keys()
        }
    }
