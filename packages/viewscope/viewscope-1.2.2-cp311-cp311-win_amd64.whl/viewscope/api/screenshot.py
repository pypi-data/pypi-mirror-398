"""
屏幕截图API路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
import sys

router = APIRouter()

def _get_ui():
    if 'main' in sys.modules:
        return sys.modules['main'].ui_analyzer
    import main
    return main.ui_analyzer

class ScreenshotRequest(BaseModel):
    device_id: str
    package_filter: Optional[str] = None

class ScreenshotResponse(BaseModel):
    success: bool
    screenshot: Optional[str] = None
    hierarchy: Optional[dict] = None
    device_info: Optional[dict] = None
    error: Optional[str] = None
    device_id: str

def get_ui_analyzer():
    """依赖注入：获取UI分析器"""
    return _get_ui()

@router.post("/screenshot", response_model=ScreenshotResponse)
async def capture_screenshot(
    device: str = Query(..., description="设备ID"),
    package: Optional[str] = Query(None, description="应用包名过滤"),
    analyzer=Depends(get_ui_analyzer)
):
    """截图并获取UI层次结构"""
    try:
        result = await analyzer.capture_with_hierarchy(device)

        return ScreenshotResponse(
            success=result["success"],
            screenshot=result.get("screenshot"),
            hierarchy=result.get("hierarchy"),
            device_info=result.get("device_info"),
            error=result.get("error"),
            device_id=device
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"截图失败: {str(e)}"
        )

@router.get("/screenshot/{screenshot_id}")
async def get_screenshot(screenshot_id: str):
    """获取指定ID的截图（占位符，未实现历史截图功能）"""
    raise HTTPException(
        status_code=501,
        detail="历史截图功能尚未实现"
    )