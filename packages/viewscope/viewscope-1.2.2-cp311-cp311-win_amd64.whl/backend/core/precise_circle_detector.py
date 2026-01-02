#!/usr/bin/env python3
"""
精确圆形检测器 - 专门解决圆形检测的混乱问题
使用多级验证和智能过滤，只检测真正有意义的圆形UI元素
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class PreciseCircleDetector:
    """精确圆形检测器 - 专注于汽车仪表盘圆形UI元素"""

    def __init__(self):
        self.logger = logger

        # 汽车仪表盘圆形元素的典型特征
        self.dashboard_circle_specs = {
            'speed_gauge': {'radius_range': (60, 120), 'position': 'center', 'features': 'complex_interior'},
            'rpm_gauge': {'radius_range': (50, 100), 'position': 'left_center', 'features': 'dial_marks'},
            'fuel_gauge': {'radius_range': (30, 80), 'position': 'corners', 'features': 'simple_fill'},
            'temp_gauge': {'radius_range': (30, 80), 'position': 'corners', 'features': 'simple_fill'},
            'warning_light': {'radius_range': (8, 25), 'position': 'scattered', 'features': 'solid_color'},
            'button': {'radius_range': (15, 50), 'position': 'edges', 'features': 'raised_appearance'},
            'indicator': {'radius_range': (12, 35), 'position': 'info_areas', 'features': 'text_or_icon'}
        }

    def detect_dashboard_circles(self, image: np.ndarray) -> List[Dict]:
        """检测仪表盘中的圆形元素"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            height, width = gray.shape
            self.logger.info(f"开始精确圆形检测，图像尺寸: {width}x{height}")

            # 第一阶段：保守的圆形检测
            primary_circles = self._detect_primary_circles(gray)
            self.logger.info(f"第一阶段检测到 {len(primary_circles)} 个候选圆形")

            # 第二阶段：验证每个圆形的真实性
            validated_circles = []
            for i, circle in enumerate(primary_circles):
                validation_score = self._validate_circle_reality(gray, circle, image.shape)

                if validation_score > 0.7:  # 高阈值过滤
                    circle['validation_score'] = validation_score
                    circle['circle_id'] = f"circle_{i+1}"
                    validated_circles.append(circle)
                    self.logger.debug(f"圆形 {i+1} 验证通过，评分: {validation_score:.2f}")

            self.logger.info(f"第二阶段验证通过 {len(validated_circles)} 个圆形")

            # 第三阶段：语义分析和分类
            classified_circles = []
            for circle in validated_circles:
                semantic_info = self._classify_dashboard_circle(circle, image, gray)
                circle.update(semantic_info)

                # 只保留置信度高的分类结果
                if circle['semantic_confidence'] > 0.6:
                    classified_circles.append(circle)

            self.logger.info(f"最终检测结果: {len(classified_circles)} 个高质量圆形元素")

            # 按置信度排序
            classified_circles.sort(key=lambda x: x['validation_score'], reverse=True)

            return classified_circles

        except Exception as e:
            self.logger.error(f"精确圆形检测失败: {e}")
            return []

    def _detect_primary_circles(self, gray: np.ndarray) -> List[Dict]:
        """第一阶段：使用优化参数检测主要圆形"""

        # 预处理 - 针对汽车仪表盘优化
        processed = cv2.GaussianBlur(gray, (3, 3), 1.0)

        # 使用保守的霍夫圆检测参数
        circles = cv2.HoughCircles(
            processed,
            cv2.HOUGH_GRADIENT,
            dp=1,                # 图像分辨率与累加器分辨率的反比
            minDist=50,          # 圆心间最小距离 - 避免重复检测
            param1=120,          # Canny边缘检测高阈值 - 提高要求
            param2=40,           # 累加器阈值 - 提高要求减少误检
            minRadius=8,         # 最小半径 - 覆盖指示灯
            maxRadius=150        # 最大半径 - 覆盖主仪表
        )

        detected_circles = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")

            for (x, y, r) in circles:
                # 边界检查
                if (x - r >= 0 and y - r >= 0 and
                    x + r < gray.shape[1] and y + r < gray.shape[0]):

                    detected_circles.append({
                        'center': (int(x), int(y)),
                        'radius': int(r),
                        'bounds': [x-r, y-r, x+r, y+r]
                    })

        return detected_circles

    def _validate_circle_reality(self, gray: np.ndarray, circle: Dict, image_shape: Tuple) -> float:
        """验证圆形的真实性 - 多维度评分"""
        try:
            center = circle['center']
            radius = circle['radius']
            x, y = center

            score = 0.0

            # 1. 几何验证 (0.3权重)
            geometric_score = self._validate_geometry(gray, x, y, radius)
            score += geometric_score * 0.3

            # 2. 边缘连续性验证 (0.25权重)
            edge_score = self._validate_edge_continuity(gray, x, y, radius)
            score += edge_score * 0.25

            # 3. 内部一致性验证 (0.2权重)
            consistency_score = self._validate_internal_consistency(gray, x, y, radius)
            score += consistency_score * 0.2

            # 4. 上下文合理性验证 (0.25权重)
            context_score = self._validate_context_reasonableness(x, y, radius, image_shape)
            score += context_score * 0.25

            return min(1.0, max(0.0, score))

        except Exception as e:
            self.logger.error(f"圆形验证失败: {e}")
            return 0.0

    def _validate_geometry(self, gray: np.ndarray, x: int, y: int, radius: int) -> float:
        """几何验证：检查圆形的几何特征"""
        try:
            # 创建圆形掩码
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(mask, (x, y), radius, 255, -1)

            # 创建圆环掩码（边缘区域）
            ring_mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(ring_mask, (x, y), radius, 255, 3)

            # 计算圆形区域的标准差
            roi = gray[mask > 0]
            if len(roi) == 0:
                return 0.0

            std_dev = np.std(roi)

            # 检查边缘强度
            edges = cv2.Canny(gray, 50, 150)
            edge_pixels = edges[ring_mask > 0]
            edge_ratio = np.sum(edge_pixels > 0) / len(edge_pixels) if len(edge_pixels) > 0 else 0

            # 几何评分
            geometry_score = 0.5

            # 半径合理性 (汽车仪表盘元素通常在8-150像素)
            if 8 <= radius <= 150:
                geometry_score += 0.3
            elif radius < 8 or radius > 200:
                geometry_score -= 0.4

            # 内部变化适中
            if 10 <= std_dev <= 80:
                geometry_score += 0.2
            elif std_dev < 5:  # 过于平坦
                geometry_score -= 0.3

            # 边缘清晰度
            if edge_ratio > 0.4:
                geometry_score += 0.2
            elif edge_ratio < 0.2:
                geometry_score -= 0.2

            return max(0.0, min(1.0, geometry_score))

        except:
            return 0.0

    def _validate_edge_continuity(self, gray: np.ndarray, x: int, y: int, radius: int) -> float:
        """边缘连续性验证：真正的圆形应该有连续的边缘"""
        try:
            # 创建圆形边缘模板
            template = np.zeros((radius*2+10, radius*2+10), dtype=np.uint8)
            center_template = (template.shape[1]//2, template.shape[0]//2)
            cv2.circle(template, center_template, radius, 255, 2)

            # 提取对应区域
            x1, y1 = max(0, x-radius-5), max(0, y-radius-5)
            x2, y2 = min(gray.shape[1], x+radius+5), min(gray.shape[0], y+radius+5)
            roi = gray[y1:y2, x1:x2]

            if roi.shape[0] == 0 or roi.shape[1] == 0:
                return 0.0

            # 边缘检测
            edges = cv2.Canny(roi, 50, 150)

            # 调整模板大小匹配ROI
            if template.shape != edges.shape:
                template = cv2.resize(template, (edges.shape[1], edges.shape[0]))

            # 计算边缘匹配度
            intersection = cv2.bitwise_and(edges, template)
            template_pixels = np.sum(template > 0)
            matching_pixels = np.sum(intersection > 0)

            if template_pixels == 0:
                return 0.0

            match_ratio = matching_pixels / template_pixels

            # 连续性评分
            continuity_score = min(1.0, match_ratio * 2.0)  # 放大匹配比例

            return continuity_score

        except:
            return 0.0

    def _validate_internal_consistency(self, gray: np.ndarray, x: int, y: int, radius: int) -> float:
        """内部一致性验证：真正的UI元素应该有一定的内部结构"""
        try:
            # 提取圆形内部区域
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.circle(mask, (x, y), radius-2, 255, -1)  # 稍小的圆避免边缘影响

            roi_pixels = gray[mask > 0]
            if len(roi_pixels) == 0:
                return 0.0

            # 计算内部特征
            mean_intensity = np.mean(roi_pixels)
            std_intensity = np.std(roi_pixels)

            consistency_score = 0.5

            # 亮度合理性
            if 30 <= mean_intensity <= 220:
                consistency_score += 0.3
            else:
                consistency_score -= 0.2

            # 内部变化合理性
            if 8 <= std_intensity <= 60:
                consistency_score += 0.3
            elif std_intensity < 3:  # 过于单调
                consistency_score -= 0.4
            elif std_intensity > 80:  # 过于噪杂
                consistency_score -= 0.2

            return max(0.0, min(1.0, consistency_score))

        except:
            return 0.0

    def _validate_context_reasonableness(self, x: int, y: int, radius: int, image_shape: Tuple) -> float:
        """上下文合理性验证：位置和大小是否符合汽车仪表盘规律"""
        try:
            height, width = image_shape[:2]

            # 位置比例
            x_ratio = x / width
            y_ratio = y / height

            context_score = 0.5

            # 位置合理性验证
            # 汽车仪表盘的元素通常分布在特定区域

            # 大型仪表 (速度表、转速表) 通常在中心区域
            if radius > 50:
                if 0.2 <= x_ratio <= 0.8 and 0.2 <= y_ratio <= 0.8:
                    context_score += 0.4
                else:
                    context_score -= 0.3

            # 中型元素 (辅助仪表) 通常在左右或上下区域
            elif 20 <= radius <= 50:
                # 允许在各个区域，但避免极边缘
                if 0.1 <= x_ratio <= 0.9 and 0.1 <= y_ratio <= 0.9:
                    context_score += 0.3
                else:
                    context_score -= 0.2

            # 小型元素 (指示灯) 可以在多个位置
            else:  # radius < 20
                # 指示灯通常不在图像最中心
                if not (0.4 <= x_ratio <= 0.6 and 0.4 <= y_ratio <= 0.6):
                    context_score += 0.2

            # 边界距离合理性
            min_distance_to_edge = min(x, y, width-x, height-y)
            if min_distance_to_edge > radius:
                context_score += 0.2
            else:
                context_score -= 0.3

            return max(0.0, min(1.0, context_score))

        except:
            return 0.0

    def _classify_dashboard_circle(self, circle: Dict, color_image: np.ndarray, gray_image: np.ndarray) -> Dict:
        """对检测到的圆形进行仪表盘语义分类"""
        try:
            center = circle['center']
            radius = circle['radius']
            x, y = center
            height, width = gray_image.shape

            # 提取圆形区域进行分析
            mask = np.zeros(gray_image.shape, dtype=np.uint8)
            cv2.circle(mask, center, radius, 255, -1)
            roi_gray = gray_image[mask > 0]

            # 基础特征
            mean_intensity = np.mean(roi_gray)
            std_intensity = np.std(roi_gray)

            # 位置特征
            x_ratio = x / width
            y_ratio = y / height

            # 初始化分类结果
            classification = {
                'semantic_type': 'unknown_circle',
                'semantic_confidence': 0.0,
                'functional_category': 'unknown',
                'size_category': self._categorize_size(radius),
                'position_category': self._categorize_position(x_ratio, y_ratio)
            }

            # 基于大小和位置的分类逻辑
            if radius > 60:  # 大型圆形
                if 0.3 <= x_ratio <= 0.7 and 0.2 <= y_ratio <= 0.8:
                    classification['semantic_type'] = 'main_gauge'
                    classification['functional_category'] = 'primary_display'
                    classification['semantic_confidence'] = 0.9
                else:
                    classification['semantic_type'] = 'secondary_gauge'
                    classification['functional_category'] = 'auxiliary_display'
                    classification['semantic_confidence'] = 0.7

            elif 25 <= radius <= 60:  # 中型圆形
                # 分析内部复杂度判断是否为仪表
                if std_intensity > 20:
                    classification['semantic_type'] = 'auxiliary_gauge'
                    classification['functional_category'] = 'information_display'
                    classification['semantic_confidence'] = 0.8
                else:
                    classification['semantic_type'] = 'control_button'
                    classification['functional_category'] = 'user_control'
                    classification['semantic_confidence'] = 0.7

            elif 12 <= radius < 25:  # 小型圆形
                # 基于亮度判断指示灯类型
                if mean_intensity > 150:
                    classification['semantic_type'] = 'active_indicator'
                    classification['functional_category'] = 'status_light'
                    classification['semantic_confidence'] = 0.8
                elif mean_intensity < 80:
                    classification['semantic_type'] = 'inactive_indicator'
                    classification['functional_category'] = 'status_light'
                    classification['semantic_confidence'] = 0.7
                else:
                    classification['semantic_type'] = 'small_button'
                    classification['functional_category'] = 'user_control'
                    classification['semantic_confidence'] = 0.6

            else:  # 很小的圆形 (radius < 12)
                classification['semantic_type'] = 'micro_indicator'
                classification['functional_category'] = 'status_dot'
                classification['semantic_confidence'] = 0.6

            return classification

        except Exception as e:
            self.logger.error(f"圆形分类失败: {e}")
            return {
                'semantic_type': 'unknown_circle',
                'semantic_confidence': 0.0,
                'functional_category': 'unknown',
                'size_category': 'unknown',
                'position_category': 'unknown'
            }

    def _categorize_size(self, radius: int) -> str:
        """尺寸分类"""
        if radius > 60:
            return 'large'
        elif radius > 25:
            return 'medium'
        elif radius > 12:
            return 'small'
        else:
            return 'micro'

    def _categorize_position(self, x_ratio: float, y_ratio: float) -> str:
        """位置分类"""
        if x_ratio < 0.33:
            if y_ratio < 0.33:
                return 'top_left'
            elif y_ratio > 0.67:
                return 'bottom_left'
            else:
                return 'center_left'
        elif x_ratio > 0.67:
            if y_ratio < 0.33:
                return 'top_right'
            elif y_ratio > 0.67:
                return 'bottom_right'
            else:
                return 'center_right'
        else:
            if y_ratio < 0.33:
                return 'top_center'
            elif y_ratio > 0.67:
                return 'bottom_center'
            else:
                return 'center'