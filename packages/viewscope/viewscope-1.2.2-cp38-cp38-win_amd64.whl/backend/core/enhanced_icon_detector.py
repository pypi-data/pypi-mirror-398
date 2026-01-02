#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强图标检测器 - 更精确的特殊符号检测
"""

import cv2
import numpy as np
import os
import sys

class EnhancedIconDetector:
    """增强图标检测器"""

    def __init__(self):
        pass

    def detect_all_icons(self, image):
        """检测所有类型的图标"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        detected_icons = []

        print(f"开始图标检测，图像尺寸: {width}x{height}")

        # 1. 在左侧区域详细分析所有可能的图标
        left_region_icons = self._analyze_left_region(gray)
        detected_icons.extend(left_region_icons)

        # 2. 在右侧区域寻找其他图标
        right_region_icons = self._analyze_right_region(gray)
        detected_icons.extend(right_region_icons)

        return detected_icons

    def _analyze_left_region(self, gray):
        """分析左侧区域的所有图标"""
        height, width = gray.shape

        # 左侧区域：宽度的前1/3，高度的前2/3
        roi_width = width // 3
        roi_height = (height * 2) // 3
        roi = gray[0:roi_height, 0:roi_width]

        print(f"分析左侧区域: {roi_width}x{roi_height}")

        icons = []

        # 详细分析这个区域
        # 1. 使用边缘检测找到所有形状
        edges = cv2.Canny(roi, 30, 100)

        # 2. 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        print(f"发现 {len(contours)} 个轮廓")

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            # 过滤太小或太大的轮廓
            if area < 50 or area > 2000:
                continue

            if w < 8 or h < 8 or w > 60 or h > 60:
                continue

            print(f"  轮廓{i+1}: 位置({x},{y}) 尺寸{w}x{h} 面积{area:.0f}")

            # 分析轮廓形状特征
            icon_type = self._analyze_contour_shape(contour, roi)

            if icon_type:
                icons.append({
                    'type': 'icon',
                    'icon_type': icon_type['type'],
                    'bounds': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'confidence': icon_type['confidence'],
                    'semantic_type': icon_type['semantic'],
                    'description': icon_type['description']
                })

        # 3. 使用模板匹配寻找闪电图标
        lightning_matches = self._template_match_lightning(roi)
        for match in lightning_matches:
            icons.append(match)

        return icons

    def _analyze_contour_shape(self, contour, roi):
        """分析轮廓形状，判断图标类型"""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        x, y, w, h = cv2.boundingRect(contour)

        if area == 0:
            return None

        # 计算形状特征
        aspect_ratio = w / h
        extent = area / (w * h)
        solidity = area / cv2.contourArea(cv2.convexHull(contour))

        # 1. 闪电图标特征检测
        if (0.3 <= aspect_ratio <= 0.8 and  # 窄高形状
            h > w and  # 高度大于宽度
            solidity < 0.85 and  # 有凹陷（不是凸形）
            extent < 0.8):  # 不填满边界框

            return {
                'type': 'lightning',
                'confidence': 0.7,
                'semantic': 'charging_indicator',
                'description': '闪电图标 (充电状态)'
            }

        # 2. 时钟图标特征检测
        elif (0.8 <= aspect_ratio <= 1.2 and  # 接近正方形
              0.6 <= solidity <= 0.95 and  # 相对规整
              150 <= area <= 800):  # 中等面积

            # 检查内部是否有类似指针的结构
            mask = np.zeros(roi.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            contour_roi = roi & mask

            # 使用霍夫线变换检测内部线条
            lines = cv2.HoughLines(contour_roi[y:y+h, x:x+w], 1, np.pi/180, threshold=max(8, min(w, h)//3))

            if lines is not None and len(lines) >= 1:
                return {
                    'type': 'clock',
                    'confidence': 0.6,
                    'semantic': 'time_indicator',
                    'description': '时钟图标'
                }

        # 3. 信号强度图标（多个小矩形组合）
        elif (aspect_ratio > 0.5 and area < 200):
            return {
                'type': 'signal_bar',
                'confidence': 0.5,
                'semantic': 'signal_indicator',
                'description': '信号指示'
            }

        return None

    def _template_match_lightning(self, roi):
        """使用模板匹配寻找闪电图标"""
        matches = []

        # 创建多个尺寸的闪电模板
        template_sizes = [(12, 18), (16, 24), (20, 30)]

        for size in template_sizes:
            template = self._create_enhanced_lightning_template(size)

            # 模板匹配
            result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)

            # 寻找匹配位置
            locations = np.where(result >= 0.4)  # 降低阈值

            for pt in zip(*locations[::-1]):
                x, y = pt
                w, h = size
                confidence = float(result[y, x])

                matches.append({
                    'type': 'icon',
                    'icon_type': 'lightning',
                    'bounds': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'confidence': confidence,
                    'semantic_type': 'charging_indicator',
                    'description': f'闪电图标 (模板匹配, 置信度:{confidence:.2f})'
                })

        return matches

    def _create_enhanced_lightning_template(self, size):
        """创建增强的闪电模板"""
        w, h = size
        template = np.zeros((h, w), dtype=np.uint8)

        # 绘制更真实的闪电形状
        points = [
            (w//4, 2),           # 顶部左
            (w//2, h//3),        # 中上
            (w*3//4, h//3),      # 中上右
            (w//3, h//2),        # 中间
            (w*2//3, h*2//3),    # 中下
            (w//2, h-2),         # 底部中
            (w//4, h*2//3),      # 中下左
            (w//2, h//2),        # 中间
        ]

        # 连接点形成闪电形状
        for i in range(len(points)-1):
            cv2.line(template, points[i], points[i+1], 255, 2)

        return template

    def _analyze_right_region(self, gray):
        """分析右侧区域"""
        # 右侧通常是状态指示区域
        height, width = gray.shape
        roi_start_x = (width * 2) // 3
        roi = gray[0:height//2, roi_start_x:]

        # 简单分析，主要寻找小图标
        icons = []

        edges = cv2.Canny(roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            # 调整坐标到原图
            x += roi_start_x

            if 50 <= area <= 500 and 8 <= w <= 30 and 8 <= h <= 30:
                icons.append({
                    'type': 'icon',
                    'icon_type': 'status_indicator',
                    'bounds': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'confidence': 0.5,
                    'semantic_type': 'status_indicator',
                    'description': '状态图标'
                })

        return icons

def test_enhanced_icon_detection():
    """测试增强图标检测"""

    print("=" * 60)
    print("增强图标检测测试")
    print("=" * 60)

    # 初始化检测器
    detector = EnhancedIconDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    if image is None:
        print("无法加载测试图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]}")

    # 执行图标检测
    icons = detector.detect_all_icons(image)

    print(f"\n检测结果: 发现 {len(icons)} 个图标")
    print("=" * 40)

    for i, icon in enumerate(icons):
        print(f"图标 {i+1}:")
        print(f"  类型: {icon['icon_type']}")
        print(f"  位置: {icon['bounds']}")
        print(f"  中心: {icon['center']}")
        print(f"  置信度: {icon['confidence']:.3f}")
        print(f"  语义: {icon.get('semantic_type', 'unknown')}")
        print(f"  描述: {icon.get('description', '未知图标')}")
        print()

    print("=" * 60)
    return icons

if __name__ == "__main__":
    test_enhanced_icon_detection()