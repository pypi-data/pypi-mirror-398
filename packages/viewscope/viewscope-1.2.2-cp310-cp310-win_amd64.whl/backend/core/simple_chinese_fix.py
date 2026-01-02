#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版中文显示修复
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector

def create_chinese_fixed_visualization():
    """创建中文显示修复版可视化"""

    print("=" * 50)
    print("中文显示修复")
    print("=" * 50)

    # 初始化检测器
    detector = ComprehensiveDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    # 执行检测
    result = detector.comprehensive_detection(image)
    circles = result['elements']['circles']
    text_regions = result['elements']['text_regions']

    print(f"检测结果: 圆形={len(circles)}, 文字={len(text_regions)}")

    # 创建可视化
    result_image = image.copy()

    # 加载中文字体
    try:
        font_path = "C:/Windows/Fonts/msyh.ttc"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 16)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    def draw_chinese_text(img, text, pos, color, size=16):
        """绘制中文文字"""
        try:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            draw.text(pos, text, font=font, fill=color)
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except:
            return img

    # 绘制圆形检测
    for i, circle in enumerate(circles):
        center = circle['center']
        radius = circle['radius']
        semantic_type = circle.get('semantic_type', 'unknown')
        validation_score = circle.get('validation_score', 0)

        if 'auxiliary' in semantic_type:
            color = (255, 0, 255)  # 紫色
            type_text = "辅助仪表"
        else:
            color = (128, 128, 128)  # 灰色
            type_text = "状态指示器"

        # 绘制圆形
        cv2.circle(result_image, center, radius, color, 3)
        cv2.circle(result_image, center, 3, color, -1)

        # 绘制中文标签
        label_text = f"C{i+1}:{type_text}"
        label_pos = (center[0] - 40, center[1] - radius - 25)
        result_image = draw_chinese_text(result_image, label_text, label_pos, color)

    # 绘制文字检测
    for i, text_region in enumerate(text_regions):
        bounds = text_region['bounds']
        x1, y1, x2, y2 = bounds
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)

        # 选择颜色
        if language == 'chinese':
            color = (0, 255, 128)
            lang_text = "中文"
        elif language == 'english':
            color = (128, 255, 0)
            lang_text = "英文"
        elif language == 'numeric':
            color = (255, 128, 255)
            lang_text = "数字"
        else:
            color = (255, 255, 255)
            lang_text = "其他"

        # 绘制边界框
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)

        # 绘制中文内容标签
        display_content = content[:6] + "..." if len(content) > 6 else content
        content_label = f"[{lang_text}]{display_content}"
        content_pos = (x1, y1 - 20)
        result_image = draw_chinese_text(result_image, content_label, content_pos, color)

    # 添加图例
    legend_items = [
        ("圆形检测:", (255, 255, 255)),
        ("紫色=辅助仪表", (255, 0, 255)),
        ("灰色=状态指示器", (128, 128, 128)),
        ("文字识别:", (255, 255, 255)),
        ("绿色=中文", (0, 255, 128)),
        ("黄色=英文", (128, 255, 0)),
        ("粉色=数字", (255, 128, 255))
    ]

    for i, (text, color) in enumerate(legend_items):
        y_pos = 25 + i * 18
        result_image = draw_chinese_text(result_image, text, (10, y_pos), color)

    # 添加统计信息
    stats_items = [
        f"检测统计:",
        f"圆形: {len(circles)} 个",
        f"文字: {len(text_regions)} 个",
        f"耗时: {result['detection_time']:.2f}秒"
    ]

    stats_x = image.shape[1] - 150
    for i, text in enumerate(stats_items):
        y_pos = 25 + i * 18
        result_image = draw_chinese_text(result_image, text, (stats_x, y_pos), (255, 255, 255))

    # 保存结果
    output_path = "../../chinese_fixed_result.png"
    cv2.imwrite(output_path, result_image)

    print(f"中文显示修复版已保存: {output_path}")

    # 显示识别的中文内容
    chinese_texts = [t for t in text_regions if t.get('language') == 'chinese']
    print(f"\n识别的中文内容:")
    for i, text in enumerate(chinese_texts):
        content = text['text']
        confidence = text['confidence']
        print(f"  {i+1}. '{content}' (置信度: {confidence:.3f})")

    print("\n中文显示问题修复完成!")

if __name__ == "__main__":
    create_chinese_fixed_visualization()