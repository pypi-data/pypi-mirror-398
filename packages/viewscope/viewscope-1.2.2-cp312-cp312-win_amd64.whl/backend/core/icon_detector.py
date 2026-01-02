#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标检测器 - 专门检测特殊符号图标
"""

import cv2
import numpy as np
import os
import sys

class IconDetector:
    """图标检测器 - 识别闪电、信号、电池等图标"""

    def __init__(self):
        pass

    def detect_icons(self, image):
        """检测各种图标"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        detected_icons = []

        # 1. 检测闪电图标
        lightning_icons = self._detect_lightning_icons(gray)
        detected_icons.extend(lightning_icons)

        # 2. 检测信号图标
        signal_icons = self._detect_signal_icons(gray)
        detected_icons.extend(signal_icons)

        # 3. 检测时钟图标
        clock_icons = self._detect_clock_icons(gray)
        detected_icons.extend(clock_icons)

        return detected_icons

    def _detect_lightning_icons(self, gray):
        """检测闪电图标（充电状态）"""
        lightning_icons = []

        height, width = gray.shape

        # 在左侧区域查找闪电图标
        roi_height = height // 2
        roi_width = width // 4
        roi = gray[0:roi_height, 0:roi_width]

        # 使用多种方法检测闪电形状

        # 方法1: 基于轮廓的闪电检测
        lightning_contours = self._detect_lightning_by_contours(roi)

        # 方法2: 基于模板匹配（简化的闪电模板）
        lightning_templates = self._detect_lightning_by_template(roi)

        # 合并结果
        all_candidates = lightning_contours + lightning_templates

        for candidate in all_candidates:
            x, y, w, h = candidate['bounds']

            lightning_icons.append({
                'type': 'icon',
                'icon_type': 'lightning',
                'bounds': (x, y, w, h),
                'center': (x + w//2, y + h//2),
                'confidence': candidate.get('confidence', 0.7),
                'semantic_type': 'charging_indicator',
                'description': '闪电图标 (充电状态)'
            })

        return lightning_icons

    def _detect_lightning_by_contours(self, roi):
        """基于轮廓检测闪电形状"""
        candidates = []

        # 二值化
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # 获取轮廓特征
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            # 闪电图标的特征筛选
            if (10 <= w <= 30 and 15 <= h <= 40 and  # 合适的尺寸
                100 <= area <= 800 and  # 合适的面积
                h > w):  # 高度大于宽度（竖直形状）

                # 计算轮廓的复杂度（闪电应该有锯齿形状）
                perimeter = cv2.arcLength(contour, True)
                complexity = perimeter / area if area > 0 else 0

                # 闪电形状通常有较高的周长面积比
                if 0.2 <= complexity <= 0.8:
                    # 检查形状是否类似闪电（有向内的凹陷）
                    hull = cv2.convexHull(contour)
                    hull_area = cv2.contourArea(hull)
                    solidity = area / hull_area if hull_area > 0 else 0

                    # 闪电的solidity通常较小（因为有凹陷）
                    if solidity < 0.85:
                        candidates.append({
                            'bounds': (x, y, w, h),
                            'confidence': min(0.8, 0.3 + (0.85 - solidity)),
                            'method': 'contour_analysis'
                        })

        return candidates

    def _detect_lightning_by_template(self, roi):
        """基于模板匹配检测闪电"""
        candidates = []

        # 创建简化的闪电模板
        template_size = (16, 24)  # 宽x高
        lightning_template = self._create_lightning_template(template_size)

        # 模板匹配
        result = cv2.matchTemplate(roi, lightning_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.5)  # 降低阈值

        for pt in zip(*locations[::-1]):  # 转换坐标
            x, y = pt
            w, h = template_size
            confidence = result[y, x]

            candidates.append({
                'bounds': (x, y, w, h),
                'confidence': float(confidence),
                'method': 'template_matching'
            })

        return candidates

    def _create_lightning_template(self, size):
        """创建闪电图标模板"""
        w, h = size
        template = np.zeros((h, w), dtype=np.uint8)

        # 画一个简化的闪电形状
        # 上半部分：从左上到右中
        cv2.line(template, (2, 2), (w-4, h//2-2), 255, 2)
        # 下半部分：从左中到右下
        cv2.line(template, (4, h//2+2), (w-2, h-2), 255, 2)
        # 中间的连接部分
        cv2.line(template, (w//2-2, h//2-4), (w//2+2, h//2+4), 255, 2)

        return template

    def _detect_signal_icons(self, gray):
        """检测信号强度图标"""
        signal_icons = []

        height, width = gray.shape
        roi_height = height // 3
        roi_width = width // 4
        roi = gray[0:roi_height, 0:roi_width]

        # 查找信号强度的特征模式（递增的竖线）
        # 这里可以扩展更复杂的信号图标检测逻辑

        return signal_icons

    def _detect_clock_icons(self, gray):
        """检测时钟图标"""
        clock_icons = []

        height, width = gray.shape
        roi_height = height // 2
        roi_width = width // 4
        roi = gray[0:roi_height, 0:roi_width]

        # 二值化
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            # 时钟图标特征：接近正方形，中等尺寸
            if (15 <= w <= 35 and 15 <= h <= 35 and  # 合适尺寸
                0.8 <= w/h <= 1.2 and  # 接近正方形
                200 <= area <= 1000):  # 合适面积

                # 检查是否有类似时钟指针的线条
                mask = np.zeros(binary.shape, dtype=np.uint8)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                roi_clock = binary & mask

                # 简单的线条检测（时钟指针）
                lines = cv2.HoughLines(roi_clock[y:y+h, x:x+w], 1, np.pi/180, threshold=10)

                if lines is not None and len(lines) >= 2:  # 至少有两条线（时钟指针）
                    clock_icons.append({
                        'type': 'icon',
                        'icon_type': 'clock',
                        'bounds': (x, y, w, h),
                        'center': (x + w//2, y + h//2),
                        'confidence': 0.6,
                        'semantic_type': 'time_indicator',
                        'description': '时钟图标'
                    })

        return clock_icons

def test_icon_detection():
    """测试图标检测"""

    print("=" * 50)
    print("图标检测测试")
    print("=" * 50)

    # 初始化图标检测器
    icon_detector = IconDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    if image is None:
        print("无法加载测试图像")
        return

    # 执行图标检测
    icons = icon_detector.detect_icons(image)

    print(f"检测到 {len(icons)} 个图标:")

    for i, icon in enumerate(icons):
        print(f"  {i+1}. 类型: {icon['icon_type']}")
        print(f"      位置: {icon['bounds']}")
        print(f"      置信度: {icon['confidence']:.3f}")
        print(f"      语义: {icon.get('semantic_type', 'unknown')}")
        print(f"      描述: {icon.get('description', '未知图标')}")
        print()

    return icons

if __name__ == "__main__":
    test_icon_detection()