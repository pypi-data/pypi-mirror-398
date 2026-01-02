"""
设备操作API路由
实现真实设备的点击、按键等操作
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys

router = APIRouter()

def _get_dm():
    """获取设备管理器实例"""
    if 'main' in sys.modules:
        return sys.modules['main'].device_manager
    import main
    return main.device_manager

def _get_recorder():
    """获取操作录制器"""
    try:
        from core.action_recorder import get_action_recorder
        return get_action_recorder()
    except Exception:
        class DummyRecorder:
            def record_action(self, *args, **kwargs): pass
        return DummyRecorder()

class ClickRequest(BaseModel):
    x: int
    y: int
    # 前端显示尺寸（用于坐标转换）
    display_width: Optional[int] = None
    display_height: Optional[int] = None

class KeyRequest(BaseModel):
    key: str

class InputRequest(BaseModel):
    text: str

class SwipeRequest(BaseModel):
    fx: int  # 起点x坐标
    fy: int  # 起点y坐标
    tx: int  # 终点x坐标
    ty: int  # 终点y坐标
    duration: int = 500  # 滑动时长(毫秒)
    # 前端显示尺寸（用于坐标转换）
    display_width: Optional[int] = None
    display_height: Optional[int] = None

def get_device_manager():
    """依赖注入：获取设备管理器"""
    return _get_dm()

@router.post("/device/{device_id}/click")
async def click_device(device_id: str, request: ClickRequest, dm=Depends(get_device_manager)):
    """点击设备指定坐标（支持坐标缩放转换）"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")

        if not device_manager.is_connected:
            device_manager.connect()

        # 获取设备实际分辨率
        device_info = device_manager.device.info
        device_width = device_info.get('displayWidth', 1080)
        device_height = device_info.get('displayHeight', 1920)

        # 坐标转换：如果前端提供了显示尺寸，进行缩放
        real_x = request.x
        real_y = request.y

        if request.display_width and request.display_height:
            # 计算缩放比例
            scale_x = device_width / request.display_width
            scale_y = device_height / request.display_height
            real_x = int(request.x * scale_x)
            real_y = int(request.y * scale_y)

        # 执行点击操作
        device_manager.device.click(real_x, real_y)

        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="click",
            params={"x": real_x, "y": real_y},
            coordinates={"x": real_x, "y": real_y}
        )

        return {
            "success": True,
            "action": "click",
            "coordinates": [real_x, real_y],
            "original_coordinates": [request.x, request.y],
            "device_resolution": [device_width, device_height],
            "device_id": device_id
        }

    except Exception as e:
        print(f"[FAIL]设备点击失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"点击失败: {str(e)}"
        )

@router.post("/device/{device_id}/key")
async def press_key(device_id: str, request: KeyRequest, dm=Depends(get_device_manager)):
    """按系统键"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 执行按键操作
        device_manager.device.press(request.key)
        
        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="key",
            params={"key": request.key}
        )
        
        return {
            "success": True,
            "action": "key",
            "key": request.key,
            "device_id": device_id
        }
        
    except Exception as e:
        print(f"[FAIL]按键失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"按键失败: {str(e)}"
        )

@router.post("/device/{device_id}/input")
async def input_text(device_id: str, request: InputRequest, dm=Depends(get_device_manager)):
    """输入文本"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 执行文本输入
        device_manager.device.send_keys(request.text)
        
        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="input",
            params={"text": request.text}
        )
        
        return {
            "success": True,
            "action": "input",
            "text": request.text,
            "device_id": device_id
        }
        
    except Exception as e:
        print(f"[FAIL]文本输入失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文本输入失败: {str(e)}"
        )

@router.get("/device/{device_id}/screen_size")
async def get_screen_size(device_id: str, dm=Depends(get_device_manager)):
    """获取屏幕尺寸"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 获取屏幕信息
        info = device_manager.device.info
        return {
            "success": True,
            "width": info['displayWidth'],
            "height": info['displayHeight'],
            "device_id": device_id
        }
        
    except Exception as e:
        print(f"[FAIL]获取屏幕尺寸失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取屏幕尺寸失败: {str(e)}"
        )

@router.post("/device/{device_id}/long_click")
async def long_click_device(device_id: str, request: ClickRequest, dm=Depends(get_device_manager)):
    """长按设备指定坐标"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 执行长按操作
        device_manager.device.long_click(request.x, request.y)
        
        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="long_click",
            params={"x": request.x, "y": request.y},
            coordinates={"x": request.x, "y": request.y}
        )
        
        return {
            "success": True,
            "action": "long_click",
            "coordinates": [request.x, request.y],
            "device_id": device_id
        }
        
    except Exception as e:
        print(f"[FAIL]设备长按失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"长按失败: {str(e)}"
        )

@router.post("/device/{device_id}/swipe")
async def swipe_device(device_id: str, request: SwipeRequest, dm=Depends(get_device_manager)):
    """滑动操作（支持坐标缩放转换）"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")

        if not device_manager.is_connected:
            device_manager.connect()

        # 获取设备实际分辨率
        device_info = device_manager.device.info
        device_width = device_info.get('displayWidth', 1080)
        device_height = device_info.get('displayHeight', 1920)

        # 坐标转换
        real_fx, real_fy = request.fx, request.fy
        real_tx, real_ty = request.tx, request.ty

        if request.display_width and request.display_height:
            scale_x = device_width / request.display_width
            scale_y = device_height / request.display_height
            real_fx = int(request.fx * scale_x)
            real_fy = int(request.fy * scale_y)
            real_tx = int(request.tx * scale_x)
            real_ty = int(request.ty * scale_y)

        # 执行滑动操作
        device_manager.device.swipe(real_fx, real_fy, real_tx, real_ty, request.duration / 1000.0)

        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="swipe",
            params={
                "fx": real_fx, "fy": real_fy,
                "tx": real_tx, "ty": real_ty,
                "duration": request.duration
            },
            coordinates={"fx": real_fx, "fy": real_fy, "tx": real_tx, "ty": real_ty}
        )

        return {
            "success": True,
            "action": "swipe",
            "start_coordinates": [real_fx, real_fy],
            "end_coordinates": [real_tx, real_ty],
            "duration": request.duration,
            "device_id": device_id
        }
        
    except Exception as e:
        print(f"[FAIL]设备滑动失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"滑动失败: {str(e)}"
        )