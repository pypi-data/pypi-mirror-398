"""
屏幕截图API路由
支持普通截图、快速截图、增量更新
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import base64
import time
import sys

router = APIRouter()

def _get_ui():
    """获取UI分析器实例"""
    if 'main' in sys.modules:
        return sys.modules['main'].ui_analyzer
    import main
    return main.ui_analyzer

def _get_stream():
    """获取流管理器实例"""
    if 'main' in sys.modules:
        return sys.modules['main'].screen_stream_manager
    import main
    return main.screen_stream_manager

class ScreenshotRequest(BaseModel):
    device_id: str
    package_filter: Optional[str] = None

class ScreenshotResponse(BaseModel):
    success: bool
    screenshot: Optional[str] = None
    hierarchy: Optional[dict] = None
    error: Optional[str] = None
    device_id: str
    device_info: Optional[dict] = None
    performance: Optional[dict] = None

def get_ui_analyzer():
    """依赖注入：获取UI分析器"""
    return _get_ui()

def get_stream_manager():
    """依赖注入：获取流管理器"""
    return _get_stream()

@router.post("/screenshot", response_model=ScreenshotResponse)
async def capture_screenshot(
    device: str = Query(..., description="设备ID"),
    package: Optional[str] = Query(None, description="应用包名过滤"),
    analyzer=Depends(get_ui_analyzer)
):
    """截图并获取UI层次结构（优化版本，并行执行）"""
    try:
        start_time = time.time()
        result = await analyzer.capture_with_hierarchy(device)
        elapsed = time.time() - start_time

        return ScreenshotResponse(
            success=result["success"],
            screenshot=result.get("screenshot"),
            hierarchy=result.get("hierarchy"),
            error=result.get("error"),
            device_id=device,
            device_info=result.get("device_info"),
            performance=result.get("performance")
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"截图失败: {str(e)}"
        )

@router.get("/screenshot/fast")
async def fast_screenshot(
    device: str = Query(..., description="设备ID"),
    quality: int = Query(80, description="JPEG质量(1-100)"),
    analyzer=Depends(get_ui_analyzer)
):
    """
    快速截图 - 仅返回图片，不包含UI层次结构
    适用于实时预览场景，延迟更低
    """
    try:
        start_time = time.time()

        # 直接获取帧数据
        frame_data = await analyzer.capture_frame_raw(device)

        if frame_data is None:
            raise HTTPException(status_code=404, detail="设备未连接或截图失败")

        elapsed = time.time() - start_time

        # 直接返回JPEG图片
        return Response(
            content=frame_data,
            media_type="image/jpeg",
            headers={
                "X-Capture-Time-Ms": str(int(elapsed * 1000)),
                "X-Frame-Size": str(len(frame_data)),
                "Cache-Control": "no-cache"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"快速截图失败: {str(e)}")

@router.get("/screenshot/incremental")
async def incremental_screenshot(
    device: str = Query(..., description="设备ID"),
    last_hash: Optional[str] = Query(None, description="上一帧哈希，用于增量检测"),
    analyzer=Depends(get_ui_analyzer),
    stream_manager=Depends(get_stream_manager)
):
    """
    增量截图 - 仅在屏幕变化时返回新帧
    返回304表示屏幕无变化
    """
    try:
        start_time = time.time()

        # 获取增量帧
        result = await analyzer.capture_frame_incremental(device)

        if result is None:
            raise HTTPException(status_code=404, detail="设备未连接或截图失败")

        frame_data, is_changed = result

        # 更新流管理器缓存
        if is_changed:
            stream_manager.update_frame_cache(device, frame_data)

        current_hash = stream_manager.get_frame_hash(device) or ""

        elapsed = time.time() - start_time

        # 如果客户端提供了hash且未变化，返回304
        if last_hash and last_hash == current_hash and not is_changed:
            return Response(
                status_code=304,
                headers={
                    "X-Frame-Hash": current_hash,
                    "X-Changed": "false"
                }
            )

        # 返回新帧
        return Response(
            content=frame_data,
            media_type="image/jpeg",
            headers={
                "X-Capture-Time-Ms": str(int(elapsed * 1000)),
                "X-Frame-Size": str(len(frame_data)),
                "X-Frame-Hash": current_hash,
                "X-Changed": "true" if is_changed else "false",
                "Cache-Control": "no-cache"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增量截图失败: {str(e)}")

@router.get("/screenshot/cached")
async def get_cached_screenshot(
    device: str = Query(..., description="设备ID"),
    stream_manager=Depends(get_stream_manager)
):
    """
    获取缓存的最后一帧
    适用于快速显示，无需等待新截图
    """
    frame_data = stream_manager.get_cached_frame(device)

    if frame_data is None:
        raise HTTPException(status_code=404, detail="没有缓存的帧")

    return Response(
        content=frame_data,
        media_type="image/jpeg",
        headers={
            "X-Frame-Hash": stream_manager.get_frame_hash(device) or "",
            "X-Cached": "true",
            "Cache-Control": "no-cache"
        }
    )

@router.get("/screenshot/{screenshot_id}")
async def get_screenshot(screenshot_id: str):
    """获取指定ID的截图（占位符，未实现历史截图功能）"""
    raise HTTPException(
        status_code=501,
        detail="历史截图功能尚未实现"
    )