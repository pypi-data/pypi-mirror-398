"""
元素操作API路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys

router = APIRouter()

def _get_ui():
    if 'main' in sys.modules:
        return sys.modules['main'].ui_analyzer
    import main
    return main.ui_analyzer

class ElementClickRequest(BaseModel):
    device: str
    selector: Dict[str, Any]

class ElementInputRequest(BaseModel):
    device: str
    selector: Dict[str, Any]
    text: str

def get_ui_analyzer():
    """依赖注入：获取UI分析器"""
    return _get_ui()

@router.get("/element/info")
async def get_element_info(
    device: str = Query(..., description="设备ID"),
    x: int = Query(..., description="X坐标"),
    y: int = Query(..., description="Y坐标"),
    analyzer=Depends(get_ui_analyzer)
):
    """获取指定坐标的元素信息"""
    try:
        device_manager = analyzer.device_manager.get_device(device)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 先获取当前UI层次结构
        hierarchy = await analyzer._get_ui_hierarchy(device_manager)
        
        # 查找指定位置的元素
        element = analyzer.find_element_at_position(hierarchy, x, y)
        
        if element:
            return {
                "success": True,
                "element": element,
                "position": {"x": x, "y": y}
            }
        else:
            return {
                "success": False,
                "error": "未找到该位置的元素",
                "position": {"x": x, "y": y}
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取元素信息失败: {str(e)}"
        )

@router.post("/element/click")
async def click_element(request: ElementClickRequest, analyzer=Depends(get_ui_analyzer)):
    """点击指定元素"""
    try:
        device_manager = analyzer.device_manager.get_device(request.device)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {request.device} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 构建选择器并点击
        selector = request.selector
        device = device_manager.device
        
        # 根据选择器类型执行点击
        if 'resourceId' in selector:
            element = device(resourceId=selector['resourceId'])
        elif 'text' in selector:
            element = device(text=selector['text'])
        elif 'coordinates' in selector:
            # 坐标点击
            x, y = selector['coordinates']
            device.click(x, y)
            return {"success": True, "message": f"坐标点击成功: ({x}, {y})"}
        else:
            raise ValueError("不支持的选择器类型")
        
        # 执行点击
        if element.exists():
            element.click()
            return {"success": True, "message": "元素点击成功"}
        else:
            return {"success": False, "error": "元素不存在"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"点击元素失败: {str(e)}"
        )

@router.post("/element/input")
async def input_text(request: ElementInputRequest, analyzer=Depends(get_ui_analyzer)):
    """向元素输入文本"""
    try:
        device_manager = analyzer.device_manager.get_device(request.device)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {request.device} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 构建选择器并输入文本
        selector = request.selector
        device = device_manager.device
        
        # 根据选择器类型找到元素
        if 'resourceId' in selector:
            element = device(resourceId=selector['resourceId'])
        elif 'text' in selector:
            element = device(text=selector['text'])
        else:
            raise ValueError("不支持的选择器类型")
        
        # 执行文本输入
        if element.exists():
            element.set_text(request.text)
            return {"success": True, "message": "文本输入成功"}
        else:
            return {"success": False, "error": "元素不存在"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"输入文本失败: {str(e)}"
        )