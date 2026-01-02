"""
基础视觉检测器模块
使用OpenCV实现基础形状检测和图像分析
"""

import cv2
import numpy as np
import imagehash
from PIL import Image
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BasicDetector:
    """基础视觉检测器 - 第1-2轮核心实现"""
    
    def __init__(self):
        self.logger = logger
        self.last_detection_results = []
        self.detection_cache = {}
        
    def detect_circles(self, image: np.ndarray, 
                      min_radius: int = 10, 
                      max_radius: int = 100) -> List[Dict]:
        """
        检测图像中的圆形元素（按钮、开关等）
        
        Args:
            image: 输入图像（numpy数组）
            min_radius: 最小半径
            max_radius: 最大半径
        
        Returns:
            List[Dict]: 检测到的圆形元素列表
        """
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
                dp=1,                # 累加器分辨率与图像分辨率的反比
                minDist=30,          # 圆心之间的最小距离
                param1=50,           # Canny边缘检测的高阈值
                param2=30,           # 累加器阈值
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
                    
                    # 语义推断
                    semantic_name = self._infer_circle_semantic_name(r)
                    
                    detected_circles.append({
                        'type': 'circle',
                        'center': (int(x), int(y)),
                        'radius': int(r),
                        'bounds': [left, top, right, bottom],
                        'avg_color': avg_color,
                        'confidence': 0.8,
                        'semantic_name': semantic_name
                    })
            
            self.logger.info(f"检测到 {len(detected_circles)} 个圆形元素")
            return detected_circles
            
        except Exception as e:
            self.logger.error(f"圆形检测失败: {e}")
            return []
    
    def detect_rectangles(self, image: np.ndarray, 
                         min_area: int = 100) -> List[Dict]:
        """
        检测图像中的矩形元素（按钮、输入框等）
        
        Args:
            image: 输入图像（numpy数组）
            min_area: 最小面积阈值
        
        Returns:
            List[Dict]: 检测到的矩形元素列表
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                edges, 
                cv2.RETR_EXTERNAL,      # 只检测外部轮廓
                cv2.CHAIN_APPROX_SIMPLE  # 压缩水平、垂直和对角线段
            )
            
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
                    
                    # 语义推断
                    semantic_name = self._infer_rectangle_semantic_name(w, h, aspect_ratio)
                    
                    detected_rectangles.append({
                        'type': 'rectangle',
                        'bounds': [x, y, x+w, y+h],
                        'width': w,
                        'height': h,
                        'area': int(area),
                        'aspect_ratio': round(aspect_ratio, 2),
                        'avg_color': avg_color,
                        'confidence': 0.7,
                        'semantic_name': semantic_name
                    })
            
            self.logger.info(f"检测到 {len(detected_rectangles)} 个矩形元素")
            return detected_rectangles
            
        except Exception as e:
            self.logger.error(f"矩形检测失败: {e}")
            return []
    
    def calculate_image_hash(self, image: np.ndarray, 
                           hash_type: str = 'average') -> str:
        """
        计算图像哈希值用于相似度比较
        
        Args:
            image: 输入图像（numpy数组）
            hash_type: 哈希类型 ('average', 'perceptual', 'difference', 'wavelet')
        
        Returns:
            str: 图像哈希值（16进制字符串）
        """
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
                hash_value = imagehash.average_hash(pil_image)
            elif hash_type == 'perceptual':
                hash_value = imagehash.phash(pil_image)
            elif hash_type == 'difference':
                hash_value = imagehash.dhash(pil_image)
            elif hash_type == 'wavelet':
                hash_value = imagehash.whash(pil_image)
            else:
                hash_value = imagehash.average_hash(pil_image)
            
            hash_str = str(hash_value)
            self.logger.debug(f"计算{hash_type}哈希: {hash_str}")
            return hash_str
            
        except Exception as e:
            self.logger.error(f"图像哈希计算失败: {e}")
            return ""
    
    def compare_images(self, hash1: str, hash2: str) -> float:
        """
        比较两个图像哈希的相似度
        
        Args:
            hash1: 第一个图像的哈希值
            hash2: 第二个图像的哈希值
        
        Returns:
            float: 相似度（0.0-1.0，1.0表示完全相同）
        """
        try:
            if not hash1 or not hash2:
                return 0.0
            
            # 计算汉明距离
            hamming_distance = bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
            
            # 最大可能的汉明距离（每个16进制字符代表4位）
            max_distance = len(hash1) * 4
            
            # 计算相似度
            similarity = 1.0 - (hamming_distance / max_distance)
            
            self.logger.debug(f"图像相似度: {similarity:.2f} (汉明距离: {hamming_distance})")
            return max(0.0, similarity)
            
        except Exception as e:
            self.logger.error(f"图像相似度比较失败: {e}")
            return 0.0
    
    def detect_all_elements(self, image: np.ndarray) -> Dict:
        """
        检测图像中的所有UI元素
        
        Args:
            image: 输入图像（numpy数组）
        
        Returns:
            Dict: 包含所有检测结果的字典
        """
        try:
            # 检测圆形元素
            circles = self.detect_circles(image)
            
            # 检测矩形元素  
            rectangles = self.detect_rectangles(image)
            
            # 计算图像哈希
            image_hash = self.calculate_image_hash(image)
            
            # 获取图像信息
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            
            result = {
                'success': True,
                'image_info': {
                    'width': width,
                    'height': height,
                    'channels': channels,
                    'hash': image_hash
                },
                'detected_elements': {
                    'circles': circles,
                    'rectangles': rectangles,
                    'total_count': len(circles) + len(rectangles)
                },
                'detection_metadata': {
                    'detector_type': 'opencv_basic',
                    'detection_methods': ['hough_circles', 'contour_rectangles']
                }
            }
            
            # 缓存结果
            self.last_detection_results = result
            self.detection_cache[image_hash] = result
            
            self.logger.info(f"元素检测完成: 圆形={len(circles)}, 矩形={len(rectangles)}")
            return result
            
        except Exception as e:
            self.logger.error(f"元素检测失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'detected_elements': {'circles': [], 'rectangles': [], 'total_count': 0}
            }
    
    def _analyze_average_color(self, roi: np.ndarray) -> Dict:
        """
        分析区域的平均颜色
        
        Args:
            roi: 感兴趣区域
        
        Returns:
            Dict: 颜色信息
        """
        try:
            if len(roi.shape) == 3:
                # BGR格式
                mean_color = np.mean(roi, axis=(0, 1))
                return {
                    'bgr': [int(mean_color[0]), int(mean_color[1]), int(mean_color[2])],
                    'dominant_channel': int(np.argmax(mean_color)),
                    'brightness': 'bright' if np.mean(mean_color) > 128 else 'dark'
                }
            else:
                # 灰度图
                mean_gray = np.mean(roi)
                return {
                    'gray': int(mean_gray),
                    'brightness': 'bright' if mean_gray > 128 else 'dark'
                }
        except Exception:
            return {'error': 'color_analysis_failed'}
    
    def _infer_circle_semantic_name(self, radius: int) -> str:
        """
        根据圆形半径推断语义名称
        
        Args:
            radius: 圆形半径
        
        Returns:
            str: 语义名称
        """
        if radius < 20:
            return "small_button_or_indicator"
        elif radius < 50:
            return "medium_button_or_switch"
        else:
            return "large_button_or_control"
    
    def _infer_rectangle_semantic_name(self, width: int, height: int, aspect_ratio: float) -> str:
        """
        根据矩形特征推断语义名称
        
        Args:
            width: 宽度
            height: 高度
            aspect_ratio: 长宽比
        
        Returns:
            str: 语义名称
        """
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
    
    def find_similar_images(self, image: np.ndarray, threshold: float = 0.9) -> List[str]:
        """
        在缓存中查找相似图像
        
        Args:
            image: 输入图像
            threshold: 相似度阈值
        
        Returns:
            List[str]: 相似图像的哈希值列表
        """
        try:
            current_hash = self.calculate_image_hash(image)
            similar_hashes = []
            
            for cached_hash in self.detection_cache.keys():
                similarity = self.compare_images(current_hash, cached_hash)
                if similarity >= threshold:
                    similar_hashes.append(cached_hash)
            
            self.logger.info(f"找到 {len(similar_hashes)} 个相似图像")
            return similar_hashes
            
        except Exception as e:
            self.logger.error(f"查找相似图像失败: {e}")
            return []