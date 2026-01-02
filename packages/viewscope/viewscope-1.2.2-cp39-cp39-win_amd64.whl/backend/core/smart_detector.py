#!/usr/bin/env python3
"""
智能检测器 - 基于深度学习和计算机视觉的精确UI元素检测
重点解决误检和过度检测问题
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
import math

logger = logging.getLogger(__name__)

class SmartDetector:
    """智能检测器 - 精确的UI元素检测和分类"""

    def __init__(self):
        self.logger = logger
        self.min_confidence = 0.7  # 提高置信度阈值
        self.context_analyzer = None

    def detect_precise_circles(self, image: np.ndarray) -> List[Dict]:
        """精确圆形检测 - 减少误检"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 更严格的预处理
            gray = cv2.GaussianBlur(gray, (5, 5), 1.2)

            # 自适应边缘检测
            edges = cv2.Canny(gray, 50, 150)

            # 使用更保守的参数 - 只检测明显的圆形
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=40,      # 增加最小距离，避免重复检测
                param1=100,      # 提高边缘检测阈值
                param2=35,       # 提高累加器阈值，减少误检
                minRadius=15,    # 适中的最小半径
                maxRadius=100    # 适中的最大半径
            )

            detected_circles = []
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")

                for (x, y, r) in circles:
                    # 验证圆形的有效性
                    if self._validate_circle(gray, x, y, r):
                        # 分析圆形区域特征
                        circle_info = self._analyze_circle_region(image, x, y, r)

                        if circle_info['confidence'] > self.min_confidence:
                            detected_circles.append(circle_info)

            self.logger.info(f"精确圆形检测: {len(detected_circles)} 个有效圆形")
            return detected_circles

        except Exception as e:
            self.logger.error(f"精确圆形检测失败: {e}")
            return []

    def _validate_circle(self, gray: np.ndarray, x: int, y: int, r: int) -> bool:
        """验证圆形的有效性"""
        try:
            # 边界检查
            if (x - r < 0 or y - r < 0 or
                x + r >= gray.shape[1] or y + r >= gray.shape[0]):
                return False

            # 提取圆形区域
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(mask, (x, y), r, 255, -1)
            roi = cv2.bitwise_and(gray, mask)

            # 检查圆形边界的连续性
            circle_edge = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(circle_edge, (x, y), r, 255, 2)

            # 计算边界上的梯度强度
            edges = cv2.Canny(gray, 50, 150)
            edge_intersection = cv2.bitwise_and(edges, circle_edge)
            edge_ratio = np.sum(edge_intersection > 0) / (2 * np.pi * r)

            # 有效圆形应该有足够的边界连续性
            return edge_ratio > 0.3

        except:
            return False

    def _analyze_circle_region(self, image: np.ndarray, x: int, y: int, r: int) -> Dict:
        """分析圆形区域特征"""
        try:
            # 提取ROI
            roi = image[max(0, y-r):min(image.shape[0], y+r),
                       max(0, x-r):min(image.shape[1], x+r)]

            # 颜色一致性分析
            if len(roi.shape) == 3:
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                roi_gray = roi.copy()

            # 计算区域的标准差 - 判断是否为均匀区域
            std_dev = np.std(roi_gray)
            mean_intensity = np.mean(roi_gray)

            # 边缘强度分析
            edges = cv2.Canny(roi_gray, 50, 150)
            edge_density = np.sum(edges > 0) / (roi_gray.shape[0] * roi_gray.shape[1])

            # 形状规律性分析
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            circularity = 0

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)

                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)

            # 综合置信度计算
            confidence = self._calculate_circle_confidence(
                std_dev, mean_intensity, edge_density, circularity, r
            )

            # 语义分类
            semantic_type = self._classify_circle_semantics(
                x, y, r, mean_intensity, std_dev, image.shape
            )

            return {
                'type': 'circle',
                'center': (int(x), int(y)),
                'radius': int(r),
                'bounds': [max(0, x-r), max(0, y-r),
                          min(image.shape[1], x+r), min(image.shape[0], y+r)],
                'confidence': confidence,
                'semantic_type': semantic_type,
                'features': {
                    'std_dev': float(std_dev),
                    'mean_intensity': float(mean_intensity),
                    'edge_density': float(edge_density),
                    'circularity': float(circularity)
                }
            }

        except Exception as e:
            self.logger.error(f"圆形区域分析失败: {e}")
            return {
                'type': 'circle',
                'center': (int(x), int(y)),
                'radius': int(r),
                'confidence': 0.0,
                'semantic_type': 'unknown'
            }

    def _calculate_circle_confidence(self, std_dev: float, mean_intensity: float,
                                   edge_density: float, circularity: float, radius: int) -> float:
        """计算圆形检测的置信度"""
        try:
            # 基础置信度
            confidence = 0.5

            # 大小合理性 (汽车仪表盘元素通常在15-80像素)
            if 15 <= radius <= 80:
                confidence += 0.2
            elif radius < 15 or radius > 100:
                confidence -= 0.3

            # 颜色一致性 (标准差适中的区域更可能是有意义的UI元素)
            if 20 <= std_dev <= 60:
                confidence += 0.2
            elif std_dev > 80:
                confidence -= 0.2

            # 亮度合理性 (过暗或过亮的区域可能是噪声)
            if 50 <= mean_intensity <= 200:
                confidence += 0.1
            else:
                confidence -= 0.1

            # 边缘密度 (适中的边缘密度表明有结构化内容)
            if 0.1 <= edge_density <= 0.4:
                confidence += 0.2
            elif edge_density > 0.6:
                confidence -= 0.3

            # 圆形度 (接近1表示更圆)
            if circularity > 0.7:
                confidence += 0.3
            elif circularity < 0.5:
                confidence -= 0.2

            return max(0.0, min(1.0, confidence))

        except:
            return 0.5

    def _classify_circle_semantics(self, x: int, y: int, r: int,
                                 mean_intensity: float, std_dev: float,
                                 image_shape: Tuple[int, int, int]) -> str:
        """基于位置和特征进行语义分类"""
        height, width = image_shape[:2]

        # 位置分析
        x_ratio = x / width
        y_ratio = y / height

        # 大小分析
        if r > 60:
            size_category = "large"
        elif r > 35:
            size_category = "medium"
        else:
            size_category = "small"

        # 位置分类
        if x_ratio < 0.3:
            location = "left_panel"
        elif x_ratio > 0.7:
            location = "right_panel"
        else:
            location = "center_area"

        # 亮度分类
        if mean_intensity > 150:
            brightness = "bright"
        elif mean_intensity < 80:
            brightness = "dark"
        else:
            brightness = "medium"

        # 语义推理
        if size_category == "large" and location == "center_area":
            return "main_gauge"
        elif size_category == "medium" and brightness == "bright":
            return "indicator_button"
        elif size_category == "small" and std_dev < 30:
            return "status_light"
        elif location == "left_panel" and size_category in ["medium", "large"]:
            return "trip_display"
        elif location == "right_panel" and size_category in ["medium", "large"]:
            return "info_display"
        else:
            return f"{size_category}_{location}_element"

    def detect_meaningful_rectangles(self, image: np.ndarray) -> List[Dict]:
        """检测有意义的矩形区域"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 多层边缘检测
            edges1 = cv2.Canny(gray, 50, 150)
            edges2 = cv2.Canny(gray, 80, 200)
            edges = cv2.bitwise_or(edges1, edges2)

            # 形态学操作 - 连接断开的边缘
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detected_rectangles = []

            for contour in contours:
                # 面积过滤 - 更严格的最小面积
                area = cv2.contourArea(contour)
                if area < 500:  # 提高最小面积阈值
                    continue

                # 多边形近似
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # 只保留4边形或接近4边形的轮廓
                if 4 <= len(approx) <= 6:
                    x, y, w, h = cv2.boundingRect(contour)

                    # 更严格的长宽比过滤
                    aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                    if aspect_ratio > 8:  # 过滤过于细长的形状
                        continue

                    # 面积比验证 - 轮廓面积与边界框面积的比值
                    bbox_area = w * h
                    if bbox_area > 0:
                        area_ratio = area / bbox_area
                        if area_ratio < 0.5:  # 过滤填充度太低的轮廓
                            continue

                    # 验证矩形的有效性
                    if self._validate_rectangle(gray, x, y, w, h):
                        rect_info = self._analyze_rectangle_region(image, x, y, w, h)

                        if rect_info['confidence'] > self.min_confidence:
                            detected_rectangles.append(rect_info)

            self.logger.info(f"有意义矩形检测: {len(detected_rectangles)} 个有效矩形")
            return detected_rectangles

        except Exception as e:
            self.logger.error(f"矩形检测失败: {e}")
            return []

    def _validate_rectangle(self, gray: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
        """验证矩形的有效性"""
        try:
            # 边界检查
            if x < 0 or y < 0 or x + w >= gray.shape[1] or y + h >= gray.shape[0]:
                return False

            # 尺寸合理性检查
            if w < 20 or h < 20 or w > gray.shape[1] * 0.8 or h > gray.shape[0] * 0.8:
                return False

            # 提取矩形区域
            roi = gray[y:y+h, x:x+w]

            # 检查是否有足够的内容变化
            std_dev = np.std(roi)
            if std_dev < 10:  # 过于均匀的区域可能不是有意义的UI元素
                return False

            # 检查边框特征
            border_thickness = 3
            top_border = roi[:border_thickness, :]
            bottom_border = roi[-border_thickness:, :]
            left_border = roi[:, :border_thickness]
            right_border = roi[:, -border_thickness:]

            # 计算边框的平均亮度差异
            border_std = np.std([np.mean(top_border), np.mean(bottom_border),
                               np.mean(left_border), np.mean(right_border)])

            # 有明显边框的矩形更可能是UI元素
            return border_std > 5

        except:
            return False

    def _analyze_rectangle_region(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> Dict:
        """分析矩形区域特征"""
        try:
            roi = image[y:y+h, x:x+w]

            if len(roi.shape) == 3:
                roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                roi_gray = roi.copy()

            # 特征计算
            std_dev = np.std(roi_gray)
            mean_intensity = np.mean(roi_gray)
            aspect_ratio = w / h if h > 0 else 0

            # 边缘分析
            edges = cv2.Canny(roi_gray, 50, 150)
            edge_density = np.sum(edges > 0) / (roi_gray.shape[0] * roi_gray.shape[1])

            # 置信度计算
            confidence = self._calculate_rectangle_confidence(
                w, h, std_dev, mean_intensity, edge_density, aspect_ratio
            )

            # 语义分类
            semantic_type = self._classify_rectangle_semantics(
                x, y, w, h, aspect_ratio, mean_intensity, image.shape
            )

            return {
                'type': 'rectangle',
                'bounds': [x, y, x + w, y + h],
                'width': w,
                'height': h,
                'area': w * h,
                'aspect_ratio': aspect_ratio,
                'confidence': confidence,
                'semantic_type': semantic_type,
                'features': {
                    'std_dev': float(std_dev),
                    'mean_intensity': float(mean_intensity),
                    'edge_density': float(edge_density)
                }
            }

        except Exception as e:
            self.logger.error(f"矩形区域分析失败: {e}")
            return {
                'type': 'rectangle',
                'bounds': [x, y, x + w, y + h],
                'confidence': 0.0,
                'semantic_type': 'unknown'
            }

    def _calculate_rectangle_confidence(self, w: int, h: int, std_dev: float,
                                      mean_intensity: float, edge_density: float,
                                      aspect_ratio: float) -> float:
        """计算矩形检测置信度"""
        try:
            confidence = 0.5

            # 尺寸合理性
            area = w * h
            if 500 <= area <= 50000:
                confidence += 0.2
            elif area < 500:
                confidence -= 0.3

            # 长宽比合理性
            if 0.3 <= aspect_ratio <= 5:
                confidence += 0.2
            elif aspect_ratio > 8:
                confidence -= 0.4

            # 内容丰富度
            if 15 <= std_dev <= 70:
                confidence += 0.2
            elif std_dev < 10:
                confidence -= 0.3

            # 亮度合理性
            if 40 <= mean_intensity <= 180:
                confidence += 0.1

            # 边缘密度
            if 0.05 <= edge_density <= 0.3:
                confidence += 0.2
            elif edge_density > 0.5:
                confidence -= 0.2

            return max(0.0, min(1.0, confidence))

        except:
            return 0.5

    def _classify_rectangle_semantics(self, x: int, y: int, w: int, h: int,
                                    aspect_ratio: float, mean_intensity: float,
                                    image_shape: Tuple[int, int, int]) -> str:
        """矩形语义分类"""
        height, width = image_shape[:2]

        x_ratio = x / width
        y_ratio = y / height

        # 基于长宽比的分类
        if aspect_ratio > 3:
            if h < 40:
                return "horizontal_bar"
            else:
                return "horizontal_panel"
        elif aspect_ratio < 0.5:
            return "vertical_bar"
        elif 0.8 <= aspect_ratio <= 1.2:
            return "square_button"

        # 基于位置的分类
        if y_ratio < 0.3:  # 上部区域
            return "top_info_panel"
        elif y_ratio > 0.7:  # 下部区域
            return "bottom_control_panel"
        elif x_ratio < 0.3:  # 左侧
            return "left_info_panel"
        elif x_ratio > 0.7:  # 右侧
            return "right_info_panel"
        else:
            return "central_display_area"

    def smart_detection(self, image: np.ndarray) -> Dict:
        """智能检测 - 整合所有优化算法"""
        try:
            start_time = cv2.getTickCount()

            # 精确圆形检测
            circles = self.detect_precise_circles(image)

            # 有意义矩形检测
            rectangles = self.detect_meaningful_rectangles(image)

            # 过滤和去重
            filtered_circles = self._filter_overlapping_elements(circles, 'circle')
            filtered_rectangles = self._filter_overlapping_elements(rectangles, 'rectangle')

            # 上下文验证
            validated_circles = self._context_validation(filtered_circles, image)
            validated_rectangles = self._context_validation(filtered_rectangles, image)

            all_elements = validated_circles + validated_rectangles

            # 计算处理时间
            end_time = cv2.getTickCount()
            processing_time = (end_time - start_time) / cv2.getTickFrequency()

            # 构建结果
            result = {
                'success': True,
                'total_elements': len(all_elements),
                'elements': all_elements,
                'statistics': {
                    'circles': len(validated_circles),
                    'rectangles': len(validated_rectangles),
                    'processing_time': round(processing_time, 3),
                    'average_confidence': np.mean([e['confidence'] for e in all_elements]) if all_elements else 0
                }
            }

            self.logger.info(f"智能检测完成: {len(all_elements)}个高置信度元素, 耗时{processing_time:.3f}s")
            return result

        except Exception as e:
            self.logger.error(f"智能检测失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_elements': 0,
                'elements': []
            }

    def _filter_overlapping_elements(self, elements: List[Dict], element_type: str) -> List[Dict]:
        """过滤重叠元素，保留置信度最高的"""
        if not elements:
            return []

        # 按置信度排序
        sorted_elements = sorted(elements, key=lambda x: x['confidence'], reverse=True)
        filtered = []

        for element in sorted_elements:
            is_overlapping = False

            for existing in filtered:
                if self._calculate_overlap(element, existing, element_type) > 0.5:
                    is_overlapping = True
                    break

            if not is_overlapping:
                filtered.append(element)

        return filtered

    def _calculate_overlap(self, elem1: Dict, elem2: Dict, element_type: str) -> float:
        """计算两个元素的重叠程度"""
        try:
            if element_type == 'circle':
                center1, r1 = elem1['center'], elem1['radius']
                center2, r2 = elem2['center'], elem2['radius']

                distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
                return max(0, (r1 + r2 - distance) / min(r1, r2))

            elif element_type == 'rectangle':
                bounds1 = elem1['bounds']
                bounds2 = elem2['bounds']

                # 计算交集
                x1 = max(bounds1[0], bounds2[0])
                y1 = max(bounds1[1], bounds2[1])
                x2 = min(bounds1[2], bounds2[2])
                y2 = min(bounds1[3], bounds2[3])

                if x1 >= x2 or y1 >= y2:
                    return 0

                intersection = (x2 - x1) * (y2 - y1)
                area1 = (bounds1[2] - bounds1[0]) * (bounds1[3] - bounds1[1])
                area2 = (bounds2[2] - bounds2[0]) * (bounds2[3] - bounds2[1])

                return intersection / min(area1, area2)

            return 0
        except:
            return 0

    def _context_validation(self, elements: List[Dict], image: np.ndarray) -> List[Dict]:
        """基于上下文的验证"""
        validated = []

        for element in elements:
            # 基础验证通过的才进行上下文验证
            if element['confidence'] > self.min_confidence:
                # 可以添加更多上下文验证逻辑
                # 例如：位置合理性、与其他元素的关系等
                validated.append(element)

        return validated