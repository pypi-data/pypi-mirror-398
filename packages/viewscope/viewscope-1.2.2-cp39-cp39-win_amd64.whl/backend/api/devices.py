"""
设备管理API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import re
import sys

router = APIRouter()

def _get_dm():
    """获取设备管理器实例"""
    if 'main' in sys.modules:
        return sys.modules['main'].device_manager
    import main
    return main.device_manager

def _get_ui():
    """获取UI分析器实例"""
    if 'main' in sys.modules:
        return sys.modules['main'].ui_analyzer
    import main
    return main.ui_analyzer

class DeviceInfo(BaseModel):
    id: str
    model: str = "Unknown"
    brand: str = "Unknown"
    version: str = "Unknown"
    sdk: int = 0
    resolution: str = "Unknown"
    status: str = "disconnected"
    connected: bool = False
    current_app: dict = None
    error: str = None
    connection_type: str = "usb"  # "usb" or "wifi"
    ip_address: Optional[str] = None

class WiFiConnectionRequest(BaseModel):
    ip_address: str
    port: int = 5555
    
class WiFiDiscoveryRequest(BaseModel):
    ip_range: str = "192.168.1.1-192.168.1.255"  # IP范围扫描
    port: int = 5555

class ConnectionResponse(BaseModel):
    success: bool
    message: str
    device_info: DeviceInfo = None
    screenshot_data: dict = None

def get_device_manager():
    """依赖注入：获取设备管理器"""
    return _get_dm()

@router.get("/devices", response_model=List[DeviceInfo])
async def get_devices(dm=Depends(get_device_manager)):
    """获取所有连接的设备"""
    try:
        # 如果需要刷新设备列表
        if dm.should_refresh_devices():
            devices = await dm.scan_devices()
        else:
            devices = dm.get_all_devices()
        
        return [DeviceInfo(**device) for device in devices]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取设备列表失败: {str(e)}"
        )

@router.post("/devices/{device_id}/connect", response_model=ConnectionResponse)
async def connect_device(
    device_id: str, 
    auto_screenshot: bool = True,
    dm=Depends(get_device_manager)
):
    """连接指定设备"""
    try:
        device_info = await dm.connect_device(device_id)
        screenshot_data = None
        
        # 如果启用自动截图
        if auto_screenshot:
            try:
                ui_analyzer = _get_ui()
                screenshot_data = await ui_analyzer.capture_with_hierarchy(device_id)
            except Exception as screenshot_error:
                import traceback
                traceback.print_exc()
                # 自动截图失败不影响连接结果
        
        return ConnectionResponse(
            success=True,
            message="设备连接成功" + ("，已自动截图" if screenshot_data and screenshot_data.get("success") else ""),
            device_info=DeviceInfo(**device_info),
            screenshot_data=screenshot_data
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"连接设备失败: {str(e)}"
        )

@router.delete("/devices/{device_id}")
async def disconnect_device(device_id: str, dm=Depends(get_device_manager)):
    """断开设备连接"""
    try:
        await dm.disconnect_device(device_id)
        
        return {
            "success": True,
            "message": f"设备 {device_id} 已断开连接"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"断开设备连接失败: {str(e)}"
        )

@router.get("/devices/{device_id}/status")
async def get_device_status(device_id: str, dm=Depends(get_device_manager)):
    """获取设备状态"""
    try:
        status = await dm.get_device_status(device_id)
        return status
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取设备状态失败: {str(e)}"
        )

@router.post("/devices/wifi/discover")
async def discover_wifi_devices(request: WiFiDiscoveryRequest, dm=Depends(get_device_manager)):
    """扫描WiFi设备"""
    try:
        devices = await dm.discover_wifi_devices(request.ip_range, request.port)
        return {
            "success": True,
            "message": f"扫描完成，发现 {len(devices)} 个WiFi设备",
            "devices": [DeviceInfo(**device) for device in devices]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"WiFi设备扫描失败: {str(e)}"
        )

@router.post("/devices/wifi/connect")
async def connect_wifi_device(request: WiFiConnectionRequest, dm=Depends(get_device_manager)):
    """连接WiFi设备"""
    try:
        device_info = await dm.connect_wifi_device(request.ip_address, request.port)
        
        # 尝试自动截图
        screenshot_data = None
        try:
            ui_analyzer = _get_ui()
            device_id = f"{request.ip_address}:{request.port}"
            screenshot_data = await ui_analyzer.capture_with_hierarchy(device_id)
        except Exception:
            pass
        
        return ConnectionResponse(
            success=True,
            message=f"WiFi设备连接成功: {request.ip_address}:{request.port}",
            device_info=DeviceInfo(**device_info),
            screenshot_data=screenshot_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"连接WiFi设备失败: {str(e)}"
        )

@router.delete("/devices/wifi/{ip_address}")
async def disconnect_wifi_device(ip_address: str, port: int = 5555, dm=Depends(get_device_manager)):
    """断开WiFi设备连接"""
    try:
        device_id = f"{ip_address}:{port}"
        await dm.disconnect_wifi_device(device_id)
        
        return {
            "success": True,
            "message": f"WiFi设备 {device_id} 已断开连接"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"断开WiFi设备连接失败: {str(e)}"
        )