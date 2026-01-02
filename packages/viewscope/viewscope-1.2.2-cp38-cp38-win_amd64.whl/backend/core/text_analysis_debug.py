#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文字识别详细分析调试
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector

def analyze_text_recognition_accuracy():
    """分析文字识别精确度"""

    print("=" * 60)
    print("文字识别精确度分析")
    print("=" * 60)

    # 初始化检测器
    detector = ComprehensiveDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    # 执行检测
    result = detector.comprehensive_detection(image)
    text_regions = result['elements']['text_regions']

    print(f"总文字区域: {len(text_regions)}")
    print("\n详细识别结果分析:")
    print("-" * 60)

    # 分析每个文字区域
    for i, text_region in enumerate(text_regions):
        bounds = text_region['bounds']
        x1, y1, x2, y2 = bounds
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)
        ocr_engine = text_region.get('ocr_engine', 'unknown')

        print(f"\n文字区域 #{i+1}:")
        print(f"  位置: ({x1}, {y1}) -> ({x2}, {y2})")
        print(f"  尺寸: {x2-x1}x{y2-y1} 像素")
        print(f"  内容: '{content}'")
        print(f"  语言类型: {language}")
        print(f"  置信度: {confidence:.3f}")
        print(f"  识别引擎: {ocr_engine}")

        # 特别分析问题文字
        if "ERRORkm" in content or "ERROR" in content:
            print(f"  >>> 发现ERRORkm文字区域")
            print(f"      原始内容: '{content}'")
            print(f"      应为: 'ERROR km' 或 'ERRORkm'")
            print(f"      分类为: [{language}] - 应为: [英文]")

        elif "kWh" in content or "KWh" in content or "kwh" in content:
            print(f"  >>> 发现kWh相关文字区域")
            print(f"      原始内容: '{content}'")
            print(f"      应为: '--.-kWh/100km'")
            print(f"      分类为: [{language}] - 应为: [混合] (符号+英文+数字)")

        # 分析中文识别情况
        elif language == 'chinese':
            chinese_chars = []
            for char in content:
                if '\u4e00' <= char <= '\u9fff':
                    chinese_chars.append(char)
            print(f"  >>> 中文字符: {chinese_chars}")

    print("\n" + "=" * 60)
    print("问题分析:")
    print("=" * 60)

    # 查找具体的问题文字
    error_texts = [t for t in text_regions if "ERROR" in t['text'] or "error" in t['text'].lower()]
    kwh_texts = [t for t in text_regions if "kwh" in t['text'].lower() or "kWh" in t['text'] or "--" in t['text']]

    if error_texts:
        print("\nERRORkm 识别问题:")
        for t in error_texts:
            print(f"  识别为: '{t['text']}' 语言: {t.get('language', 'unknown')}")
            print(f"  分析: 应该识别为英文文字，但可能被分类为其他")

    if kwh_texts:
        print("\nkWh/100km 识别问题:")
        for t in kwh_texts:
            print(f"  识别为: '{t['text']}' 语言: {t.get('language', 'unknown')}")
            print(f"  分析: 包含符号、英文、数字的混合内容")

    print("\n结论:")
    print("1. OCR识别准确性 - 文字内容是否正确识别")
    print("2. 语言分类准确性 - 是否正确分类为英文/混合类型")
    print("3. 标记显示准确性 - 可视化标记是否对应正确的语言类型")

if __name__ == "__main__":
    analyze_text_recognition_accuracy()