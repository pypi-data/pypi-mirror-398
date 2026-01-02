#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shape Discriminator - 彻底区分闪电图标和垂直柱图标
核心思路：闪电是锯齿状，垂直柱是矩形条状
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional

class ShapeDiscriminator:
    """形状判别器 - 区分闪电图标和垂直柱状图标"""

    def __init__(self):
        # 闪电图标特征阈值
        self.lightning_min_direction_changes = 2  # 闪电至少2次方向变化
        self.lightning_max_rectangularity = 0.7   # 闪电矩形度要低
        self.lightning_min_complexity = 15        # 闪电复杂度要高

        # 垂直柱特征阈值
        self.bar_min_rectangularity = 0.8         # 垂直柱矩形度要高
        self.bar_max_direction_changes = 1        # 垂直柱方向变化要少
        self.bar_min_aspect_ratio = 2.0           # 垂直柱高宽比要大

    def analyze_shape_features(self, contour: np.ndarray, roi: np.ndarray = None) -> Dict:
        """分析轮廓的形状特征"""

        # 基本几何特征
        area = cv2.contourArea(contour)
        if area < 10:
            return {'type': 'invalid', 'confidence': 0.0}

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = h / w if w > 0 else 0

        # 计算矩形度（轮廓面积/边界矩形面积）
        rectangularity = area / (w * h) if (w * h) > 0 else 0

        # 计算周长复杂度
        perimeter = cv2.arcLength(contour, True)
        complexity = (perimeter ** 2) / area if area > 0 else 0

        # 分析方向变化（检测锯齿模式）
        direction_changes = self._count_direction_changes(contour)

        # 分析形状凸性
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        # 分析边缘密度（垂直柱边缘简单，闪电边缘复杂）
        edge_complexity = self._analyze_edge_complexity(contour, roi)

        return {
            'area': area,
            'aspect_ratio': aspect_ratio,
            'rectangularity': rectangularity,
            'complexity': complexity,
            'direction_changes': direction_changes,
            'solidity': solidity,
            'edge_complexity': edge_complexity,
            'bounds': (x, y, w, h)
        }

    def _count_direction_changes(self, contour: np.ndarray) -> int:
        """计算轮廓的方向变化次数（闪电特征）"""
        if len(contour) < 4:
            return 0

        # 简化轮廓
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) < 3:
            return 0

        direction_changes = 0
        for i in range(1, len(approx) - 1):
            p1 = approx[i-1][0]
            p2 = approx[i][0]
            p3 = approx[i+1][0]

            # 计算向量方向
            v1 = (p2[0] - p1[0], p2[1] - p1[1])
            v2 = (p3[0] - p2[0], p3[1] - p2[1])

            # 计算角度变化
            if v1[0] != 0 and v2[0] != 0:
                if (v1[0] * v2[0]) < 0:  # X方向改变
                    direction_changes += 1

        return direction_changes

    def _analyze_edge_complexity(self, contour: np.ndarray, roi: np.ndarray = None) -> float:
        """分析边缘复杂度"""
        if roi is None:
            return 0.0

        # 创建轮廓掩码
        mask = np.zeros(roi.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)

        # 计算边缘
        edges = cv2.Canny(roi, 50, 150)

        # 计算轮廓区域内的边缘密度
        masked_edges = cv2.bitwise_and(edges, mask)
        edge_pixels = np.sum(masked_edges > 0)
        total_pixels = np.sum(mask > 0)

        return edge_pixels / total_pixels if total_pixels > 0 else 0.0

    def classify_shape(self, features: Dict) -> Dict:
        """基于特征分类形状为闪电或垂直柱"""

        lightning_score = 0.0
        bar_score = 0.0

        # 特征1: 方向变化（闪电多变化，垂直柱少变化）
        direction_changes = features.get('direction_changes', 0)
        if direction_changes >= self.lightning_min_direction_changes:
            lightning_score += 0.3
        if direction_changes <= self.bar_max_direction_changes:
            bar_score += 0.3

        # 特征2: 矩形度（垂直柱高矩形度，闪电低矩形度）
        rectangularity = features.get('rectangularity', 0)
        if rectangularity <= self.lightning_max_rectangularity:
            lightning_score += 0.25
        if rectangularity >= self.bar_min_rectangularity:
            bar_score += 0.25

        # 特征3: 复杂度（闪电复杂，垂直柱简单）
        complexity = features.get('complexity', 0)
        if complexity >= self.lightning_min_complexity:
            lightning_score += 0.2
        if complexity < self.lightning_min_complexity:
            bar_score += 0.2

        # 特征4: 高宽比（垂直柱很高，闪电适中）
        aspect_ratio = features.get('aspect_ratio', 0)
        if aspect_ratio >= self.bar_min_aspect_ratio:
            bar_score += 0.15
        if 1.2 <= aspect_ratio <= 2.5:  # 闪电合理高宽比
            lightning_score += 0.15

        # 特征5: 边缘复杂度（闪电边缘复杂，垂直柱边缘简单）
        edge_complexity = features.get('edge_complexity', 0)
        if edge_complexity > 0.3:
            lightning_score += 0.1
        if edge_complexity <= 0.2:
            bar_score += 0.1

        # 确定分类结果
        if lightning_score > bar_score and lightning_score > 0.6:
            return {
                'type': 'lightning',
                'confidence': lightning_score,
                'reason': f"Lightning features: changes={direction_changes}, rect={rectangularity:.2f}, complex={complexity:.1f}"
            }
        elif bar_score > lightning_score and bar_score > 0.6:
            return {
                'type': 'vertical_bar',
                'confidence': bar_score,
                'reason': f"Bar features: rect={rectangularity:.2f}, aspect={aspect_ratio:.2f}, changes={direction_changes}"
            }
        else:
            return {
                'type': 'ambiguous',
                'confidence': max(lightning_score, bar_score),
                'reason': f"Unclear: lightning={lightning_score:.2f}, bar={bar_score:.2f}"
            }

    def filter_lightning_candidates(self, candidates: List[Dict], image: np.ndarray) -> List[Dict]:
        """过滤候选者，只保留真正的闪电图标"""

        filtered_candidates = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        for candidate in candidates:
            x, y, w, h = candidate['bounds']

            # 提取候选区域
            roi = gray[y:y+h, x:x+w]
            if roi.size == 0:
                continue

            # 找到轮廓
            edges = cv2.Canny(roi, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                continue

            # 分析最大轮廓
            main_contour = max(contours, key=cv2.contourArea)
            features = self.analyze_shape_features(main_contour, roi)
            classification = self.classify_shape(features)

            print(f"Candidate at ({x},{y}): {classification['type']} (conf={classification['confidence']:.2f}) - {classification['reason']}")

            # 只保留被分类为闪电的候选者
            if classification['type'] == 'lightning':
                candidate['shape_classification'] = classification
                candidate['shape_features'] = features
                filtered_candidates.append(candidate)
            elif classification['type'] == 'vertical_bar':
                print(f"  EXCLUDED: Identified as vertical bar (signal strength)")
            else:
                print(f"  EXCLUDED: Ambiguous classification")

        return filtered_candidates

def test_shape_discriminator():
    """测试形状判别器"""
    print("=" * 60)
    print("SHAPE DISCRIMINATOR TEST")
    print("=" * 60)

    discriminator = ShapeDiscriminator()

    # 加载测试图像
    test_image = "../../resources/20250910-100334.png"
    if not os.path.exists(test_image):
        print(f"Test image not found: {test_image}")
        return

    image = cv2.imread(test_image)
    if image is None:
        print("Failed to load image")
        return

    print(f"Image size: {image.shape[1]}x{image.shape[0]} pixels")

    # 模拟一些候选者（包括闪电和垂直柱）
    mock_candidates = [
        {'bounds': (80, 165, 10, 15)},   # 真实闪电图标区域
        {'bounds': (65, 130, 8, 25)},    # 可能的垂直柱区域
        {'bounds': (75, 135, 6, 20)},    # 另一个垂直柱
    ]

    # 测试形状判别
    filtered = discriminator.filter_lightning_candidates(mock_candidates, image)

    print(f"\\nRESULTS:")
    print(f"Original candidates: {len(mock_candidates)}")
    print(f"Filtered lightning icons: {len(filtered)}")

    for icon in filtered:
        classification = icon['shape_classification']
        print(f"  Lightning icon: bounds={icon['bounds']}, confidence={classification['confidence']:.2f}")

    return filtered

if __name__ == "__main__":
    import os
    test_shape_discriminator()