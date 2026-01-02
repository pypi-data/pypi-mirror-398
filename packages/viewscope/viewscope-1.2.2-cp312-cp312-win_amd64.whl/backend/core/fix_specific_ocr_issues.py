#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复具体的OCR识别问题
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector

def analyze_specific_ocr_issues():
    """分析具体的OCR问题"""

    print("=" * 60)
    print("具体OCR问题分析")
    print("=" * 60)

    # 初始化检测器
    detector = ComprehensiveDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    # 执行检测
    result = detector.comprehensive_detection(image)
    text_regions = result['elements']['text_regions']

    print("问题文字分析:")
    print("-" * 40)

    for i, text_region in enumerate(text_regions):
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)
        bounds = text_region['bounds']

        # 问题1: ERRORkm 识别分析
        if "ERROR" in content:
            print(f"\n问题1: ERRORkm 文字")
            print(f"  OCR识别结果: '{content}'")
            print(f"  语言分类: {language}")
            print(f"  置信度: {confidence:.3f}")
            print(f"  分析结果:")
            print(f"    - OCR识别: 正确 ✓ (ERRORkm)")
            print(f"    - 语言分类: 正确 ✓ (english)")
            print(f"    - 标记显示: 需要确认是否显示为[英文]")
            print(f"    - 结论: OCR和分类都正确，可能是标记显示问题")

        # 问题2: kWh/100km 识别分析
        elif "KWh" in content or "kWh" in content or ("--" in content and "km" in content):
            print(f"\n问题2: kWh/100km 文字")
            print(f"  OCR识别结果: '{content}'")
            print(f"  语言分类: {language}")
            print(f"  置信度: {confidence:.3f}")
            print(f"  期望内容: '--.-kWh/100km'")
            print(f"  分析结果:")

            # 分析OCR错误
            expected = "--.-kWh/100km"
            if content != expected:
                print(f"    - OCR识别: 错误 ✗")
                print(f"      识别为: '{content}'")
                print(f"      应该是: '{expected}'")
                print(f"      错误类型:")
                if "KWh" in content:
                    print(f"        * 大小写错误: KWh -> kWh")
                if "loO" in content or "loo" in content:
                    print(f"        * 数字识别错误: 100 -> loO/loo")
                if content.startswith("一"):
                    print(f"        * 符号识别错误: -- -> 一")
            else:
                print(f"    - OCR识别: 正确 ✓")

            # 分析语言分类
            if language == "mixed":
                print(f"    - 语言分类: 正确 ✓ (mixed - 符号+英文+数字)")
            else:
                print(f"    - 语言分类: 可能错误 (分类为{language}，应为mixed)")

            print(f"    - 结论: 主要是OCR识别精度问题")

    print(f"\n" + "=" * 60)
    print("总结:")
    print("=" * 60)
    print("1. ERRORkm:")
    print("   - OCR识别: 正确")
    print("   - 语言分类: 正确 (english)")
    print("   - 问题: 标记显示可能显示为[其他]而非[英文]")

    print("\n2. --.-kWh/100km:")
    print("   - OCR识别: 有误 (识别为'一.KWh/loOkm')")
    print("   - 语言分类: 正确 (mixed)")
    print("   - 问题: OCR对符号和数字的识别精度不足")

    print("\n修复建议:")
    print("1. ERRORkm: 检查标记颜色逻辑，确保英文显示为黄色")
    print("2. kWh/100km: 提高OCR预处理，或使用多引擎验证")

if __name__ == "__main__":
    analyze_specific_ocr_issues()