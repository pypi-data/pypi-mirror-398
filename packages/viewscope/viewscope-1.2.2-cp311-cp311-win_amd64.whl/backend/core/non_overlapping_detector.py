#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非重叠检测器 - 确保OCR和图形检测不重叠
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector
from bar_chart_detector import BarChartDetector

class NonOverlappingDetector:
    """非重叠检测器 - 处理检测结果冲突"""

    def __init__(self):
        pass

    def calculate_overlap_ratio(self, bounds1, bounds2):
        """计算两个边界框的重叠比例"""
        x1_1, y1_1, w1, h1 = bounds1 if len(bounds1) == 4 else (*bounds1[:2], bounds1[2]-bounds1[0], bounds1[3]-bounds1[1])
        x1_2, y1_2, w2, h2 = bounds2 if len(bounds2) == 4 else (*bounds2[:2], bounds2[2]-bounds2[0], bounds2[3]-bounds2[1])

        x2_1, y2_1 = x1_1 + w1, y1_1 + h1
        x2_2, y2_2 = x1_2 + w2, y1_2 + h2

        # 计算重叠区域
        overlap_x1 = max(x1_1, x1_2)
        overlap_y1 = max(y1_1, y1_2)
        overlap_x2 = min(x2_1, x2_2)
        overlap_y2 = min(y2_1, y2_2)

        if overlap_x2 <= overlap_x1 or overlap_y2 <= overlap_y1:
            return 0.0

        # 重叠面积
        overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)

        # 总面积
        area1 = w1 * h1
        area2 = w2 * h2

        # 返回重叠比例 (相对于较小区域)
        smaller_area = min(area1, area2)
        return overlap_area / smaller_area if smaller_area > 0 else 0.0

    def filter_conflicting_detections(self, text_regions, bar_charts, circles, overlap_threshold=0.3):
        """过滤冲突的检测结果 - OCR优先"""

        print(f"冲突检测过滤: OCR={len(text_regions)}, 柱状图={len(bar_charts)}, 圆形={len(circles)}")

        # 1. OCR区域优先，过滤与OCR重叠的柱状图
        filtered_bar_charts = []

        for bar_chart in bar_charts:
            bar_bounds = bar_chart['bounds']
            conflicts_with_text = False

            for text_region in text_regions:
                text_bounds = text_region['bounds']
                overlap_ratio = self.calculate_overlap_ratio(bar_bounds, text_bounds)

                if overlap_ratio > overlap_threshold:
                    conflicts_with_text = True
                    print(f"  过滤柱状图 {bar_chart['chart_type']}: 与文字 '{text_region['text']}' 重叠 {overlap_ratio:.2f}")
                    break

            if not conflicts_with_text:
                filtered_bar_charts.append(bar_chart)

        # 2. 过滤与OCR重叠的圆形检测
        filtered_circles = []

        for circle in circles:
            # 将圆形转换为边界框进行重叠检测
            center = circle['center']
            radius = circle['radius']
            circle_bounds = (center[0] - radius, center[1] - radius, 2 * radius, 2 * radius)

            conflicts_with_text = False

            for text_region in text_regions:
                text_bounds = text_region['bounds']
                overlap_ratio = self.calculate_overlap_ratio(circle_bounds, text_bounds)

                if overlap_ratio > overlap_threshold:
                    conflicts_with_text = True
                    print(f"  过滤圆形: 与文字 '{text_region['text']}' 重叠 {overlap_ratio:.2f}")
                    break

            if not conflicts_with_text:
                filtered_circles.append(circle)

        # 3. 过滤柱状图之间的重叠 (保留置信度高的)
        final_bar_charts = []
        used_bars = [False] * len(filtered_bar_charts)

        for i, bar1 in enumerate(filtered_bar_charts):
            if used_bars[i]:
                continue

            best_bar = bar1
            used_bars[i] = True

            for j, bar2 in enumerate(filtered_bar_charts):
                if used_bars[j] or i == j:
                    continue

                overlap_ratio = self.calculate_overlap_ratio(bar1['bounds'], bar2['bounds'])

                if overlap_ratio > overlap_threshold:
                    # 保留置信度更高的
                    if bar2['confidence'] > best_bar['confidence']:
                        best_bar = bar2
                    used_bars[j] = True

            final_bar_charts.append(best_bar)

        print(f"过滤结果: OCR={len(text_regions)} (不变), 柱状图={len(bar_charts)}->{len(final_bar_charts)}, 圆形={len(circles)}->{len(filtered_circles)}")

        return text_regions, final_bar_charts, filtered_circles

class CleanVisualizationRenderer:
    """清洁可视化渲染器"""

    def __init__(self):
        self.font = self._load_chinese_font()
        self.colors = self._define_color_scheme()

    def _load_chinese_font(self):
        """加载中文字体"""
        try:
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, 16)
                    except:
                        continue

            return ImageFont.load_default()
        except:
            return ImageFont.load_default()

    def _define_color_scheme(self):
        """定义颜色方案"""
        return {
            # 圆形检测颜色
            'circle_auxiliary': (255, 0, 255),     # 紫色 - 辅助仪表
            'circle_indicator': (128, 128, 128),   # 灰色 - 状态指示器

            # 文字检测颜色
            'text_chinese': (0, 255, 128),         # 绿色 - 中文
            'text_english': (255, 255, 0),         # 黄色 - 英文
            'text_numeric': (255, 128, 255),       # 粉色 - 数字
            'text_mixed': (0, 255, 255),           # 青色 - 混合

            # 柱状图检测颜色
            'bar_signal': (255, 165, 0),           # 橙色 - 信号强度
            'bar_battery': (0, 128, 255),          # 蓝色 - 电池指示
            'bar_status': (128, 0, 255),           # 紫红色 - 状态柱
            'bar_vertical': (255, 20, 147),        # 深粉色 - 垂直柱

            # 特征点颜色
            'sift_point': (0, 255, 0),             # 绿色 - SIFT
            'orb_point': (0, 0, 255),              # 红色 - ORB
        }

    def draw_chinese_text(self, image, text, position, color, font_size=16):
        """在图像上绘制中文文字"""
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)

            if font_size != 16:
                try:
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                    else:
                        font = self.font
                except:
                    font = self.font
            else:
                font = self.font

            draw.text(position, text, font=font, fill=color)
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except:
            return image

    def get_language_info(self, language):
        """获取语言信息和对应颜色"""
        language_map = {
            'chinese': ('中文', self.colors['text_chinese']),
            'english': ('英文', self.colors['text_english']),
            'numeric': ('数字', self.colors['text_numeric']),
            'mixed': ('混合', self.colors['text_mixed']),
        }
        return language_map.get(language, ('未知', (255, 255, 255)))

    def get_bar_chart_info(self, chart_type):
        """获取柱状图信息和对应颜色"""
        chart_map = {
            'signal_strength': ('信号强度', self.colors['bar_signal']),
            'battery_level': ('电池电量', self.colors['bar_battery']),
            'status_bars': ('状态柱', self.colors['bar_status']),
            'vertical_bars': ('垂直柱', self.colors['bar_vertical'])
        }
        return chart_map.get(chart_type, ('柱状图', self.colors['bar_status']))

    def improve_ocr_result(self, text_regions):
        """改进OCR结果"""
        improved_regions = []

        for region in text_regions:
            content = region['text']
            corrected_content = content

            # 修复OCR错误
            if "一.KWh" in content or "一.kWh" in content:
                corrected_content = content.replace("一.KWh", "--.-kWh").replace("一.kWh", "--.-kWh")

            if "1oO" in content:
                corrected_content = corrected_content.replace("1oO", "100")
            elif "loO" in content:
                corrected_content = corrected_content.replace("loO", "100")
            elif "loo" in content:
                corrected_content = corrected_content.replace("loo", "100")

            if "--.-kWh/" in corrected_content and "km" in corrected_content:
                if not corrected_content.endswith("100km"):
                    corrected_content = "--.-kWh/100km"

            improved_region = region.copy()
            improved_region['text'] = corrected_content
            improved_region['original_text'] = content

            improved_regions.append(improved_region)

        return improved_regions

def create_non_overlapping_visualization():
    """创建非重叠的最终综合检测标记展示"""

    print("=" * 60)
    print("非重叠的最终综合检测标记展示")
    print("=" * 60)

    # 初始化检测器
    detector = ComprehensiveDetector()
    bar_detector = BarChartDetector()
    conflict_resolver = NonOverlappingDetector()
    renderer = CleanVisualizationRenderer()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image):
        print(f"测试图像不存在: {test_image}")
        return

    image = cv2.imread(test_image)
    if image is None:
        print("无法加载图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]} 像素")

    # 执行基础检测
    print("\n执行基础检测...")
    result = detector.comprehensive_detection(image)

    if not result['success']:
        print(f"检测失败: {result.get('error', '未知错误')}")
        return

    # 执行柱状图检测
    print("执行柱状图检测...")
    bar_charts = bar_detector.detect_bar_charts(image)

    # 提取检测结果
    circles = result['elements']['circles']
    text_regions = result['elements']['text_regions']
    features = result['features']

    print(f"原始检测结果: 圆形={len(circles)}, 文字={len(text_regions)}, 柱状图={len(bar_charts)}")

    # 改进OCR结果
    improved_text_regions = renderer.improve_ocr_result(text_regions)

    # 过滤冲突检测 - OCR优先
    print("\n过滤冲突检测...")
    final_text_regions, final_bar_charts, final_circles = conflict_resolver.filter_conflicting_detections(
        improved_text_regions, bar_charts, circles
    )

    print(f"最终检测结果: 圆形={len(final_circles)}, 文字={len(final_text_regions)}, 柱状图={len(final_bar_charts)}")

    # 创建可视化
    print("\n创建非重叠可视化标记...")
    result_image = image.copy()

    # 1. 绘制圆形检测
    for i, circle in enumerate(final_circles):
        center = circle['center']
        radius = circle['radius']
        semantic_type = circle.get('semantic_type', 'unknown')
        validation_score = circle.get('validation_score', 0)

        if 'auxiliary' in semantic_type:
            color = renderer.colors['circle_auxiliary']
            type_text = "辅助仪表"
        else:
            color = renderer.colors['circle_indicator']
            type_text = "状态指示器"

        thickness = max(2, int(validation_score * 5))

        # 绘制圆形
        cv2.circle(result_image, center, radius, color, thickness)
        cv2.circle(result_image, center, 3, color, -1)

        # 绘制标签
        label_text = f"C{i+1}:{type_text}"
        label_pos = (center[0] - 40, center[1] - radius - 25)
        result_image = renderer.draw_chinese_text(
            result_image, label_text, label_pos, color, font_size=14
        )

    # 2. 绘制过滤后的柱状图检测
    for i, chart in enumerate(final_bar_charts):
        bounds = chart['bounds']
        x, y, w, h = bounds
        chart_type = chart['chart_type']
        confidence = chart['confidence']
        bar_count = chart['bar_count']

        type_text, color = renderer.get_bar_chart_info(chart_type)

        # 绘制边界矩形
        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)

        # 绘制标签
        label_text = f"B{i+1}:{type_text}"
        label_pos = (x, y - 20)
        result_image = renderer.draw_chinese_text(
            result_image, label_text, label_pos, color, font_size=12
        )

    # 3. 绘制文字检测 - 优先级最高
    for i, text_region in enumerate(final_text_regions):
        bounds = text_region['bounds']
        x1, y1, x2, y2 = bounds
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)

        lang_text, color = renderer.get_language_info(language)

        # 绘制内容标签
        content_label = f"[{lang_text}]{content}"
        content_pos = (x1, y1 - 25)
        result_image = renderer.draw_chinese_text(
            result_image, content_label, content_pos, color, font_size=12
        )

        # 置信度标签
        conf_label = f"置信度:{confidence:.2f}"
        conf_pos = (x1, y1 - 10)
        result_image = renderer.draw_chinese_text(
            result_image, conf_label, conf_pos, color, font_size=10
        )

    # 4. 添加图例
    legend_items = [
        ("OCR优先规则", (255, 255, 255)),
        ("圆形检测", renderer.colors['circle_auxiliary']),
        ("  紫色 = 辅助仪表", renderer.colors['circle_auxiliary']),
        ("柱状图检测 (避开OCR)", renderer.colors['bar_signal']),
        ("  橙色 = 信号强度", renderer.colors['bar_signal']),
        ("  蓝色 = 电池电量", renderer.colors['bar_battery']),
        ("  紫红 = 状态柱", renderer.colors['bar_status']),
        ("文字识别 (最高优先)", renderer.colors['text_chinese']),
        ("  绿色 = 中文", renderer.colors['text_chinese']),
        ("  黄色 = 英文", renderer.colors['text_english']),
        ("  粉色 = 数字", renderer.colors['text_numeric']),
        ("  青色 = 混合", renderer.colors['text_mixed'])
    ]

    for i, (label, color) in enumerate(legend_items):
        y_pos = 25 + i * 16
        result_image = renderer.draw_chinese_text(
            result_image, label, (10, y_pos), color, font_size=11
        )

    # 5. 添加统计信息
    stats_items = [
        "非重叠检测统计",
        f"总元素: {len(final_circles) + len(final_bar_charts) + len(final_text_regions)} 个",
        f"圆形检测: {len(final_circles)} 个",
        f"柱状图检测: {len(final_bar_charts)} 个",
        f"文字识别: {len(final_text_regions)} 个",
        f"过滤的柱状图: {len(bar_charts) - len(final_bar_charts)} 个",
        f"过滤的圆形: {len(circles) - len(final_circles)} 个",
        "检测规则: OCR优先不重叠"
    ]

    stats_x = image.shape[1] - 220
    for i, text in enumerate(stats_items):
        y_pos = 25 + i * 16
        color = (255, 255, 255) if i == 0 else (200, 200, 200)
        result_image = renderer.draw_chinese_text(
            result_image, text, (stats_x, y_pos), color, font_size=10
        )

    # 保存最终结果
    output_path = "../../non_overlapping_final_result.png"
    cv2.imwrite(output_path, result_image)

    print(f"\n非重叠的最终可视化结果已保存: {output_path}")
    print(f"检测规则: OCR文字识别具有最高优先级，图形检测避开文字区域")
    print("=" * 60)

if __name__ == "__main__":
    create_non_overlapping_visualization()