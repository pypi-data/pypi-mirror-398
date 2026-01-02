#!/usr/bin/env python3
"""
本地测试脚本 - 在backend/core目录下测试
"""

import cv2
import numpy as np
import os
import sys
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_detector import AdvancedDetector
from basic_detector import BasicDetector

def test_local():
    """本地测试"""

    print("=" * 50)
    print("本地检测测试")
    print("=" * 50)

    # 初始化检测器
    print("初始化检测器...")
    basic_detector = BasicDetector()
    advanced_detector = AdvancedDetector()

    # 测试图像路径 (相对于项目根目录)
    test_image = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image):
        print(f"测试图像不存在: {test_image}")
        # 尝试其他路径
        test_image = "../resources/20250910-100334.png"
        if not os.path.exists(test_image):
            print(f"测试图像也不存在: {test_image}")
            return

    print(f"测试图像: {test_image}")

    # 加载图像
    image = cv2.imread(test_image)
    if image is None:
        print("无法加载图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]} 像素")

    # 基础检测
    print("\n基础检测器:")
    start_time = time.time()
    basic_result = basic_detector.detect_all_elements(image)
    basic_time = time.time() - start_time

    basic_circles = len(basic_result['detected_elements']['circles'])
    basic_rectangles = len(basic_result['detected_elements']['rectangles'])
    basic_total = basic_circles + basic_rectangles

    print(f"圆形: {basic_circles}, 矩形: {basic_rectangles}, 总计: {basic_total}")
    print(f"耗时: {basic_time:.3f} 秒")

    # 高级检测
    print("\n高级检测器:")
    start_time = time.time()
    advanced_result = advanced_detector.enhanced_detect_all_elements(image)
    advanced_time = time.time() - start_time

    advanced_total = advanced_result['detected_elements']['total_count']
    enhanced_elements = advanced_result['detected_elements']['enhanced_elements']

    # 统计元素类型
    element_types = {}
    for element in enhanced_elements:
        elem_type = element['type']
        element_types[elem_type] = element_types.get(elem_type, 0) + 1

    print(f"总计元素: {advanced_total}")
    print(f"元素类型: {dict(element_types)}")
    print(f"耗时: {advanced_time:.3f} 秒")

    # 显示检测到的元素
    print("\n检测到的元素:")
    for i, element in enumerate(enhanced_elements[:10]):  # 显示前10个
        elem_type = element['type']
        if elem_type == 'circle':
            center = element['center']
            radius = element['radius']
            print(f"  {i+1}. 圆形 - 中心({center[0]},{center[1]}), 半径{radius}")
        elif elem_type == 'rectangle':
            bounds = element['bounds']
            print(f"  {i+1}. 矩形 - 位置({bounds[0]},{bounds[1]})-({bounds[2]},{bounds[3]})")
        else:
            print(f"  {i+1}. {elem_type} - {element.get('semantic_name', '未知')}")

    print("\n测试完成!")

if __name__ == "__main__":
    test_local()