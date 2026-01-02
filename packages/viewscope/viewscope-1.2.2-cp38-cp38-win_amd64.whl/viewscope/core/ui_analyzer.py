"""
UI分析器核心模块
负责UI层次结构解析和元素分析
"""

import asyncio
import base64
import io
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from PIL import Image

class UIAnalyzer:
    """UI分析器"""
    
    def __init__(self, device_manager):
        self.device_manager = device_manager
        
    async def capture_with_hierarchy(self, device_id: str) -> dict:
        """截图并获取UI层次结构"""
        device_manager = self.device_manager.get_device(device_id)
        if not device_manager:
            raise ValueError(f"设备 {device_id} 不存在")
        
        if not device_manager.is_connected:
            device_manager.connect()
        
        try:
            # 确保uiautomator2服务正常运行
            await self._ensure_device_ready(device_manager)
            
            # 获取设备分辨率信息
            device_info = await self._get_device_resolution(device_manager)
            
            # 获取截图
            screenshot_data = await self._take_screenshot(device_manager)
            
            # 获取UI层次结构
            hierarchy_data = await self._get_ui_hierarchy(device_manager)
            
            return {
                "success": True,
                "screenshot": screenshot_data,
                "hierarchy": hierarchy_data,
                "device_info": device_info,
                "device_id": device_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id
            }
    
    async def _ensure_device_ready(self, device_manager):
        """确保设备和uiautomator2服务准备就绪"""
        try:
            # 检查ADB连接
            if not device_manager.is_connected:
                device_manager.connect()

            loop = asyncio.get_event_loop()

            try:
                device_info = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: device_manager.device.info),
                    timeout=5.0
                )
                if not device_info or 'display' not in device_info:
                    raise Exception("R1")
            except (asyncio.TimeoutError, Exception):
                try:
                    device_manager.disconnect()
                    await asyncio.sleep(2)
                    device_manager.connect()
                except Exception:
                    pass

        except Exception as e:
            raise Exception(f"E1: {str(e)}")
    
    async def _get_device_resolution(self, device_manager) -> dict:
        """获取设备分辨率和屏幕方向信息"""
        try:
            loop = asyncio.get_event_loop()
            device_info = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: device_manager.device.info),
                timeout=5.0
            )

            display_width = device_info.get('displayWidth', 1080)
            display_height = device_info.get('displayHeight', 1920)
            display_rotation = device_info.get('displayRotation', 0)

            orientation = 'portrait' if display_height > display_width else 'landscape'
            rotation_names = {0: 'natural', 1: 'left', 2: 'inverted', 3: 'right'}
            rotation_name = rotation_names.get(display_rotation, 'unknown')

            ui_width = display_width
            ui_height = display_height

            coordinate_system = 'rotated' if display_rotation in [1, 3] else 'normal'

            return {
                'width': display_width,
                'height': display_height,
                'ui_width': ui_width,
                'ui_height': ui_height,
                'orientation': orientation,
                'rotation': display_rotation,
                'rotation_name': rotation_name,
                'coordinate_system': coordinate_system,
                'aspect_ratio': round(max(display_width, display_height) / min(display_width, display_height), 2)
            }

        except Exception:
            return {
                'width': 1080, 'height': 1920,
                'ui_width': 1080, 'ui_height': 1920,
                'orientation': 'portrait', 'rotation': 0,
                'rotation_name': 'natural', 'coordinate_system': 'normal',
                'aspect_ratio': 1.78
            }
    
    async def _take_screenshot(self, device_manager) -> str:
        """使用ADB获取设备截图"""
        return await self._adb_screenshot(device_manager)
    
    async def _adb_screenshot(self, device_manager) -> str:
        """使用ADB命令直接截图"""
        try:
            device_id = device_manager.device_id

            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._execute_adb_screencap, device_id),
                timeout=8.0
            )

            if result and len(result) > 0:
                base64_str = base64.b64encode(result).decode('utf-8')
                return base64_str
            else:
                raise Exception("S1")

        except asyncio.TimeoutError:
            raise Exception("S2")
        except Exception as e:
            raise Exception(f"S3: {str(e)}")

    def _execute_adb_screencap(self, device_id: str) -> bytes:
        """执行ADB截图命令"""
        try:
            result = subprocess.run([
                'adb', '-s', device_id, 'exec-out', 'screencap', '-p'
            ], capture_output=True, timeout=6)

            if result.returncode == 0 and result.stdout:
                return result.stdout
            else:
                raise Exception("S4")

        except subprocess.TimeoutExpired:
            raise Exception("S5")
        except Exception as e:
            raise Exception(f"S6: {str(e)}")
    
    async def _get_ui_hierarchy(self, device_manager) -> dict:
        """获取UI层次结构"""
        try:
            loop = asyncio.get_event_loop()
            ui_xml = await asyncio.wait_for(
                loop.run_in_executor(None, device_manager.device.dump_hierarchy),
                timeout=15.0
            )

            if not ui_xml or ui_xml.strip() == "":
                raise Exception("H1")

            root = ET.fromstring(ui_xml)
            hierarchy = self._parse_xml_node(root)

            return hierarchy

        except asyncio.TimeoutError:
            raise Exception("H2")
        except ET.ParseError as e:
            raise Exception(f"H3: {str(e)}")
        except Exception as e:
            raise Exception(f"H4: {str(e)}")
    
    def _parse_xml_node(self, node: ET.Element) -> dict:
        """解析XML节点"""
        # 提取节点属性
        attrs = node.attrib
        
        # 解析边界坐标
        bounds = self._parse_bounds(attrs.get('bounds', ''))
        
        # 构建节点数据
        node_data = {
            'class': attrs.get('class', ''),
            'text': attrs.get('text', ''),
            'resource_id': attrs.get('resource-id', ''),
            'content_desc': attrs.get('content-desc', ''),
            'package': attrs.get('package', ''),
            'bounds': bounds,
            'checkable': attrs.get('checkable', 'false') == 'true',
            'checked': attrs.get('checked', 'false') == 'true',
            'clickable': attrs.get('clickable', 'false') == 'true',
            'enabled': attrs.get('enabled', 'true') == 'true',
            'focusable': attrs.get('focusable', 'false') == 'true',
            'focused': attrs.get('focused', 'false') == 'true',
            'scrollable': attrs.get('scrollable', 'false') == 'true',
            'long_clickable': attrs.get('long-clickable', 'false') == 'true',
            'password': attrs.get('password', 'false') == 'true',
            'selected': attrs.get('selected', 'false') == 'true',
            'displayed': attrs.get('displayed', 'true') == 'true',
            'index': int(attrs.get('index', '0')),
            'children': []
        }
        
        # 递归解析子节点
        for child in node:
            child_data = self._parse_xml_node(child)
            node_data['children'].append(child_data)
        
        return node_data
    
    def _parse_bounds(self, bounds_str: str) -> List[int]:
        """解析边界坐标字符串"""
        if not bounds_str:
            return [0, 0, 0, 0]
        
        try:
            # 格式: "[left,top][right,bottom]"
            bounds_str = bounds_str.replace('][', ',').replace('[', '').replace(']', '')
            coords = [int(x) for x in bounds_str.split(',')]
            return coords
        except:
            return [0, 0, 0, 0]
    
    def find_element_at_position(self, hierarchy: dict, x: int, y: int) -> Optional[dict]:
        """在层次结构中查找指定位置的元素"""
        def search_node(node: dict) -> Optional[dict]:
            if not node.get('bounds'):
                return None
            
            left, top, right, bottom = node['bounds']
            
            # 检查点击位置是否在当前节点范围内
            if left <= x <= right and top <= y <= bottom:
                # 优先检查子节点
                for child in node.get('children', []):
                    result = search_node(child)
                    if result:
                        return result
                
                # 如果子节点中没找到，返回当前节点
                return node
            
            return None
        
        return search_node(hierarchy)
    
    def get_element_path(self, hierarchy: dict, target_element: dict) -> List[dict]:
        """获取从根节点到目标元素的路径"""
        def find_path(node: dict, path: List[dict]) -> Optional[List[dict]]:
            current_path = path + [node]
            
            # 如果找到目标元素
            if node == target_element:
                return current_path
            
            # 在子节点中递归查找
            for child in node.get('children', []):
                result = find_path(child, current_path)
                if result:
                    return result
            
            return None
        
        return find_path(hierarchy, []) or []