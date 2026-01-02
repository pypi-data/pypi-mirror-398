"""
代码生成器核心模块
根据UI元素信息生成uiautomator2定位代码
"""

from typing import List, Dict, Optional, Tuple

class CodeGenerator:
    """uiautomator2代码生成器"""
    
    def __init__(self):
        pass
    
    def generate_element_code(self, element: dict, options: dict = None) -> dict:
        """生成元素定位代码"""
        if not element:
            raise ValueError("元素信息不能为空")
        
        options = options or {}
        
        # 生成不同类型的定位代码
        selectors = self._generate_selectors(element)
        operations = self._generate_operations(element, options)
        
        # 构建完整代码
        full_code = self._build_full_code(selectors, operations, element)
        
        return {
            "selectors": selectors,
            "operations": operations,
            "full_code": full_code,
            "element_info": self._get_element_summary(element)
        }
    
    def _generate_selectors(self, element: dict) -> List[dict]:
        """生成元素选择器代码"""
        selectors = []
        
        # 1. Resource ID 选择器 (优先级最高)
        if element.get('resource_id'):
            selectors.append({
                "type": "resource_id",
                "priority": 1,
                "stability": "high",
                "code": f'd(resourceId="{element["resource_id"]}")',
                "description": "资源ID定位 - 最稳定的定位方式",
                "pros": ["稳定性高", "执行速度快", "不受文本变化影响"],
                "cons": ["需要开发者设置ID"]
            })
        
        # 2. Text 选择器
        if element.get('text') and element['text'].strip():
            text = element['text'].strip()
            selectors.append({
                "type": "text",
                "priority": 2,
                "stability": "medium",
                "code": f'd(text="{text}")',
                "description": f"文本定位 - 基于显示文本 '{text}'",
                "pros": ["直观易懂", "适合文本固定的场景"],
                "cons": ["文本变化时会失效", "多语言环境不稳定"]
            })
            
            # 文本包含匹配
            if len(text) > 10:  # 文本较长时提供包含匹配
                short_text = text[:8] + "..."
                selectors.append({
                    "type": "text_contains",
                    "priority": 3,
                    "stability": "medium",
                    "code": f'd(textContains="{text[:8]}")',
                    "description": f"文本包含定位 - 包含 '{short_text}'",
                    "pros": ["对文本变化容错性更强"],
                    "cons": ["可能匹配到多个元素"]
                })
        
        # 3. Content Description 选择器
        if element.get('content_desc'):
            selectors.append({
                "type": "content_desc",
                "priority": 2,
                "stability": "high",
                "code": f'd(description="{element["content_desc"]}")',
                "description": f"内容描述定位 - 基于无障碍描述",
                "pros": ["稳定性高", "语义化好"],
                "cons": ["不是所有元素都有描述"]
            })
        
        # 4. Class Name 选择器
        if element.get('class'):
            class_name = element['class']
            selectors.append({
                "type": "class_name",
                "priority": 4,
                "stability": "low",
                "code": f'd(className="{class_name}")',
                "description": f"类名定位 - 基于UI组件类型",
                "pros": ["适合组件类型固定的场景"],
                "cons": ["通常会匹配多个元素", "需要结合其他条件"]
            })
        
        # 5. 组合选择器
        if len(selectors) > 1:
            # 组合最佳的两个条件
            combo_conditions = []
            if element.get('resource_id'):
                combo_conditions.append(f'resourceId="{element["resource_id"]}"')
            elif element.get('text') and element['text'].strip():
                combo_conditions.append(f'text="{element["text"].strip()}"')
            
            if element.get('class') and len(combo_conditions) == 1:
                combo_conditions.append(f'className="{element["class"]}"')
            
            if len(combo_conditions) >= 2:
                selectors.append({
                    "type": "combined",
                    "priority": 1,
                    "stability": "very_high",
                    "code": f'd({", ".join(combo_conditions)})',
                    "description": "组合定位 - 多条件组合",
                    "pros": ["准确性最高", "误匹配概率极低"],
                    "cons": ["条件过多时维护复杂"]
                })
        
        # 6. 坐标定位 (兜底方案)
        if element.get('bounds'):
            bounds = element['bounds']
            center_x = (bounds[0] + bounds[2]) // 2
            center_y = (bounds[1] + bounds[3]) // 2
            selectors.append({
                "type": "coordinate",
                "priority": 5,
                "stability": "very_low",
                "code": f'd.click({center_x}, {center_y})',
                "description": f"坐标点击 - 点击位置 ({center_x}, {center_y})",
                "pros": ["总是可用的兜底方案"],
                "cons": ["屏幕分辨率变化时失效", "界面布局变化时失效", "不具备通用性"]
            })
        
        # 按优先级排序
        selectors.sort(key=lambda x: x["priority"])
        
        return selectors
    
    def _generate_operations(self, element: dict, options: dict) -> List[dict]:
        """生成元素操作代码"""
        operations = []
        
        # 基本点击操作
        operations.append({
            "type": "click",
            "code": "element.click()",
            "description": "点击元素",
            "applicable": element.get('clickable', False)
        })
        
        # 长按操作
        if element.get('long_clickable', False):
            operations.append({
                "type": "long_click",
                "code": "element.long_click()",
                "description": "长按元素",
                "applicable": True
            })
        
        # 文本输入操作
        if element.get('class', '').endswith('EditText') or 'edit' in element.get('class', '').lower():
            operations.append({
                "type": "input_text",
                "code": 'element.set_text("输入内容")',
                "description": "输入文本",
                "applicable": True
            })
            
            operations.append({
                "type": "clear_text",
                "code": "element.clear_text()",
                "description": "清空文本",
                "applicable": True
            })
        
        # 滚动操作
        if element.get('scrollable', False):
            operations.extend([
                {
                    "type": "scroll_up",
                    "code": "element.scroll.up()",
                    "description": "向上滚动",
                    "applicable": True
                },
                {
                    "type": "scroll_down", 
                    "code": "element.scroll.down()",
                    "description": "向下滚动",
                    "applicable": True
                }
            ])
        
        # 等待操作
        operations.extend([
            {
                "type": "wait_exists",
                "code": "element.wait(timeout=10)",
                "description": "等待元素出现",
                "applicable": True
            },
            {
                "type": "wait_gone",
                "code": "element.wait_gone(timeout=10)",
                "description": "等待元素消失",
                "applicable": True
            }
        ])
        
        # 断言操作
        operations.extend([
            {
                "type": "assert_exists",
                "code": "assert element.exists()",
                "description": "断言元素存在",
                "applicable": True
            },
            {
                "type": "get_info",
                "code": "info = element.info",
                "description": "获取元素信息",
                "applicable": True
            }
        ])
        
        return operations
    
    def _build_full_code(self, selectors: List[dict], operations: List[dict], element: dict) -> str:
        """构建完整的代码示例"""
        if not selectors:
            return "# 无法生成定位代码：元素缺少必要的定位属性"
        
        code_lines = [
            "# uiautomator2 自动化代码",
            "# 此代码由 Android View Scope 自动生成",
            "",
            "import uiautomator2 as u2",
            "",
            "# 连接设备",
            'd = u2.connect()  # 默认连接第一个设备',
            "# d = u2.connect('设备序列号')  # 连接指定设备",
            "",
            "# 等待应用启动完成",
            'd.app_start("应用包名")',
            "",
        ]
        
        # 添加推荐的定位方式
        code_lines.append("# 元素定位（按推荐程度排序）:")
        for i, selector in enumerate(selectors[:3], 1):  # 只显示前3个最佳方案
            stability_icon = {
                "very_high": "🟢",
                "high": "🟢", 
                "medium": "🟡",
                "low": "🟠",
                "very_low": "🔴"
            }.get(selector["stability"], "⚪")
            
            code_lines.append(f"")
            code_lines.append(f"# 方式 {i}: {selector['description']} {stability_icon}")
            code_lines.append(f"element = {selector['code']}")
            code_lines.append("if element.exists():")
            
            # 添加常用操作
            if element.get('clickable', False):
                code_lines.append("    element.click()  # 点击操作")
            
            if 'EditText' in element.get('class', ''):
                code_lines.append('    element.set_text("输入内容")  # 文本输入')
            
            code_lines.append("    print(f'操作成功: {element.info}')")
            code_lines.append("else:")
            code_lines.append("    print('元素不存在')")
        
        # 添加错误处理示例
        code_lines.extend([
            "",
            "# 带错误处理的完整示例:",
            "try:",
            f"    element = {selectors[0]['code']}",
            "    ",
            "    # 等待元素出现",
            "    if element.wait(timeout=10):",
            "        element.click()",
            "        print('操作执行成功')",
            "    else:",
            "        print('元素等待超时')",
            "",
            "except Exception as e:",
            "    print(f'操作失败: {e}')",
            "",
            "# 获取元素详细信息:",
            f"element = {selectors[0]['code']}",
            "if element.exists():",
            "    info = element.info",
            "    print(f'元素信息: {info}')",
        ])
        
        return "\n".join(code_lines)
    
    def _get_element_summary(self, element: dict) -> dict:
        """获取元素摘要信息"""
        return {
            "class": element.get('class', ''),
            "text": element.get('text', ''),
            "resource_id": element.get('resource_id', ''),
            "content_desc": element.get('content_desc', ''),
            "bounds": element.get('bounds', []),
            "clickable": element.get('clickable', False),
            "editable": 'EditText' in element.get('class', ''),
            "scrollable": element.get('scrollable', False)
        }
    
    def generate_batch_code(self, elements: List[dict]) -> str:
        """生成批量操作代码"""
        if not elements:
            return "# 没有选中的元素"
        
        code_lines = [
            "# 批量操作代码",
            "import uiautomator2 as u2",
            "",
            "d = u2.connect()",
            "",
            "# 定义所有目标元素",
            "elements = ["
        ]
        
        for i, element in enumerate(elements):
            selectors = self._generate_selectors(element)
            if selectors:
                best_selector = selectors[0]['code']
                code_lines.append(f"    {best_selector},  # 元素 {i+1}")
        
        code_lines.extend([
            "]",
            "",
            "# 批量执行操作",
            "for i, element in enumerate(elements):",
            "    try:",
            "        if element.exists():",
            "            element.click()",
            "            print(f'元素 {i+1} 点击成功')",
            "        else:",
            "            print(f'元素 {i+1} 不存在')",
            "    except Exception as e:",
            "        print(f'元素 {i+1} 操作失败: {e}')"
        ])
        
        return "\n".join(code_lines)