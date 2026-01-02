"""
WebSocket屏幕流服务
实现实时屏幕推送、增量更新、帧率控制
"""

import asyncio
import time
import hashlib
import io
from typing import Dict, Set, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from PIL import Image


class StreamQuality(Enum):
    """流质量级别"""
    LOW = "low"        # 480p, quality=50, 30fps - 流畅
    MEDIUM = "medium"  # 640p, quality=55, 25fps - 平衡
    HIGH = "high"      # 720p, quality=60, 20fps - 高清


@dataclass
class StreamConfig:
    """流配置"""
    quality: StreamQuality = StreamQuality.MEDIUM
    target_fps: int = 25
    jpeg_quality: int = 55
    max_width: int = 640
    send_unchanged: bool = False  # 是否发送未变化的帧

    @classmethod
    def from_quality(cls, quality: StreamQuality) -> "StreamConfig":
        configs = {
            StreamQuality.LOW: cls(
                quality=StreamQuality.LOW,
                target_fps=30,
                jpeg_quality=50,
                max_width=480
            ),
            StreamQuality.MEDIUM: cls(
                quality=StreamQuality.MEDIUM,
                target_fps=25,
                jpeg_quality=55,
                max_width=640
            ),
            StreamQuality.HIGH: cls(
                quality=StreamQuality.HIGH,
                target_fps=20,
                jpeg_quality=60,
                max_width=720
            ),
        }
        return configs.get(quality, configs[StreamQuality.MEDIUM])


@dataclass
class StreamStats:
    """流统计信息"""
    frames_sent: int = 0
    frames_skipped: int = 0
    bytes_sent: int = 0
    start_time: float = field(default_factory=time.time)
    last_frame_time: float = 0
    avg_capture_ms: float = 0
    avg_send_ms: float = 0
    current_fps: float = 0

    def to_dict(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            "frames_sent": self.frames_sent,
            "frames_skipped": self.frames_skipped,
            "bytes_sent": self.bytes_sent,
            "elapsed_seconds": round(elapsed, 2),
            "avg_fps": round(self.frames_sent / max(elapsed, 0.001), 1),
            "current_fps": round(self.current_fps, 1),
            "avg_capture_ms": round(self.avg_capture_ms, 1),
            "avg_send_ms": round(self.avg_send_ms, 1),
            "efficiency": round(self.frames_sent / max(self.frames_sent + self.frames_skipped, 1) * 100, 1)
        }


class ScreenStreamManager:
    """屏幕流管理器 - 管理多个设备的实时流"""

    def __init__(self, ui_analyzer):
        self.ui_analyzer = ui_analyzer
        self._active_streams: Dict[str, "DeviceStream"] = {}
        self._frame_cache: Dict[str, bytes] = {}
        self._frame_hash: Dict[str, str] = {}

    def get_stream(self, device_id: str) -> Optional["DeviceStream"]:
        """获取设备流"""
        return self._active_streams.get(device_id)

    def create_stream(self, device_id: str, config: StreamConfig = None) -> "DeviceStream":
        """创建或获取设备流"""
        if device_id not in self._active_streams:
            stream = DeviceStream(
                device_id=device_id,
                ui_analyzer=self.ui_analyzer,
                config=config or StreamConfig(),
                manager=self
            )
            self._active_streams[device_id] = stream
        return self._active_streams[device_id]

    def remove_stream(self, device_id: str):
        """移除设备流"""
        if device_id in self._active_streams:
            stream = self._active_streams[device_id]
            stream.stop()
            del self._active_streams[device_id]

    def get_cached_frame(self, device_id: str) -> Optional[bytes]:
        """获取缓存的帧"""
        return self._frame_cache.get(device_id)

    def update_frame_cache(self, device_id: str, frame_data: bytes):
        """更新帧缓存"""
        self._frame_cache[device_id] = frame_data
        self._frame_hash[device_id] = hashlib.md5(frame_data).hexdigest()[:16]

    def get_frame_hash(self, device_id: str) -> Optional[str]:
        """获取帧哈希"""
        return self._frame_hash.get(device_id)

    def get_all_stats(self) -> Dict[str, dict]:
        """获取所有流的统计信息"""
        return {
            device_id: stream.stats.to_dict()
            for device_id, stream in self._active_streams.items()
        }


class DeviceStream:
    """单个设备的屏幕流"""

    def __init__(self, device_id: str, ui_analyzer, config: StreamConfig, manager: ScreenStreamManager):
        self.device_id = device_id
        self.ui_analyzer = ui_analyzer
        self.config = config
        self.manager = manager

        self._subscribers: Set[Callable] = set()
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self.stats = StreamStats()

        # 帧间隔计算（确保target_fps至少为1避免除零）
        safe_fps = max(1, config.target_fps)
        self._frame_interval = 1.0 / safe_fps
        self._last_hash: Optional[str] = None

        # 性能追踪
        self._capture_times: list = []
        self._send_times: list = []
        self._fps_window: list = []

    def subscribe(self, callback: Callable):
        """订阅帧更新"""
        self._subscribers.add(callback)
        if not self._is_running and len(self._subscribers) > 0:
            self.start()

    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        self._subscribers.discard(callback)
        if len(self._subscribers) == 0:
            self.stop()

    def start(self):
        """启动流"""
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._stream_loop())

    def stop(self):
        """停止流"""
        self._is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _stream_loop(self):
        """流主循环"""
        while self._is_running:
            loop_start = time.time()

            try:
                # 捕获帧
                capture_start = time.time()
                frame_data = await self._capture_frame()
                capture_time = (time.time() - capture_start) * 1000

                if frame_data:
                    # 计算哈希检测变化
                    current_hash = hashlib.md5(frame_data).hexdigest()[:16]
                    is_changed = current_hash != self._last_hash

                    if is_changed or self.config.send_unchanged:
                        # 发送帧
                        send_start = time.time()
                        await self._broadcast_frame(frame_data, is_changed)
                        send_time = (time.time() - send_start) * 1000

                        # 更新统计
                        self.stats.frames_sent += 1
                        self.stats.bytes_sent += len(frame_data)
                        self._last_hash = current_hash

                        # 更新缓存
                        self.manager.update_frame_cache(self.device_id, frame_data)

                        # 追踪性能
                        self._update_performance(capture_time, send_time)
                    else:
                        self.stats.frames_skipped += 1

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)
                continue

            # 计算需要等待的时间以维持目标帧率
            elapsed = time.time() - loop_start
            sleep_time = max(0, self._frame_interval - elapsed)

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

            # 更新实时FPS
            self._update_fps()

    async def _capture_frame(self) -> Optional[bytes]:
        """捕获一帧 - 优化速度版本"""
        try:
            device_manager = self.ui_analyzer.device_manager.get_device(self.device_id)
            if not device_manager or not device_manager.is_connected:
                return None

            loop = asyncio.get_running_loop()

            def capture():
                img = device_manager.device.screenshot()

                # 根据配置调整大小 - 使用BILINEAR更快
                if self.config.max_width and img.width > self.config.max_width:
                    ratio = self.config.max_width / img.width
                    new_size = (self.config.max_width, int(img.height * ratio))
                    # 使用BILINEAR重采样，比LANCZOS快很多
                    try:
                        img = img.resize(new_size, Image.Resampling.BILINEAR)
                    except AttributeError:
                        # Pillow < 9.1.0 兼容
                        img = img.resize(new_size, Image.BILINEAR)

                buffer = io.BytesIO()
                # 禁用optimize加速编码
                img.save(buffer, format='JPEG', quality=self.config.jpeg_quality, optimize=False)
                return buffer.getvalue()

            return await asyncio.wait_for(
                loop.run_in_executor(None, capture),
                timeout=1.0  # 减少超时时间
            )

        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    async def _broadcast_frame(self, frame_data: bytes, is_changed: bool):
        """广播帧给所有订阅者 - 支持二进制和JSON两种模式"""
        if not self._subscribers:
            return

        # 构建消息 - 不再包含base64数据，改为二进制发送
        metadata = {
            "type": "frame_meta",
            "device_id": self.device_id,
            "timestamp": time.time(),
            "changed": is_changed,
            "size": len(frame_data)
        }

        # 复制订阅者集合，避免迭代时修改
        subscribers_copy = set(self._subscribers)
        dead_subscribers = set()

        for callback in subscribers_copy:
            try:
                # 先发送元数据，再发送二进制帧
                await callback(metadata, frame_data)
            except Exception:
                dead_subscribers.add(callback)

        # 清理失效的订阅者
        if dead_subscribers:
            self._subscribers -= dead_subscribers

    def _update_performance(self, capture_time: float, send_time: float):
        """更新性能统计"""
        # 使用滑动窗口计算平均值
        window_size = 30

        self._capture_times.append(capture_time)
        self._send_times.append(send_time)

        if len(self._capture_times) > window_size:
            self._capture_times = self._capture_times[-window_size:]
            self._send_times = self._send_times[-window_size:]

        self.stats.avg_capture_ms = sum(self._capture_times) / len(self._capture_times)
        self.stats.avg_send_ms = sum(self._send_times) / len(self._send_times)

    def _update_fps(self):
        """更新FPS统计"""
        current_time = time.time()
        self._fps_window.append(current_time)

        # 保留最近1秒的时间戳
        cutoff = current_time - 1.0
        self._fps_window = [t for t in self._fps_window if t > cutoff]

        self.stats.current_fps = len(self._fps_window)
        self.stats.last_frame_time = current_time

    def update_config(self, config: StreamConfig):
        """更新配置"""
        self.config = config
        # 确保fps至少为1避免除零
        safe_fps = max(1, config.target_fps)
        self._frame_interval = 1.0 / safe_fps


class FrameBuffer:
    """帧缓冲区 - 用于平滑播放"""

    def __init__(self, max_frames: int = 5):
        self.max_frames = max_frames
        self._frames: list = []
        self._lock = asyncio.Lock()

    async def push(self, frame_data: bytes, timestamp: float):
        """添加帧"""
        async with self._lock:
            self._frames.append((frame_data, timestamp))
            if len(self._frames) > self.max_frames:
                self._frames.pop(0)

    async def pop(self) -> Optional[tuple]:
        """获取最旧的帧"""
        async with self._lock:
            if self._frames:
                return self._frames.pop(0)
            return None

    async def get_latest(self) -> Optional[bytes]:
        """获取最新帧"""
        async with self._lock:
            if self._frames:
                return self._frames[-1][0]
            return None

    @property
    def size(self) -> int:
        return len(self._frames)
