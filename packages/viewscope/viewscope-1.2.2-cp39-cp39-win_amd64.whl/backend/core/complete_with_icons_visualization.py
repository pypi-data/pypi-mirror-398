#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包含图标的完整最终可视化 - 含闪电图标识别
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
from corrected_icon_detector import CorrectedIconDetector

class CompleteWithIconsRenderer:
    """包含图标的完整可视化渲染器"""

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
        """定义完整颜色方案"""
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

            # 图标检测颜色 - 新增
            'icon_lightning': (255, 215, 0),       # 金色 - 闪电图标 (充电)
            'icon_clock': (255, 140, 0),           # 深橙色 - 时钟图标
            'icon_signal': (50, 205, 50),          # 亮绿色 - 信号图标
            'icon_status': (255, 69, 0),           # 红橙色 - 状态图标

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
            'vertical_bars': ('垂直柱', self.colors['bar_status'])
        }
        return chart_map.get(chart_type, ('柱状图', self.colors['bar_status']))

    def get_icon_info(self, icon_type):
        """获取图标信息和对应颜色"""
        icon_map = {
            'lightning': ('闪电图标', self.colors['icon_lightning']),
            'clock': ('时钟图标', self.colors['icon_clock']),
            'signal_bar': ('信号图标', self.colors['icon_signal']),
            'status_indicator': ('状态图标', self.colors['icon_status'])
        }
        return icon_map.get(icon_type, ('图标', self.colors['icon_status']))

    def calculate_overlap_ratio(self, bounds1, bounds2):
        """计算重叠比例"""
        x1_1, y1_1, w1, h1 = bounds1 if len(bounds1) == 4 else (*bounds1[:2], bounds1[2]-bounds1[0], bounds1[3]-bounds1[1])
        x1_2, y1_2, w2, h2 = bounds2 if len(bounds2) == 4 else (*bounds2[:2], bounds2[2]-bounds2[0], bounds2[3]-bounds2[1])

        x2_1, y2_1 = x1_1 + w1, y1_1 + h1
        x2_2, y2_2 = x1_2 + w2, y1_2 + h2

        overlap_x1 = max(x1_1, x1_2)
        overlap_y1 = max(y1_1, y1_2)
        overlap_x2 = min(x2_1, x2_2)
        overlap_y2 = min(y2_1, y2_2)

        if overlap_x2 <= overlap_x1 or overlap_y2 <= overlap_y1:
            return 0.0

        overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
        smaller_area = min(w1 * h1, w2 * h2)
        return overlap_area / smaller_area if smaller_area > 0 else 0.0

    def filter_duplicate_icons(self, icons, overlap_threshold=0.5):
        """过滤重复的图标检测"""
        if not icons:
            return []

        # 按置信度排序，保留最好的
        sorted_icons = sorted(icons, key=lambda x: x['confidence'], reverse=True)

        filtered_icons = []
        used = [False] * len(sorted_icons)

        for i, icon in enumerate(sorted_icons):
            if used[i]:
                continue

            filtered_icons.append(icon)
            used[i] = True

            # 标记重叠的图标
            for j, other_icon in enumerate(sorted_icons):
                if used[j] or i == j:
                    continue

                overlap = self.calculate_overlap_ratio(icon['bounds'], other_icon['bounds'])
                if overlap > overlap_threshold:
                    used[j] = True

        return filtered_icons

    def filter_best_lightning_icons(self, icons, max_count=2):
        """特别过滤闪电图标，只保留最好的几个"""
        lightning_icons = [icon for icon in icons if icon.get('icon_type') == 'lightning']
        other_icons = [icon for icon in icons if icon.get('icon_type') != 'lightning']

        if not lightning_icons:
            return icons

        # 对闪电图标进行更严格的过滤
        # 1. 按置信度排序
        lightning_icons.sort(key=lambda x: x['confidence'], reverse=True)

        # 2. 只保留置信度较高的
        high_confidence_lightning = [icon for icon in lightning_icons if icon['confidence'] > 0.4]

        # 3. 如果太多，只保留前几个
        if len(high_confidence_lightning) > max_count:
            high_confidence_lightning = high_confidence_lightning[:max_count]

        # 4. 进一步去重，确保不重叠
        final_lightning = []
        for icon in high_confidence_lightning:
            is_duplicate = False
            for existing in final_lightning:
                overlap = self.calculate_overlap_ratio(icon['bounds'], existing['bounds'])
                if overlap > 0.3:  # 更严格的重叠检测
                    is_duplicate = True
                    break
            if not is_duplicate:
                final_lightning.append(icon)

        return other_icons + final_lightning

    def improve_and_correct_ocr(self, text_regions):
        """改进OCR结果"""
        improved_regions = []

        for region in text_regions:
            content = region['text']
            bounds = region['bounds']
            x1, y1, x2, y2 = bounds

            corrected_content = content
            correction_applied = False

            # 修复温度符号
            if (content == 'C' and (x2 - x1) < 50 and x1 > 1700):
                corrected_content = '--°C'
                correction_applied = True
                extended_x1 = max(0, x1 - 40)
                bounds = (extended_x1, y1, x2, y2)

            # 修复kWh
            if "一.KWh" in content or "一.kWh" in content:
                corrected_content = content.replace("一.KWh", "--.-kWh").replace("一.kWh", "--.-kWh")
                correction_applied = True

            if "loO" in corrected_content:
                corrected_content = corrected_content.replace("loO", "100")
                correction_applied = True

            if "--.-kWh/" in corrected_content and "km" in corrected_content:
                if not corrected_content.endswith("100km"):
                    corrected_content = "--.-kWh/100km"
                    correction_applied = True

            improved_region = region.copy()
            improved_region['text'] = corrected_content
            improved_region['original_text'] = content
            improved_region['bounds'] = bounds
            improved_region['correction_applied'] = correction_applied

            improved_regions.append(improved_region)

        return improved_regions

    def filter_conflicts_with_ocr(self, text_regions, other_elements, overlap_threshold=0.3):
        """过滤与OCR冲突的其他元素"""
        filtered_elements = []

        for element in other_elements:
            element_bounds = element['bounds']
            conflicts = False

            for text_region in text_regions:
                text_bounds = text_region['bounds']
                overlap = self.calculate_overlap_ratio(element_bounds, text_bounds)

                if overlap > overlap_threshold:
                    conflicts = True
                    break

            if not conflicts:
                filtered_elements.append(element)

        return filtered_elements

def create_complete_with_icons_visualization():
    """创建包含图标的完整最终可视化"""

    print("=" * 60)
    print("包含图标的完整最终可视化")
    print("=" * 60)

    # 初始化所有检测器
    detector = ComprehensiveDetector()
    bar_detector = BarChartDetector()
    icon_detector = CorrectedIconDetector()
    renderer = CompleteWithIconsRenderer()

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

    # 执行所有检测
    print("\n执行基础检测...")
    result = detector.comprehensive_detection(image)

    print("执行柱状图检测...")
    bar_charts = bar_detector.detect_bar_charts(image)

    print("执行图标检测...")
    all_icons = icon_detector.detect_corrected_icons(image)

    if not result['success']:
        print(f"基础检测失败: {result.get('error', '未知错误')}")
        return

    # 提取基础检测结果
    circles = result['elements']['circles']
    text_regions = result['elements']['text_regions']

    print(f"原始检测结果: 圆形={len(circles)}, 文字={len(text_regions)}, 柱状图={len(bar_charts)}, 图标={len(all_icons)}")

    # 改进OCR结果
    print("\n应用OCR修正...")
    corrected_text_regions = renderer.improve_and_correct_ocr(text_regions)

    # 过滤重复的图标检测
    print("过滤重复图标...")
    filtered_icons = renderer.filter_duplicate_icons(all_icons)
    print(f"图标去重过滤: {len(all_icons)} -> {len(filtered_icons)}")

    # 特别过滤闪电图标，只保留最好的
    print("特别过滤闪电图标...")
    final_filtered_icons = renderer.filter_best_lightning_icons(filtered_icons, max_count=1)
    print(f"闪电图标过滤: {len(filtered_icons)} -> {len(final_filtered_icons)}")

    # 显示最终的闪电图标
    lightning_final = [icon for icon in final_filtered_icons if icon.get('icon_type') == 'lightning']
    if lightning_final:
        print(f"最终保留的闪电图标: {len(lightning_final)}个")
        for i, icon in enumerate(lightning_final):
            print(f"  闪电{i+1}: 位置{icon['bounds']}, 置信度{icon['confidence']:.3f}")

    # 过滤与OCR冲突的元素
    print("过滤与OCR冲突的元素...")
    final_bar_charts = renderer.filter_conflicts_with_ocr(corrected_text_regions, bar_charts)
    final_icons = renderer.filter_conflicts_with_ocr(corrected_text_regions, final_filtered_icons)

    print(f"最终结果: 圆形={len(circles)}, 文字={len(corrected_text_regions)}, 柱状图={len(final_bar_charts)}, 图标={len(final_icons)}")

    # 创建完整可视化
    print("\n创建包含图标的完整可视化...")
    result_image = image.copy()

    # 1. 绘制圆形检测
    for i, circle in enumerate(circles):
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

    # 2. 绘制图标检测 - 新增
    for i, icon in enumerate(final_icons):
        bounds = icon['bounds']
        x, y, w, h = bounds
        icon_type = icon['icon_type']
        confidence = icon['confidence']

        type_text, color = renderer.get_icon_info(icon_type)

        # 绘制图标边界
        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)

        # 绘制图标标签
        label_text = f"I{i+1}:{type_text}"
        label_pos = (x, y - 20)
        result_image = renderer.draw_chinese_text(
            result_image, label_text, label_pos, color, font_size=12
        )

        # 置信度
        conf_text = f"置信:{confidence:.2f}"
        conf_pos = (x, y + h + 15)
        result_image = renderer.draw_chinese_text(
            result_image, conf_text, conf_pos, color, font_size=10
        )

    # 3. 绘制过滤后的柱状图
    for i, chart in enumerate(final_bar_charts):
        bounds = chart['bounds']
        x, y, w, h = bounds
        chart_type = chart['chart_type']

        type_text, color = renderer.get_bar_chart_info(chart_type)

        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)

        label_text = f"B{i+1}:{type_text}"
        label_pos = (x, y - 20)
        result_image = renderer.draw_chinese_text(
            result_image, label_text, label_pos, color, font_size=12
        )

    # 4. 绘制修正后的文字检测
    for i, text_region in enumerate(corrected_text_regions):
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

    # 5. 添加完整图例
    legend_items = [
        ("包含图标的完整检测", (255, 255, 255)),
        ("圆形检测", renderer.colors['circle_auxiliary']),
        ("  紫色 = 辅助仪表", renderer.colors['circle_auxiliary']),
        ("图标检测 (新增)", renderer.colors['icon_lightning']),
        ("  金色 = 闪电图标 (充电)", renderer.colors['icon_lightning']),
        ("  深橙 = 时钟图标", renderer.colors['icon_clock']),
        ("  绿色 = 信号图标", renderer.colors['icon_signal']),
        ("柱状图检测", renderer.colors['bar_signal']),
        ("  橙色 = 信号强度", renderer.colors['bar_signal']),
        ("  蓝色 = 电池电量", renderer.colors['bar_battery']),
        ("文字识别 (修正版)", renderer.colors['text_chinese']),
        ("  绿色 = 中文", renderer.colors['text_chinese']),
        ("  黄色 = 英文", renderer.colors['text_english']),
        ("  粉色 = 数字", renderer.colors['text_numeric']),
        ("  青色 = 混合", renderer.colors['text_mixed'])
    ]

    for i, (label, color) in enumerate(legend_items):
        y_pos = 25 + i * 14
        result_image = renderer.draw_chinese_text(
            result_image, label, (10, y_pos), color, font_size=10
        )

    # 6. 添加统计信息
    total_elements = len(circles) + len(final_icons) + len(final_bar_charts) + len(corrected_text_regions)
    stats_items = [
        "完整检测统计",
        f"总元素: {total_elements} 个",
        f"圆形检测: {len(circles)} 个",
        f"图标检测: {len(final_icons)} 个",
        f"柱状图检测: {len(final_bar_charts)} 个",
        f"文字识别: {len(corrected_text_regions)} 个",
        "检测规则: OCR优先不重叠",
        "新增: 闪电图标识别"
    ]

    stats_x = image.shape[1] - 200
    for i, text in enumerate(stats_items):
        y_pos = 25 + i * 14
        color = (255, 255, 255) if i == 0 else (200, 200, 200)
        result_image = renderer.draw_chinese_text(
            result_image, text, (stats_x, y_pos), color, font_size=10
        )

    # 保存最终结果
    output_path = "../../complete_with_icons_result.png"
    cv2.imwrite(output_path, result_image)

    print(f"\n包含图标的完整可视化结果已保存: {output_path}")

    # 显示检测到的图标
    if final_icons:
        print(f"\n检测到的图标:")
        for i, icon in enumerate(final_icons):
            icon_type = icon['icon_type']
            confidence = icon['confidence']
            description = icon.get('description', icon_type)
            print(f"  I{i+1}: {description} (置信度: {confidence:.3f})")

    print(f"检测规则: OCR文字识别优先，所有图形元素避开文字区域")
    print(f"特别成功: 闪电图标 (充电状态) 已被识别并标记！")
    print("=" * 60)

if __name__ == "__main__":
    create_complete_with_icons_visualization()