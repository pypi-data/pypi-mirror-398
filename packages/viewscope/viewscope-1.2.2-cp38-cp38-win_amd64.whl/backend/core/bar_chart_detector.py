#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
柱状图检测器 - 专门检测柱状图形元素
"""

import cv2
import numpy as np
import os
import sys

class BarChartDetector:
    """柱状图检测器"""

    def __init__(self):
        self.min_bar_width = 5
        self.max_bar_width = 30
        self.min_bar_height = 10
        self.min_bars_in_group = 3

    def detect_bar_charts(self, image):
        """检测柱状图元素"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 获取图像尺寸
        height, width = gray.shape

        # 检测结果
        bar_charts = []

        # 1. 边缘检测
        edges = cv2.Canny(gray, 50, 150)

        # 2. 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 3. 筛选可能的柱状元素
        potential_bars = []

        for contour in contours:
            # 获取边界矩形
            x, y, w, h = cv2.boundingRect(contour)

            # 筛选条件：
            # - 宽度在合理范围内
            # - 高度 > 宽度 (垂直柱状)
            # - 面积足够大
            area = cv2.contourArea(contour)

            if (self.min_bar_width <= w <= self.max_bar_width and
                h >= self.min_bar_height and
                h > w * 0.8 and  # 高度应该大于宽度
                area > 20):

                potential_bars.append({
                    'contour': contour,
                    'bounds': (x, y, w, h),
                    'area': area,
                    'center': (x + w//2, y + h//2)
                })

        # 4. 查找柱状图组 (多个相邻的柱状元素)
        if len(potential_bars) >= self.min_bars_in_group:
            bar_groups = self._group_nearby_bars(potential_bars)

            for group in bar_groups:
                if len(group) >= self.min_bars_in_group:
                    bar_chart = self._analyze_bar_group(group)
                    if bar_chart:
                        bar_charts.append(bar_chart)

        # 5. 特殊检测：信号强度图标
        signal_bars = self._detect_signal_strength_bars(gray)
        if signal_bars:
            bar_charts.extend(signal_bars)

        # 6. 特殊检测：电池图标
        battery_bars = self._detect_battery_bars(gray)
        if battery_bars:
            bar_charts.extend(battery_bars)

        return bar_charts

    def _group_nearby_bars(self, bars, max_distance=50):
        """将相邻的柱状元素分组"""
        if not bars:
            return []

        groups = []
        used = [False] * len(bars)

        for i, bar in enumerate(bars):
            if used[i]:
                continue

            group = [bar]
            used[i] = True

            # 查找相邻的柱状元素
            for j, other_bar in enumerate(bars):
                if used[j] or i == j:
                    continue

                # 计算距离
                dist = abs(bar['center'][0] - other_bar['center'][0])
                y_diff = abs(bar['center'][1] - other_bar['center'][1])

                # 如果在同一水平线上且距离适中
                if dist <= max_distance and y_diff <= 30:
                    group.append(other_bar)
                    used[j] = True

            if len(group) >= self.min_bars_in_group:
                groups.append(group)

        return groups

    def _analyze_bar_group(self, group):
        """分析柱状图组"""
        if len(group) < self.min_bars_in_group:
            return None

        # 计算组的边界
        all_x = []
        all_y = []
        all_w = []
        all_h = []

        for bar in group:
            x, y, w, h = bar['bounds']
            all_x.append(x)
            all_y.append(y)
            all_w.append(w)
            all_h.append(h)

        # 组的总边界
        group_x1 = min(all_x)
        group_y1 = min(all_y)
        group_x2 = max([x + w for x, w in zip(all_x, all_w)])
        group_y2 = max([y + h for y, h in zip(all_y, all_h)])

        # 分析柱状图类型
        avg_width = np.mean(all_w)
        avg_height = np.mean(all_h)
        height_variance = np.var(all_h)

        # 判断图表类型
        if height_variance > 100:
            chart_type = "signal_strength"  # 高度变化大，可能是信号强度
        elif avg_height > avg_width * 2:
            chart_type = "vertical_bars"
        else:
            chart_type = "status_bars"

        return {
            'type': 'bar_chart',
            'chart_type': chart_type,
            'bounds': (group_x1, group_y1, group_x2 - group_x1, group_y2 - group_y1),
            'center': ((group_x1 + group_x2) // 2, (group_y1 + group_y2) // 2),
            'bar_count': len(group),
            'bars': group,
            'confidence': min(0.8, 0.5 + len(group) * 0.1)
        }

    def _detect_signal_strength_bars(self, gray):
        """专门检测信号强度柱状图标"""
        height, width = gray.shape

        # 在图像左上角区域查找
        roi_height = height // 3
        roi_width = width // 4
        roi = gray[0:roi_height, 0:roi_width]

        # 二值化
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 查找类似信号强度的模式
        signal_bars = []
        potential_signal_rects = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # 信号强度柱的特征：小矩形，高度递增
            if (3 <= w <= 15 and 5 <= h <= 25 and
                x < roi_width // 2):  # 在左侧区域
                potential_signal_rects.append((x, y, w, h))

        # 如果找到3个或以上的小矩形，可能是信号强度图标
        if len(potential_signal_rects) >= 3:
            # 按x坐标排序
            potential_signal_rects.sort(key=lambda rect: rect[0])

            # 检查是否呈递增高度模式
            heights = [rect[3] for rect in potential_signal_rects[:4]]  # 取前4个
            if len(heights) >= 3 and self._is_increasing_pattern(heights):
                # 计算总边界
                min_x = min([rect[0] for rect in potential_signal_rects])
                min_y = min([rect[1] for rect in potential_signal_rects])
                max_x = max([rect[0] + rect[2] for rect in potential_signal_rects])
                max_y = max([rect[1] + rect[3] for rect in potential_signal_rects])

                signal_bars.append({
                    'type': 'bar_chart',
                    'chart_type': 'signal_strength',
                    'bounds': (min_x, min_y, max_x - min_x, max_y - min_y),
                    'center': ((min_x + max_x) // 2, (min_y + max_y) // 2),
                    'bar_count': len(potential_signal_rects),
                    'confidence': 0.85,
                    'semantic_type': 'signal_indicator'
                })

        return signal_bars

    def _detect_battery_bars(self, gray):
        """检测电池柱状图标"""
        height, width = gray.shape

        # 在图像左上角区域查找
        roi_height = height // 3
        roi_width = width // 4
        roi = gray[0:roi_height, 0:roi_width]

        # 查找类似电池的形状
        battery_bars = []

        # 使用模板匹配或轮廓分析
        # 这里简化处理，查找竖直的小矩形组合
        _, binary = cv2.threshold(roi, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # 电池图标特征：较宽的矩形，可能有内部结构
            if (15 <= w <= 40 and 20 <= h <= 50):
                # 分析内部是否有柱状结构
                battery_roi = binary[y:y+h, x:x+w]

                # 检测内部垂直线条
                vertical_lines = self._detect_vertical_lines_in_roi(battery_roi)

                if len(vertical_lines) >= 2:  # 至少2条垂直线，可能是电池
                    battery_bars.append({
                        'type': 'bar_chart',
                        'chart_type': 'battery_level',
                        'bounds': (x, y, w, h),
                        'center': (x + w//2, y + h//2),
                        'bar_count': len(vertical_lines),
                        'confidence': 0.75,
                        'semantic_type': 'battery_indicator'
                    })

        return battery_bars

    def _is_increasing_pattern(self, heights):
        """检查高度是否呈递增模式"""
        if len(heights) < 3:
            return False

        # 允许一定的误差
        tolerance = 2

        for i in range(1, len(heights)):
            if heights[i] < heights[i-1] - tolerance:
                return False

        # 至少有一定的高度差异
        return (heights[-1] - heights[0]) >= 5

    def _detect_vertical_lines_in_roi(self, roi):
        """在ROI中检测垂直线条"""
        if roi.shape[0] < 5 or roi.shape[1] < 5:
            return []

        # 使用垂直形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        vertical = cv2.morphologyEx(roi, cv2.MORPH_OPEN, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        vertical_lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > w and h >= 5:  # 高度大于宽度，且足够高
                vertical_lines.append((x, y, w, h))

        return vertical_lines

def test_bar_chart_detection():
    """测试柱状图检测"""

    print("=" * 50)
    print("柱状图检测测试")
    print("=" * 50)

    # 添加当前目录到路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from comprehensive_detector import ComprehensiveDetector

    # 初始化检测器
    detector = ComprehensiveDetector()
    bar_detector = BarChartDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    # 执行检测
    result = detector.comprehensive_detection(image)

    # 检测柱状图
    bar_charts = bar_detector.detect_bar_charts(image)

    print(f"检测到 {len(bar_charts)} 个柱状图元素:")

    for i, chart in enumerate(bar_charts):
        print(f"  {i+1}. 类型: {chart['chart_type']}")
        print(f"      位置: {chart['bounds']}")
        print(f"      柱数: {chart['bar_count']}")
        print(f"      置信度: {chart['confidence']:.3f}")
        print(f"      语义: {chart.get('semantic_type', 'unknown')}")

    return bar_charts

if __name__ == "__main__":
    test_bar_chart_detection()