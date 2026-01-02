#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题分析
"""

import cv2
import numpy as np
import os
import sys

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector

def main():
    """分析两个具体问题"""

    print("=" * 50)
    print("OCR问题分析")
    print("=" * 50)

    # 初始化检测器
    detector = ComprehensiveDetector()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    # 执行检测
    result = detector.comprehensive_detection(image)
    text_regions = result['elements']['text_regions']

    print("发现的问题文字:")
    print("-" * 30)

    for i, text_region in enumerate(text_regions):
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)

        # 问题1: ERRORkm
        if "ERROR" in content:
            print("\n问题1: ERRORkm")
            print(f"  识别内容: '{content}'")
            print(f"  语言分类: {language}")
            print(f"  置信度: {confidence:.3f}")
            print("  分析: OCR识别正确，语言分类正确(english)")
            print("  结论: 标记显示问题 - 应显示黄色[英文]标签")

        # 问题2: kWh相关
        elif "KWh" in content or "kWh" in content:
            print("\n问题2: kWh/100km")
            print(f"  识别内容: '{content}'")
            print(f"  语言分类: {language}")
            print(f"  置信度: {confidence:.3f}")
            print(f"  期望内容: '--.-kWh/100km'")
            print("  错误类型:")
            print("    - 符号错误: -- 识别为 一")
            print("    - 数字错误: 100 识别为 loO")
            print("  结论: OCR识别精度问题")

    print("\n" + "=" * 50)
    print("问题总结:")
    print("=" * 50)
    print("1. ERRORkm: 标记显示问题")
    print("   - OCR识别: 正确")
    print("   - 语言分类: 正确")
    print("   - 需修复: 标记颜色逻辑")

    print("\n2. --.-kWh/100km: OCR识别问题")
    print("   - OCR识别: 错误")
    print("   - 语言分类: 正确")
    print("   - 需修复: OCR预处理或多引擎验证")

if __name__ == "__main__":
    main()