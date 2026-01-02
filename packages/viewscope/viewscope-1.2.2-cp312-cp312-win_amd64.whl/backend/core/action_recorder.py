"""
操作录制核心模块
记录用户操作序列并生成uiautomator2脚本
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class RecordedAction:
    """录制的操作数据结构"""
    action_type: str  # 'click', 'long_click', 'input', 'key', 'swipe'
    timestamp: float  # 相对于录制开始的时间戳(秒)
    params: Dict[str, Any]  # 操作参数
    element_info: Optional[Dict[str, Any]] = None  # 元素信息
    coordinates: Optional[Dict[str, int]] = None  # 坐标信息
    screenshot_before: Optional[str] = None  # 操作前截图标识


class ActionRecorder:
    """操作录制器"""
    
    def __init__(self):
        self.is_recording = False
        self.actions: List[RecordedAction] = []
        self.start_time: Optional[float] = None
        self.current_session_id = None
        self.device_info = {}
        
    def start_recording(self, device_id: str = None) -> Dict[str, Any]:
        """开始录制操作"""
        if self.is_recording:
            return {
                "success": False,
                "message": "录制已在进行中"
            }
        
        self.is_recording = True
        self.actions = []
        self.start_time = time.time()
        self.current_session_id = f"session_{int(self.start_time)}"
        self.device_info = {"device_id": device_id}

        return {
            "success": True,
            "message": "开始录制操作",
            "session_id": self.current_session_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }
    
    def stop_recording(self) -> Dict[str, Any]:
        """停止录制操作"""
        if not self.is_recording:
            return {
                "success": False,
                "message": "当前没有录制会话"
            }
        
        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0

        return {
            "success": True,
            "message": f"录制完成，共记录 {len(self.actions)} 个操作",
            "session_id": self.current_session_id,
            "action_count": len(self.actions),
            "duration": duration
        }
    
    def record_action(self, action_type: str, params: Dict[str, Any], 
                     element_info: Optional[Dict[str, Any]] = None,
                     coordinates: Optional[Dict[str, int]] = None) -> bool:
        """记录一个操作"""
        if not self.is_recording:
            return False
        
        # 计算相对时间戳
        current_time = time.time()
        relative_timestamp = current_time - self.start_time if self.start_time else 0
        
        # 创建操作记录
        action = RecordedAction(
            action_type=action_type,
            timestamp=relative_timestamp,
            params=params.copy(),
            element_info=element_info.copy() if element_info else None,
            coordinates=coordinates.copy() if coordinates else None
        )
        
        self.actions.append(action)

        return True
    
    def get_current_session_info(self) -> Dict[str, Any]:
        """获取当前录制会话信息"""
        return {
            "is_recording": self.is_recording,
            "session_id": self.current_session_id,
            "action_count": len(self.actions),
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "device_info": self.device_info
        }
    
    def generate_script(self, script_type: str = "uiautomator2") -> str:
        """生成自动化脚本"""
        if not self.actions:
            return "# 没有录制的操作"
        
        if script_type == "uiautomator2":
            return self._generate_uiautomator2_script()
        else:
            return f"# 不支持的脚本类型: {script_type}"
    
    def _generate_uiautomator2_script(self) -> str:
        """生成uiautomator2脚本"""
        script_lines = [
            '"""',
            "自动生成的uiautomator2脚本",
            f"录制时间: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'Unknown'}",
            f"操作数量: {len(self.actions)}",
            f"会话ID: {self.current_session_id}",
            '"""',
            "",
            "import uiautomator2 as u2",
            "import time",
            "",
            "def main():",
            '    """执行录制的操作序列"""',
        ]
        
        # 添加设备连接
        device_id = self.device_info.get("device_id", "")
        if device_id:
            if ":" in device_id:  # WiFi设备
                script_lines.extend([
                    f'    # 连接WiFi设备: {device_id}',
                    f'    d = u2.connect("{device_id}")'
                ])
            else:  # USB设备
                script_lines.extend([
                    f'    # 连接USB设备: {device_id}',
                    f'    d = u2.connect("{device_id}")'
                ])
        else:
            script_lines.extend([
                '    # 连接默认设备',
                '    d = u2.connect()'
            ])
        
        script_lines.extend([
            '',
            '    print("开始执行录制的操作...")',
            ''
        ])
        
        # 添加操作序列
        last_timestamp = 0
        for i, action in enumerate(self.actions):
            # 添加延迟
            delay = action.timestamp - last_timestamp
            if delay > 0.1:  # 只有延迟超过100ms才添加sleep
                script_lines.append(f'    time.sleep({delay:.2f})  # 等待 {delay:.2f} 秒')
            
            # 生成操作代码
            action_code = self._generate_action_code(action, i + 1)
            script_lines.extend([f'    {line}' if line.strip() else '' for line in action_code])
            
            last_timestamp = action.timestamp
        
        # 添加结束代码
        script_lines.extend([
            '',
            '    print("所有操作执行完成!")',
            '',
            '',
            'if __name__ == "__main__":',
            '    main()'
        ])
        
        return '\n'.join(script_lines)
    
    def _generate_action_code(self, action: RecordedAction, step_num: int) -> List[str]:
        """为单个操作生成代码"""
        lines = [f'# 步骤 {step_num}: {action.action_type}']
        
        if action.action_type == "click":
            lines.extend(self._generate_click_code(action))
        elif action.action_type == "long_click":
            lines.extend(self._generate_long_click_code(action))
        elif action.action_type == "input":
            lines.extend(self._generate_input_code(action))
        elif action.action_type == "key":
            lines.extend(self._generate_key_code(action))
        elif action.action_type == "swipe":
            lines.extend(self._generate_swipe_code(action))
        else:
            lines.append(f'# 未支持的操作类型: {action.action_type}')
        
        lines.append('')  # 添加空行分隔
        return lines
    
    def _generate_click_code(self, action: RecordedAction) -> List[str]:
        """生成点击操作代码"""
        params = action.params
        element_info = action.element_info
        
        # 优先使用元素定位
        if element_info:
            locator = self._generate_element_locator(element_info)
            if locator:
                return [
                    f'{locator}.click()',
                    f'print("点击元素: {element_info.get("text", element_info.get("resource_id", "未知元素"))}")'
                ]
        
        # 使用坐标定位
        x, y = params.get("x", 0), params.get("y", 0)
        return [
            f'd.click({x}, {y})',
            f'print("点击坐标: ({x}, {y})")'
        ]
    
    def _generate_long_click_code(self, action: RecordedAction) -> List[str]:
        """生成长按操作代码"""
        params = action.params
        element_info = action.element_info
        
        if element_info:
            locator = self._generate_element_locator(element_info)
            if locator:
                return [
                    f'{locator}.long_click()',
                    f'print("长按元素: {element_info.get("text", element_info.get("resource_id", "未知元素"))}")'
                ]
        
        x, y = params.get("x", 0), params.get("y", 0)
        return [
            f'd.long_click({x}, {y})',
            f'print("长按坐标: ({x}, {y})")'
        ]
    
    def _generate_input_code(self, action: RecordedAction) -> List[str]:
        """生成输入操作代码"""
        params = action.params
        text = params.get("text", "")
        element_info = action.element_info
        
        lines = []
        
        # 先定位输入框
        if element_info:
            locator = self._generate_element_locator(element_info)
            if locator:
                lines.extend([
                    f'{locator}.click()  # 点击输入框获得焦点',
                    f'{locator}.set_text("{text}")',
                    f'print("输入文本: {text}")'
                ])
                return lines
        
        # 使用全局输入
        lines.extend([
            f'd.send_keys("{text}")',
            f'print("发送文本: {text}")'
        ])
        return lines
    
    def _generate_key_code(self, action: RecordedAction) -> List[str]:
        """生成按键操作代码"""
        params = action.params
        key = params.get("key", "")
        
        return [
            f'd.press("{key}")',
            f'print("按键: {key}")'
        ]
    
    def _generate_swipe_code(self, action: RecordedAction) -> List[str]:
        """生成滑动操作代码"""
        params = action.params
        fx = params.get("fx", 0)
        fy = params.get("fy", 0)
        tx = params.get("tx", 0)
        ty = params.get("ty", 0)
        duration = params.get("duration", 0.5)
        
        return [
            f'd.swipe({fx}, {fy}, {tx}, {ty}, {duration})',
            f'print("滑动: ({fx}, {fy}) -> ({tx}, {ty}), 耗时{duration}秒")'
        ]
    
    def _generate_element_locator(self, element_info: Dict[str, Any]) -> Optional[str]:
        """生成元素定位器代码"""
        if not element_info:
            return None
        
        # 优先级：resource_id > text > content_desc > class_name
        resource_id = element_info.get("resource_id")
        if resource_id:
            return f'd(resourceId="{resource_id}")'
        
        text = element_info.get("text")
        if text:
            return f'd(text="{text}")'
        
        content_desc = element_info.get("content_desc")
        if content_desc:
            return f'd(description="{content_desc}")'
        
        class_name = element_info.get("class")
        if class_name:
            return f'd(className="{class_name}")'
        
        return None
    
    def export_session_data(self) -> Dict[str, Any]:
        """导出录制会话数据"""
        return {
            "session_id": self.current_session_id,
            "device_info": self.device_info,
            "start_time": self.start_time,
            "actions": [asdict(action) for action in self.actions],
            "generated_at": time.time()
        }
    
    def import_session_data(self, session_data: Dict[str, Any]) -> bool:
        """导入录制会话数据"""
        try:
            self.current_session_id = session_data.get("session_id")
            self.device_info = session_data.get("device_info", {})
            self.start_time = session_data.get("start_time")
            
            # 重建操作列表
            self.actions = []
            for action_data in session_data.get("actions", []):
                action = RecordedAction(**action_data)
                self.actions.append(action)
            
            self.is_recording = False
            return True
        except Exception as e:
            print(f"导入会话数据失败: {e}")
            return False


# 全局录制器实例
action_recorder = ActionRecorder()


def get_action_recorder() -> ActionRecorder:
    """获取全局录制器实例"""
    return action_recorder