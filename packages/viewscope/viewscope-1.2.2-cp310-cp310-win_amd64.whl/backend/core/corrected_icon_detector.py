#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正的图标检测器 - 解决冲突和分类错误
"""

import cv2
import numpy as np
import os
import sys

class CorrectedIconDetector:
    """修正的图标检测器 - 精确识别闪电图标"""

    def __init__(self):
        pass

    def detect_corrected_icons(self, image):
        """检测修正的图标 - 重点识别闪电图标"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        detected_icons = []

        print(f"开始修正图标检测，图像尺寸: {width}x{height}")

        # 专门在左侧区域寻找闪电图标（充电标识）
        lightning_icons = self._detect_lightning_charging_icons(gray)
        detected_icons.extend(lightning_icons)

        # 检测其他真正的图标
        other_icons = self._detect_other_specific_icons(gray)
        detected_icons.extend(other_icons)

        return detected_icons

    def _detect_lightning_charging_icons(self, gray):
        """专门检测闪电充电图标"""
        height, width = gray.shape

        # 在左侧中间区域重点搜索
        roi_width = width // 4
        roi_height = height // 2
        roi_start_y = height // 4
        roi = gray[roi_start_y:roi_start_y+roi_height, 0:roi_width]

        print(f"专门搜索闪电图标区域: {roi_width}x{roi_height} 起始Y:{roi_start_y}")

        lightning_icons = []

        # 使用更精确的闪电检测
        edges = cv2.Canny(roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        print(f"发现 {len(contours)} 个轮廓用于闪电检测")

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            # 调整坐标到原图
            original_y = y + roi_start_y

            # 闪电图标的特征：
            # 1. 窄高形状 (高度大于宽度)
            # 2. 中等面积
            # 3. 有不规则边缘（闪电形状）
            if (8 <= w <= 25 and 15 <= h <= 35 and  # 合适的尺寸
                h > w * 1.2 and  # 明显的窄高形状
                80 <= area <= 400):  # 合适的面积

                # 检查形状复杂度
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    complexity = perimeter**2 / area

                    # 闪电形状应该有较高的复杂度（锯齿状边缘）
                    if complexity > 15:  # 复杂的边缘形状

                        # 检查凹凸性（闪电不是凸形）
                        hull = cv2.convexHull(contour)
                        hull_area = cv2.contourArea(hull)
                        solidity = area / hull_area if hull_area > 0 else 0

                        # 闪电形状应该有凹陷（solidity < 1）
                        if solidity < 0.9:

                            # 位置验证：在左侧中间位置
                            if x < roi_width // 2:  # 在ROI的左半部分

                                confidence = min(0.9, 0.6 + (0.9 - solidity) + (complexity - 15) / 20)

                                lightning_icons.append({
                                    'type': 'icon',
                                    'icon_type': 'lightning',
                                    'bounds': (x, original_y, w, h),
                                    'center': (x + w//2, original_y + h//2),
                                    'confidence': confidence,
                                    'semantic_type': 'charging_indicator',
                                    'description': '闪电图标 (充电标识)',
                                    'detection_method': 'shape_analysis',
                                    'area': area,
                                    'complexity': complexity,
                                    'solidity': solidity
                                })

                                print(f"发现闪电图标候选: 位置({x},{original_y}) 尺寸{w}x{h} 面积{area} 复杂度{complexity:.1f} 凹凸性{solidity:.2f}")

        # 使用模板匹配作为补充
        template_matches = self._template_match_lightning_charging(roi, roi_start_y)
        lightning_icons.extend(template_matches)

        # 移除重复检测
        lightning_icons = self._remove_duplicate_detections(lightning_icons)

        return lightning_icons

    def _template_match_lightning_charging(self, roi, roi_start_y):
        """使用模板匹配检测闪电充电图标"""
        matches = []

        # 创建闪电形状模板
        template = self._create_lightning_charging_template((16, 24))

        # 模板匹配
        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.3)  # 适当的阈值

        for pt in zip(*locations[::-1]):
            x, y = pt
            w, h = 16, 24
            confidence = float(result[y, x])
            original_y = y + roi_start_y

            matches.append({
                'type': 'icon',
                'icon_type': 'lightning',
                'bounds': (x, original_y, w, h),
                'center': (x + w//2, original_y + h//2),
                'confidence': confidence,
                'semantic_type': 'charging_indicator',
                'description': f'闪电图标 (充电标识, 模板匹配)',
                'detection_method': 'template_matching'
            })

        return matches

    def _create_lightning_charging_template(self, size):
        """创建闪电充电图标模板"""
        w, h = size
        template = np.zeros((h, w), dtype=np.uint8)

        # 绘制更准确的闪电形状
        # 上半部分：从左上角到右中间
        points1 = [(2, 2), (w-3, h//2-1)]
        cv2.line(template, points1[0], points1[1], 255, 2)

        # 中间横线（闪电的特征）
        points2 = [(w//3, h//2-3), (w//2+2, h//2-3)]
        cv2.line(template, points2[0], points2[1], 255, 2)

        # 下半部分：从左中间到右下角
        points3 = [(w//3, h//2+1), (w-2, h-2)]
        cv2.line(template, points3[0], points3[1], 255, 2)

        return template

    def _detect_other_specific_icons(self, gray):
        """检测其他特定图标"""
        other_icons = []

        height, width = gray.shape

        # 在右上角寻找小图标（但避开OCR区域）
        roi_right = gray[0:height//3, width*2//3:]
        roi_start_x = width*2//3

        edges = cv2.Canny(roi_right, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            # 调整坐标
            original_x = x + roi_start_x

            # 小图标特征
            if (8 <= w <= 20 and 8 <= h <= 20 and 50 <= area <= 300):

                # 简单形状分析
                aspect_ratio = w / h

                if 0.7 <= aspect_ratio <= 1.3:  # 接近正方形的小图标
                    other_icons.append({
                        'type': 'icon',
                        'icon_type': 'small_status',
                        'bounds': (original_x, y, w, h),
                        'center': (original_x + w//2, y + h//2),
                        'confidence': 0.6,
                        'semantic_type': 'status_indicator',
                        'description': '小状态图标'
                    })

        return other_icons

    def _remove_duplicate_detections(self, detections):
        """移除重复检测"""
        if len(detections) <= 1:
            return detections

        # 按置信度排序
        sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)

        filtered = []
        for detection in sorted_detections:
            # 检查是否与已有检测重叠
            is_duplicate = False
            for existing in filtered:
                if self._calculate_overlap(detection['bounds'], existing['bounds']) > 0.5:
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(detection)

        return filtered

    def _calculate_overlap(self, bounds1, bounds2):
        """计算重叠比例"""
        x1_1, y1_1, w1, h1 = bounds1
        x1_2, y1_2, w2, h2 = bounds2

        x2_1, y2_1 = x1_1 + w1, y1_1 + h1
        x2_2, y2_2 = x1_2 + w2, y1_2 + h2

        # 计算重叠区域
        overlap_x1 = max(x1_1, x1_2)
        overlap_y1 = max(y1_1, y1_2)
        overlap_x2 = min(x2_1, x2_2)
        overlap_y2 = min(y2_1, y2_2)

        if overlap_x2 <= overlap_x1 or overlap_y2 <= overlap_y1:
            return 0.0

        overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
        area1 = w1 * h1
        area2 = w2 * h2
        smaller_area = min(area1, area2)

        return overlap_area / smaller_area if smaller_area > 0 else 0.0

def test_corrected_icon_detection():
    """测试修正的图标检测"""

    print("=" * 60)
    print("修正图标检测测试")
    print("=" * 60)

    # 初始化检测器
    detector = CorrectedIconDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    if image is None:
        print("无法加载测试图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]}")

    # 执行修正的图标检测
    icons = detector.detect_corrected_icons(image)

    print(f"\n修正后检测结果: 发现 {len(icons)} 个图标")
    print("=" * 40)

    for i, icon in enumerate(icons):
        print(f"图标 {i+1}:")
        print(f"  类型: {icon['icon_type']}")
        print(f"  位置: {icon['bounds']}")
        print(f"  中心: {icon['center']}")
        print(f"  置信度: {icon['confidence']:.3f}")
        print(f"  语义: {icon.get('semantic_type', 'unknown')}")
        print(f"  描述: {icon.get('description', '未知图标')}")
        print(f"  检测方法: {icon.get('detection_method', 'unknown')}")

        if 'area' in icon:
            print(f"  面积: {icon['area']}")
        if 'complexity' in icon:
            print(f"  复杂度: {icon['complexity']:.1f}")
        if 'solidity' in icon:
            print(f"  凹凸性: {icon['solidity']:.2f}")
        print()

    print("=" * 60)
    return icons

if __name__ == "__main__":
    test_corrected_icon_detection()