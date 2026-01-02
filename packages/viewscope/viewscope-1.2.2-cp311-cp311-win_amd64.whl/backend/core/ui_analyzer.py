"""
UI分析器核心模块
负责UI层次结构解析和元素分析
优化版本: 支持并行截图、增量更新、WebSocket流
"""

import asyncio
import base64
import io
import subprocess
import xml.etree.ElementTree as ET
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Callable
from PIL import Image
import cv2
import numpy as np
import imagehash

class UIAnalyzer:
    """UI分析器 - 支持Android和QNX系统，优化版本"""

    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.qnx_detector = QNXVisualDetector()
        # 缓存机制
        self._device_info_cache: Dict[str, dict] = {}
        self._device_info_cache_time: Dict[str, float] = {}
        self._last_frame_hash: Dict[str, str] = {}
        self._last_frame_data: Dict[str, bytes] = {}
        self._cache_ttl = 2.0  # 设备信息缓存2秒

    async def capture_with_hierarchy(self, device_id: str) -> dict:
        """优化后的截图方法 - 并行执行，减少重复调用"""
        device_manager = self.device_manager.get_device(device_id)
        if not device_manager:
            raise ValueError(f"设备 {device_id} 不存在")

        if not device_manager.is_connected:
            device_manager.connect()

        try:
            start_time = time.time()

            # 获取设备信息（带缓存，只调用一次）
            device_info = await self._get_device_info_cached(device_manager, device_id)
            info_time = time.time() - start_time

            # 并行获取截图和UI层次结构
            screenshot_task = self._fast_screenshot(device_manager)
            hierarchy_task = self._get_ui_hierarchy(device_manager)

            results = await asyncio.gather(
                screenshot_task,
                hierarchy_task,
                return_exceptions=True
            )

            parallel_time = time.time() - start_time - info_time

            # 处理结果
            screenshot_data = results[0] if not isinstance(results[0], Exception) else None
            hierarchy_data = results[1] if not isinstance(results[1], Exception) else None

            screenshot_error = str(results[0]) if isinstance(results[0], Exception) else None
            hierarchy_error = str(results[1]) if isinstance(results[1], Exception) else None

            total_time = time.time() - start_time

            return {
                "success": screenshot_data is not None,
                "screenshot": screenshot_data,
                "hierarchy": hierarchy_data,
                "device_info": device_info,
                "device_id": device_id,
                "performance": {
                    "total_ms": int(total_time * 1000),
                    "info_ms": int(info_time * 1000),
                    "parallel_ms": int(parallel_time * 1000)
                },
                "errors": {
                    "screenshot": screenshot_error,
                    "hierarchy": hierarchy_error
                } if screenshot_error or hierarchy_error else None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id
            }

    async def _get_device_info_cached(self, device_manager, device_id: str) -> dict:
        """获取设备信息（带缓存）"""
        current_time = time.time()

        # 检查缓存是否有效
        if device_id in self._device_info_cache:
            cache_time = self._device_info_cache_time.get(device_id, 0)
            if current_time - cache_time < self._cache_ttl:
                return self._device_info_cache[device_id]

        # 获取新的设备信息
        try:
            loop = asyncio.get_running_loop()
            device_info = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: device_manager.device.info),
                timeout=3.0  # 降低超时时间
            )

            # 解析设备信息
            display_width = device_info.get('displayWidth', 1080)
            display_height = device_info.get('displayHeight', 1920)
            display_rotation = device_info.get('displayRotation', 0)

            orientation = 'portrait' if display_height > display_width else 'landscape'
            rotation_names = {0: 'natural', 1: 'left', 2: 'inverted', 3: 'right'}
            rotation_name = rotation_names.get(display_rotation, 'unknown')

            coordinate_system = 'rotated' if display_rotation in [1, 3] else 'normal'

            resolution_info = {
                'width': display_width,
                'height': display_height,
                'ui_width': display_width,
                'ui_height': display_height,
                'orientation': orientation,
                'rotation': display_rotation,
                'rotation_name': rotation_name,
                'coordinate_system': coordinate_system,
                'aspect_ratio': round(max(display_width, display_height) / min(display_width, display_height), 2)
            }

            # 更新缓存
            self._device_info_cache[device_id] = resolution_info
            self._device_info_cache_time[device_id] = current_time

            return resolution_info

        except Exception:
            return {
                'width': 1080, 'height': 1920,
                'ui_width': 1080, 'ui_height': 1920,
                'orientation': 'portrait', 'rotation': 0,
                'rotation_name': 'natural', 'coordinate_system': 'normal',
                'aspect_ratio': 1.78
            }

    async def _fast_screenshot(self, device_manager) -> str:
        """快速截图 - 使用uiautomator2原生方法 + JPEG格式 + 严格超时"""
        try:
            start_time = time.time()
            loop = asyncio.get_running_loop()

            def capture_jpeg():
                img = device_manager.device.screenshot()  # PIL Image
                buffer = io.BytesIO()
                # 使用JPEG格式，quality=80平衡质量和速度，禁用optimize加速
                img.save(buffer, format='JPEG', quality=80, optimize=False)
                return buffer.getvalue()

            # 严格1.5秒超时，避免阻塞
            image_bytes = await asyncio.wait_for(
                loop.run_in_executor(None, capture_jpeg),
                timeout=1.5
            )

            # 转换为base64
            base64_str = base64.b64encode(image_bytes).decode('utf-8')

            return base64_str

        except asyncio.TimeoutError:
            return await self._adb_screenshot(device_manager)
        except Exception:
            return await self._adb_screenshot(device_manager)

    async def capture_frame_raw(self, device_id: str) -> Optional[bytes]:
        """获取原始帧数据（用于WebSocket流）"""
        device_manager = self.device_manager.get_device(device_id)
        if not device_manager or not device_manager.is_connected:
            return None

        try:
            loop = asyncio.get_running_loop()

            def capture():
                img = device_manager.device.screenshot()
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=80)
                return buffer.getvalue()

            return await asyncio.wait_for(
                loop.run_in_executor(None, capture),
                timeout=2.0
            )
        except Exception:
            return None

    async def capture_frame_incremental(self, device_id: str) -> Optional[Tuple[bytes, bool]]:
        """增量帧捕获 - 返回 (帧数据, 是否变化)"""
        frame_data = await self.capture_frame_raw(device_id)
        if frame_data is None:
            return None

        # 计算帧哈希
        current_hash = hashlib.md5(frame_data).hexdigest()
        last_hash = self._last_frame_hash.get(device_id)

        is_changed = current_hash != last_hash

        if is_changed:
            self._last_frame_hash[device_id] = current_hash
            self._last_frame_data[device_id] = frame_data

        return (frame_data, is_changed)

    def get_last_frame(self, device_id: str) -> Optional[bytes]:
        """获取最后一帧（用于新连接时快速响应）"""
        return self._last_frame_data.get(device_id)

    async def _adb_screenshot(self, device_manager) -> str:
        """使用ADB命令直接截图（备用方法）"""
        try:
            device_id = device_manager.device_id

            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._execute_adb_screencap, device_id),
                timeout=5.0
            )

            if result and len(result) > 0:
                base64_str = base64.b64encode(result).decode('utf-8')
                return base64_str
            else:
                raise Exception("ADB截图返回空数据")

        except asyncio.TimeoutError:
            raise Exception("ADB截图超时")
        except Exception as e:
            raise Exception(f"ADB截图失败: {str(e)}")

    def _execute_adb_screencap(self, device_id: str) -> bytes:
        """执行ADB截图命令"""
        try:
            result = subprocess.run([
                'adb', '-s', device_id, 'exec-out', 'screencap', '-p'
            ], capture_output=True, timeout=4)

            if result.returncode == 0 and result.stdout:
                return result.stdout
            else:
                error_msg = result.stderr.decode('utf-8') if result.stderr else "unknown error"
                raise Exception(f"ADB screencap failed: {error_msg}")

        except subprocess.TimeoutExpired:
            raise Exception("ADB screencap timeout")
        except Exception as e:
            raise Exception(f"ADB error: {str(e)}")
    
    async def _get_ui_hierarchy(self, device_manager) -> dict:
        """获取UI层次结构"""
        try:
            # 获取UI dump，设置超时
            loop = asyncio.get_running_loop()
            ui_xml = await asyncio.wait_for(
                loop.run_in_executor(None, device_manager.device.dump_hierarchy),
                timeout=15.0
            )

            # 解析XML
            if not ui_xml or ui_xml.strip() == "":
                raise Exception("UI dump返回空内容")

            root = ET.fromstring(ui_xml)

            # 转换为结构化数据
            hierarchy = self._parse_xml_node(root)

            return hierarchy

        except asyncio.TimeoutError:
            raise Exception("UI层次结构获取超时，请检查设备连接")
        except ET.ParseError as e:
            raise Exception(f"UI层次结构XML解析失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取UI层次结构失败: {str(e)}")
    
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

# QNX系统专用的视觉检测器
class QNXVisualDetector:
    """基于OpenCV的QNX UI元素视觉检测器"""
    
    def __init__(self):
        self.template_database = {}
        self.element_cache = {}
    
    def detect_circles(self, image: np.ndarray, min_radius: int = 10, max_radius: int = 100) -> List[Dict]:
        """检测图像中的圆形元素（按钮、开关等）"""
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 应用中值滤波降噪
            gray = cv2.medianBlur(gray, 5)
            
            # 霍夫圆检测
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=30,  # 圆心之间最小距离
                param1=50,   # 高阈值
                param2=30,   # 累加器阈值
                minRadius=min_radius,
                maxRadius=max_radius
            )
            
            detected_circles = []
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                
                for (x, y, r) in circles:
                    # 计算边界框
                    left = max(0, x - r)
                    top = max(0, y - r)
                    right = min(image.shape[1], x + r)
                    bottom = min(image.shape[0], y + r)
                    
                    # 提取圆形区域进行颜色分析
                    roi = image[top:bottom, left:right]
                    avg_color = self._analyze_average_color(roi)
                    
                    detected_circles.append({
                        'type': 'circle',
                        'center': (int(x), int(y)),
                        'radius': int(r),
                        'bounds': [left, top, right, bottom],
                        'avg_color': avg_color,
                        'confidence': 0.8,  # 基础置信度
                        'semantic_name': self._infer_circle_semantic_name(roi, r)
                    })

            return detected_circles

        except Exception:
            return []
    
    def detect_rectangles(self, image: np.ndarray, min_area: int = 100) -> List[Dict]:
        """检测图像中的矩形元素（按钮、输入框等）"""
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detected_rectangles = []
            
            for contour in contours:
                # 轮廓近似
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 检查是否为矩形（4个顶点）
                if len(approx) == 4:
                    # 计算面积
                    area = cv2.contourArea(contour)
                    if area < min_area:
                        continue
                    
                    # 获取边界框
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 检查长宽比，过滤掉过于细长的形状
                    aspect_ratio = max(w, h) / min(w, h)
                    if aspect_ratio > 10:
                        continue
                    
                    # 提取矩形区域
                    roi = image[y:y+h, x:x+w]
                    avg_color = self._analyze_average_color(roi)
                    
                    detected_rectangles.append({
                        'type': 'rectangle',
                        'bounds': [x, y, x+w, y+h],
                        'area': int(area),
                        'aspect_ratio': round(aspect_ratio, 2),
                        'avg_color': avg_color,
                        'confidence': 0.7,
                        'semantic_name': self._infer_rectangle_semantic_name(roi, w, h, aspect_ratio)
                    })
            
            print(f"[DETECT] 检测到 {len(detected_rectangles)} 个矩形元素")
            return detected_rectangles
            
        except Exception as e:
            print(f"[ERROR] 矩形检测失败: {e}")
            return []
    
    def calculate_image_hash(self, image: np.ndarray, hash_type: str = 'average') -> str:
        """计算图像哈希值用于相似度比较"""
        try:
            # 转换为PIL图像
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # 根据类型计算哈希
            if hash_type == 'average':
                return str(imagehash.average_hash(pil_image))
            elif hash_type == 'perceptual':
                return str(imagehash.phash(pil_image))
            elif hash_type == 'difference':
                return str(imagehash.dhash(pil_image))
            elif hash_type == 'wavelet':
                return str(imagehash.whash(pil_image))
            else:
                return str(imagehash.average_hash(pil_image))
                
        except Exception as e:
            print(f"[ERROR] 图像哈希计算失败: {e}")
            return ""
    
    def compare_images(self, hash1: str, hash2: str) -> float:
        """比较两个图像哈希的相似度"""
        try:
            if not hash1 or not hash2:
                return 0.0
            
            # 计算汉明距离
            hamming_distance = bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
            max_distance = len(hash1) * 4  # 16进制每位代表4位
            similarity = 1.0 - (hamming_distance / max_distance)
            
            return max(0.0, similarity)
            
        except Exception as e:
            print(f"[ERROR] 图像相似度比较失败: {e}")
            return 0.0
    
    def _analyze_average_color(self, roi: np.ndarray) -> Dict:
        """分析区域的平均颜色"""
        try:
            if len(roi.shape) == 3:
                # BGR格式
                mean_color = np.mean(roi, axis=(0, 1))
                return {
                    'bgr': [int(mean_color[0]), int(mean_color[1]), int(mean_color[2])],
                    'dominant_channel': int(np.argmax(mean_color))
                }
            else:
                # 灰度图
                mean_gray = np.mean(roi)
                return {
                    'gray': int(mean_gray),
                    'brightness': 'dark' if mean_gray < 128 else 'bright'
                }
        except Exception:
            return {'error': 'color_analysis_failed'}
    
    def _infer_circle_semantic_name(self, roi: np.ndarray, radius: int) -> str:
        """根据圆形特征推断语义名称"""
        try:
            # 基于大小分类
            if radius < 20:
                return "small_button_or_indicator"
            elif radius < 50:
                return "medium_button_or_switch"
            else:
                return "large_button_or_control"
        except Exception:
            return "circular_element"
    
    def _infer_rectangle_semantic_name(self, roi: np.ndarray, width: int, height: int, aspect_ratio: float) -> str:
        """根据矩形特征推断语义名称"""
        try:
            # 基于长宽比和尺寸分类
            if aspect_ratio > 3:
                if height < 50:
                    return "horizontal_slider_or_bar"
                else:
                    return "horizontal_panel_or_strip"
            elif aspect_ratio < 0.5:
                return "vertical_bar_or_indicator"
            elif width < 100 and height < 100:
                return "small_button_or_icon"
            elif width > 200 or height > 200:
                return "large_panel_or_container"
            else:
                return "medium_button_or_field"
        except Exception:
            return "rectangular_element"
    
    def detect_ui_elements_in_qnx_screenshot(self, screenshot_bytes: bytes) -> Dict:
        """分析QNX截图中的UI元素"""
        try:
            # 将字节数据转换为OpenCV图像
            nparr = np.frombuffer(screenshot_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise Exception("无法解码截图数据")
            
            # 获取图像尺寸
            height, width = image.shape[:2]
            
            # 检测圆形元素
            circles = self.detect_circles(image)
            
            # 检测矩形元素
            rectangles = self.detect_rectangles(image)
            
            # 计算整体截图哈希
            screenshot_hash = self.calculate_image_hash(image)
            
            result = {
                'success': True,
                'image_info': {
                    'width': width,
                    'height': height,
                    'channels': image.shape[2] if len(image.shape) == 3 else 1,
                    'hash': screenshot_hash
                },
                'detected_elements': {
                    'circles': circles,
                    'rectangles': rectangles,
                    'total_count': len(circles) + len(rectangles)
                },
                'analysis_metadata': {
                    'detector_type': 'opencv_visual',
                    'target_system': 'qnx',
                    'detection_methods': ['hough_circles', 'contour_rectangles']
                }
            }
            
            print(f"[QNX-DETECT] 分析完成: 圆形={len(circles)}, 矩形={len(rectangles)}")
            return result
            
        except Exception as e:
            print(f"[ERROR] QNX截图分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'detected_elements': {'circles': [], 'rectangles': [], 'total_count': 0}
            }

# 智能标记器 - 基于特征匹配和上下文分析
class SmartLabeler:
    """基于SIFT/ORB特征匹配和模板数据库的智能UI元素标记器"""
    
    def __init__(self):
        # 特征检测器
        self.sift = cv2.SIFT_create(nfeatures=500, contrastThreshold=0.04)
        self.orb = cv2.ORB_create(nfeatures=500, scaleFactor=1.2, nlevels=8)
        self.bf_matcher = cv2.BFMatcher()
        
        # 模板数据库 - 汽车HMI界面特征模板
        self.template_database = self._initialize_template_database()
        
        # 颜色分析器
        self.color_analyzer = ColorAnalyzer()
        
    def _initialize_template_database(self) -> Dict:
        """初始化汽车HMI界面特征模板数据库"""
        return {
            'buttons': {
                'radio_button': {
                    'size_range': (20, 60),
                    'aspect_ratio_range': (0.8, 1.2),
                    'color_hints': ['blue', 'green', 'gray'],
                    'context_keywords': ['radio', 'am', 'fm', 'station']
                },
                'navigation_button': {
                    'size_range': (40, 100),
                    'aspect_ratio_range': (0.7, 1.5),
                    'color_hints': ['blue', 'white', 'gray'],
                    'context_keywords': ['map', 'nav', 'route', 'destination']
                },
                'climate_button': {
                    'size_range': (30, 80),
                    'aspect_ratio_range': (0.8, 1.3),
                    'color_hints': ['red', 'blue', 'white'],
                    'context_keywords': ['temp', 'ac', 'heat', 'fan']
                }
            },
            'indicators': {
                'volume_indicator': {
                    'size_range': (10, 40),
                    'aspect_ratio_range': (0.5, 2.0),
                    'color_hints': ['green', 'blue', 'white'],
                    'context_keywords': ['volume', 'sound', 'audio']
                },
                'battery_indicator': {
                    'size_range': (15, 50),
                    'aspect_ratio_range': (1.5, 3.0),
                    'color_hints': ['green', 'yellow', 'red'],
                    'context_keywords': ['battery', 'charge', 'power']
                }
            },
            'sliders': {
                'volume_slider': {
                    'size_range': (100, 300),
                    'aspect_ratio_range': (3.0, 8.0),
                    'color_hints': ['blue', 'gray', 'white'],
                    'context_keywords': ['volume', 'sound', 'level']
                },
                'brightness_slider': {
                    'size_range': (80, 250),
                    'aspect_ratio_range': (3.0, 8.0),
                    'color_hints': ['yellow', 'white', 'gray'],
                    'context_keywords': ['bright', 'dim', 'display']
                }
            }
        }
    
    def extract_features(self, image: np.ndarray, method: str = 'sift') -> Tuple[List, np.ndarray]:
        """提取图像特征点和描述符"""
        try:
            if method == 'sift':
                keypoints, descriptors = self.sift.detectAndCompute(image, None)
            elif method == 'orb':
                keypoints, descriptors = self.orb.detectAndCompute(image, None)
            else:
                raise ValueError(f"不支持的特征提取方法: {method}")
            
            if descriptors is None:
                return [], np.array([])
            
            print(f"[FEATURE] {method.upper()}特征提取: {len(keypoints)} 个关键点")
            return keypoints, descriptors
            
        except Exception as e:
            print(f"[ERROR] 特征提取失败: {e}")
            return [], np.array([])
    
    def match_with_template(self, element_descriptors: np.ndarray, template_descriptors: np.ndarray, 
                          method: str = 'sift', ratio_threshold: float = 0.7) -> List:
        """将元素特征与模板特征进行匹配"""
        try:
            if element_descriptors.size == 0 or template_descriptors.size == 0:
                return []
            
            if method == 'sift':
                # SIFT使用FLANN匹配器和比值测试
                flann_params = dict(algorithm=1, trees=5)
                flann = cv2.FlannBasedMatcher(flann_params, {})
                matches = flann.knnMatch(element_descriptors, template_descriptors, k=2)
                
                # Lowe比值测试过滤匹配
                good_matches = []
                for match_pair in matches:
                    if len(match_pair) == 2:
                        m, n = match_pair
                        if m.distance < ratio_threshold * n.distance:
                            good_matches.append(m)
            else:
                # ORB使用汉明距离匹配器
                matches = self.bf_matcher.match(element_descriptors, template_descriptors)
                good_matches = sorted(matches, key=lambda x: x.distance)[:20]
            
            print(f"[MATCH] 特征匹配结果: {len(good_matches)} 个良好匹配")
            return good_matches
            
        except Exception as e:
            print(f"[ERROR] 特征匹配失败: {e}")
            return []
    
    def multi_scale_template_matching(self, image: np.ndarray, template: np.ndarray, 
                                    scales: List[float] = [0.5, 0.75, 1.0, 1.25, 1.5]) -> Dict:
        """多尺度模板匹配"""
        try:
            best_match = None
            best_score = 0
            
            for scale in scales:
                # 缩放模板
                scaled_template = cv2.resize(template, None, fx=scale, fy=scale)
                
                # 检查模板是否小于图像
                if (scaled_template.shape[0] >= image.shape[0] or 
                    scaled_template.shape[1] >= image.shape[1]):
                    continue
                
                # 模板匹配
                result = cv2.matchTemplate(image, scaled_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                # 更新最佳匹配
                if max_val > best_score:
                    best_score = max_val
                    best_match = {
                        'score': max_val,
                        'location': max_loc,
                        'scale': scale,
                        'template_size': scaled_template.shape[:2]
                    }
            
            return best_match or {}
            
        except Exception as e:
            print(f"[ERROR] 多尺度模板匹配失败: {e}")
            return {}
    
    def analyze_semantic_context(self, element: Dict, surrounding_elements: List[Dict]) -> str:
        """基于上下文分析推断元素语义名称"""
        try:
            element_type = element.get('type', 'unknown')
            bounds = element.get('bounds', [0, 0, 0, 0])
            
            # 计算元素几何特征
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            aspect_ratio = width / max(height, 1)
            area = width * height
            
            # 分析颜色特征
            avg_color = element.get('avg_color', {})
            dominant_color = self._get_dominant_color_name(avg_color)
            
            # 空间关系分析
            spatial_context = self._analyze_spatial_relationships(element, surrounding_elements)
            
            # 在模板数据库中查找匹配
            best_match = self._find_best_template_match(
                element_type, width, height, aspect_ratio, dominant_color, spatial_context
            )
            
            # 构建语义名称
            semantic_name = self._construct_semantic_name(best_match, element_type, spatial_context)
            
            print(f"[SEMANTIC] 元素语义分析: {element_type} -> {semantic_name}")
            return semantic_name
            
        except Exception as e:
            print(f"[ERROR] 语义分析失败: {e}")
            return f"{element.get('type', 'unknown')}_element"
    
    def _get_dominant_color_name(self, avg_color: Dict) -> str:
        """获取主色调名称"""
        try:
            if 'bgr' in avg_color:
                b, g, r = avg_color['bgr']
                
                # 简单颜色分类
                if r > g and r > b and r > 100:
                    return 'red'
                elif g > r and g > b and g > 100:
                    return 'green'
                elif b > r and b > g and b > 100:
                    return 'blue'
                elif r + g + b < 150:
                    return 'dark'
                elif r + g + b > 600:
                    return 'white'
                else:
                    return 'gray'
            
            return 'unknown'
            
        except Exception:
            return 'unknown'
    
    def _analyze_spatial_relationships(self, element: Dict, surrounding_elements: List[Dict]) -> Dict:
        """分析元素的空间关系"""
        try:
            bounds = element.get('bounds', [0, 0, 0, 0])
            center_x = (bounds[0] + bounds[2]) / 2
            center_y = (bounds[1] + bounds[3]) / 2
            
            relationships = {
                'nearby_elements': [],
                'alignment': 'none',
                'position': 'center'
            }
            
            # 分析附近元素
            for other in surrounding_elements:
                other_bounds = other.get('bounds', [0, 0, 0, 0])
                other_center_x = (other_bounds[0] + other_bounds[2]) / 2
                other_center_y = (other_bounds[1] + other_bounds[3]) / 2
                
                # 计算距离
                distance = np.sqrt((center_x - other_center_x)**2 + (center_y - other_center_y)**2)
                
                if distance < 100:  # 100像素内视为附近
                    relationships['nearby_elements'].append({
                        'type': other.get('type', 'unknown'),
                        'distance': distance,
                        'relative_position': self._get_relative_position(bounds, other_bounds)
                    })
            
            return relationships
            
        except Exception:
            return {'nearby_elements': [], 'alignment': 'none', 'position': 'center'}
    
    def _get_relative_position(self, bounds1: List, bounds2: List) -> str:
        """获取两个元素的相对位置关系"""
        try:
            center1_x = (bounds1[0] + bounds1[2]) / 2
            center1_y = (bounds1[1] + bounds1[3]) / 2
            center2_x = (bounds2[0] + bounds2[2]) / 2
            center2_y = (bounds2[1] + bounds2[3]) / 2
            
            dx = center2_x - center1_x
            dy = center2_y - center1_y
            
            if abs(dx) > abs(dy):
                return 'right' if dx > 0 else 'left'
            else:
                return 'below' if dy > 0 else 'above'
                
        except Exception:
            return 'unknown'
    
    def _find_best_template_match(self, element_type: str, width: int, height: int, 
                                aspect_ratio: float, color: str, context: Dict) -> Dict:
        """在模板数据库中查找最佳匹配"""
        try:
            best_match = None
            best_score = 0
            
            # 遍历模板数据库
            for category, templates in self.template_database.items():
                for template_name, template_info in templates.items():
                    score = 0
                    
                    # 尺寸匹配评分
                    size_range = template_info['size_range']
                    if size_range[0] <= max(width, height) <= size_range[1]:
                        score += 0.3
                    
                    # 长宽比匹配评分
                    ratio_range = template_info['aspect_ratio_range']
                    if ratio_range[0] <= aspect_ratio <= ratio_range[1]:
                        score += 0.3
                    
                    # 颜色匹配评分
                    if color in template_info['color_hints']:
                        score += 0.2
                    
                    # 上下文关键词匹配评分
                    for nearby in context.get('nearby_elements', []):
                        for keyword in template_info['context_keywords']:
                            if keyword in nearby.get('type', '').lower():
                                score += 0.2
                                break
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'category': category,
                            'template_name': template_name,
                            'confidence': score,
                            'template_info': template_info
                        }
            
            return best_match or {}
            
        except Exception as e:
            print(f"[ERROR] 模板匹配失败: {e}")
            return {}
    
    def _construct_semantic_name(self, best_match: Dict, element_type: str, context: Dict) -> str:
        """构建语义名称"""
        try:
            if best_match and best_match.get('confidence', 0) > 0.3:
                # 使用模板匹配结果
                category = best_match['category'].rstrip('s')  # 去掉复数
                template_name = best_match['template_name']
                return f"{category}_{template_name}"
            else:
                # 基于几何特征的回退命名
                if element_type == 'circle':
                    return f"circular_{self._infer_circle_function(context)}"
                elif element_type == 'rectangle':
                    return f"rectangular_{self._infer_rectangle_function(context)}"
                else:
                    return f"{element_type}_control_element"
                    
        except Exception:
            return f"{element_type}_element"
    
    def _infer_circle_function(self, context: Dict) -> str:
        """推断圆形元素功能"""
        nearby = [elem.get('type', '') for elem in context.get('nearby_elements', [])]
        
        if any('slider' in elem or 'bar' in elem for elem in nearby):
            return 'knob'
        elif len(nearby) > 3:
            return 'button_in_cluster'
        else:
            return 'button'
    
    def _infer_rectangle_function(self, context: Dict) -> str:
        """推断矩形元素功能"""
        nearby = [elem.get('type', '') for elem in context.get('nearby_elements', [])]
        
        if any('text' in elem or 'label' in elem for elem in nearby):
            return 'input_field'
        elif len(nearby) >= 2:
            return 'panel_section'
        else:
            return 'button'

# 颜色分析器
class ColorAnalyzer:
    """基于HSV颜色空间和K-means聚类的颜色分析器"""
    
    def __init__(self):
        self.color_names = {
            'red': ([0, 100, 100], [10, 255, 255]),
            'green': ([40, 40, 40], [80, 255, 255]),
            'blue': ([100, 100, 100], [130, 255, 255]),
            'yellow': ([20, 100, 100], [30, 255, 255]),
            'orange': ([10, 100, 100], [20, 255, 255]),
            'purple': ([130, 100, 100], [160, 255, 255])
        }
    
    def analyze_dominant_colors(self, roi: np.ndarray, k: int = 3) -> List[Dict]:
        """使用K-means聚类分析ROI的主导颜色"""
        try:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # 重塑为K-means输入格式
            data = hsv.reshape((-1, 3))
            data = np.float32(data)
            
            # K-means聚类
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # 统计每个簇的像素数量
            unique, counts = np.unique(labels, return_counts=True)
            
            # 构建颜色信息
            color_info = []
            for i, center in enumerate(centers):
                percentage = counts[i] / len(data) * 100
                color_name = self._hsv_to_color_name(center)
                
                color_info.append({
                    'hsv': center.astype(int).tolist(),
                    'color_name': color_name,
                    'percentage': round(percentage, 2)
                })
            
            # 按比例排序
            color_info.sort(key=lambda x: x['percentage'], reverse=True)
            return color_info
            
        except Exception as e:
            print(f"[ERROR] 颜色分析失败: {e}")
            return []
    
    def _hsv_to_color_name(self, hsv: np.ndarray) -> str:
        """将HSV值映射到颜色名称"""
        try:
            h, s, v = hsv
            
            # 检查是否为灰色/白色/黑色
            if s < 30:
                if v < 50:
                    return 'black'
                elif v > 200:
                    return 'white'
                else:
                    return 'gray'
            
            # 检查预定义颜色范围
            for color_name, (lower, upper) in self.color_names.items():
                if (lower[0] <= h <= upper[0] and 
                    lower[1] <= s <= upper[1] and 
                    lower[2] <= v <= upper[2]):
                    return color_name
            
            return 'unknown'
            
        except Exception:
            return 'unknown'

# 上下文分析器
class ContextAnalyzer:
    """空间关系和布局模式分析器"""
    
    def __init__(self):
        self.layout_patterns = {
            'horizontal_menu': {'min_elements': 3, 'alignment': 'horizontal', 'spacing_tolerance': 0.3},
            'vertical_list': {'min_elements': 2, 'alignment': 'vertical', 'spacing_tolerance': 0.4},
            'grid_layout': {'min_elements': 4, 'alignment': 'grid', 'spacing_tolerance': 0.2},
            'control_cluster': {'min_elements': 3, 'max_distance': 150, 'mixed_types': True}
        }
    
    def analyze_layout_patterns(self, elements: List[Dict]) -> Dict:
        """分析元素的布局模式"""
        try:
            if len(elements) < 2:
                return {'pattern': 'isolated', 'confidence': 1.0}
            
            # 提取元素中心点
            centers = []
            for elem in elements:
                bounds = elem.get('bounds', [0, 0, 0, 0])
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
                centers.append((center_x, center_y))
            
            # 检测各种布局模式
            pattern_scores = {}
            
            # 水平排列检测
            pattern_scores['horizontal_menu'] = self._detect_horizontal_alignment(centers)
            
            # 垂直排列检测
            pattern_scores['vertical_list'] = self._detect_vertical_alignment(centers)
            
            # 网格布局检测
            pattern_scores['grid_layout'] = self._detect_grid_alignment(centers)
            
            # 控制簇检测
            pattern_scores['control_cluster'] = self._detect_control_cluster(elements)
            
            # 选择最高分的模式
            best_pattern = max(pattern_scores.keys(), key=lambda k: pattern_scores[k])
            confidence = pattern_scores[best_pattern]
            
            return {
                'pattern': best_pattern,
                'confidence': confidence,
                'all_scores': pattern_scores
            }
            
        except Exception as e:
            print(f"[ERROR] 布局模式分析失败: {e}")
            return {'pattern': 'unknown', 'confidence': 0.0}
    
    def _detect_horizontal_alignment(self, centers: List[Tuple]) -> float:
        """检测水平对齐"""
        try:
            if len(centers) < 3:
                return 0.0
            
            y_coords = [center[1] for center in centers]
            y_variance = np.var(y_coords)
            mean_y = np.mean(y_coords)
            
            # 计算对齐度 (方差越小对齐度越高)
            alignment_score = max(0, 1.0 - y_variance / (mean_y + 1))
            
            return min(alignment_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_vertical_alignment(self, centers: List[Tuple]) -> float:
        """检测垂直对齐"""
        try:
            if len(centers) < 2:
                return 0.0
            
            x_coords = [center[0] for center in centers]
            x_variance = np.var(x_coords)
            mean_x = np.mean(x_coords)
            
            alignment_score = max(0, 1.0 - x_variance / (mean_x + 1))
            
            return min(alignment_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_grid_alignment(self, centers: List[Tuple]) -> float:
        """检测网格对齐"""
        try:
            if len(centers) < 4:
                return 0.0
            
            # 简化的网格检测：检查是否有多个相同的x或y坐标
            x_coords = [center[0] for center in centers]
            y_coords = [center[1] for center in centers]
            
            # 统计相近坐标的数量
            x_groups = self._group_similar_values(x_coords, tolerance=50)
            y_groups = self._group_similar_values(y_coords, tolerance=50)
            
            # 网格得分基于行列的数量
            grid_score = min(len(x_groups), len(y_groups)) / max(len(centers) ** 0.5, 2)
            
            return min(grid_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _detect_control_cluster(self, elements: List[Dict]) -> float:
        """检测控制元素簇"""
        try:
            if len(elements) < 3:
                return 0.0
            
            # 计算平均距离
            centers = []
            for elem in elements:
                bounds = elem.get('bounds', [0, 0, 0, 0])
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
                centers.append((center_x, center_y))
            
            distances = []
            for i in range(len(centers)):
                for j in range(i + 1, len(centers)):
                    dist = np.sqrt((centers[i][0] - centers[j][0])**2 + 
                                 (centers[i][1] - centers[j][1])**2)
                    distances.append(dist)
            
            avg_distance = np.mean(distances)
            
            # 簇得分：距离越近得分越高
            cluster_score = max(0, 1.0 - avg_distance / 300)
            
            return min(cluster_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _group_similar_values(self, values: List[float], tolerance: float = 30) -> List[List[float]]:
        """将相似值分组"""
        try:
            if not values:
                return []
            
            sorted_values = sorted(values)
            groups = []
            current_group = [sorted_values[0]]
            
            for value in sorted_values[1:]:
                if abs(value - current_group[-1]) <= tolerance:
                    current_group.append(value)
                else:
                    groups.append(current_group)
                    current_group = [value]
            
            groups.append(current_group)
            return groups
            
        except Exception:
            return []