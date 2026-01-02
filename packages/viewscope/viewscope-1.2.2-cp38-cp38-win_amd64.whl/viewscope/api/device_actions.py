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
    if 'main' in sys.modules:
        return sys.modules['main'].device_manager
    import main
    return main.device_manager

def _get_recorder():
    try:
        from core.action_recorder import get_action_recorder
        return get_action_recorder()
    except:
        class D:
            def record_action(self, *a, **k): pass
        return D()

class ClickRequest(BaseModel):
    x: int
    y: int

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

def get_device_manager():
    """依赖注入：获取设备管理器"""
    return _get_dm()

@router.post("/device/{device_id}/click")
async def click_device(device_id: str, request: ClickRequest, dm=Depends(get_device_manager)):
    """点击设备指定坐标"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 执行点击操作
        device_manager.device.click(request.x, request.y)

        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="click",
            params={"x": request.x, "y": request.y},
            coordinates={"x": request.x, "y": request.y}
        )
        
        return {
            "success": True,
            "action": "click",
            "coordinates": [request.x, request.y],
            "device_id": device_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"C1: {str(e)}"
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
        raise HTTPException(
            status_code=500,
            detail=f"K1: {str(e)}"
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
        raise HTTPException(
            status_code=500,
            detail=f"I1: {str(e)}"
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
        raise HTTPException(
            status_code=500,
            detail=f"G1: {str(e)}"
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
        raise HTTPException(
            status_code=500,
            detail=f"L1: {str(e)}"
        )

@router.post("/device/{device_id}/swipe")
async def swipe_device(device_id: str, request: SwipeRequest, dm=Depends(get_device_manager)):
    """滑动操作"""
    try:
        device_manager = dm.get_device(device_id)
        if not device_manager:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        # 执行滑动操作
        device_manager.device.swipe(request.fx, request.fy, request.tx, request.ty, request.duration / 1000.0)

        # 录制操作
        recorder = _get_recorder()
        recorder.record_action(
            action_type="swipe",
            params={
                "fx": request.fx, "fy": request.fy, 
                "tx": request.tx, "ty": request.ty, 
                "duration": request.duration
            },
            coordinates={"fx": request.fx, "fy": request.fy, "tx": request.tx, "ty": request.ty}
        )
        
        return {
            "success": True,
            "action": "swipe",
            "start_coordinates": [request.fx, request.fy],
            "end_coordinates": [request.tx, request.ty],
            "duration": request.duration,
            "device_id": device_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"W1: {str(e)}"
        )