#!/usr/bin/env python3
"""
综合检测测试 - 在backend/core目录下直接运行，使用所有检测功能
"""

import cv2
import numpy as np
import os
import sys
import time

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_detector import AdvancedDetector
from basic_detector import BasicDetector

def comprehensive_test():
    """综合测试所有检测功能"""

    print("=" * 60)
    print("综合检测功能测试")
    print("=" * 60)

    # 初始化检测器
    print("初始化检测器...")
    advanced_detector = AdvancedDetector()
    basic_detector = BasicDetector()

    # 测试图像路径 (相对于backend/core目录)
    test_image = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image):
        print(f"测试图像不存在: {test_image}")
        return

    print(f"测试图像: {test_image}")

    # 加载图像
    image = cv2.imread(test_image)
    if image is None:
        print("无法加载图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]} 像素")

    # 1. 基础检测
    print("\n【基础检测】")
    start_time = time.time()
    basic_result = basic_detector.detect_all_elements(image)
    basic_time = time.time() - start_time

    basic_circles = len(basic_result['detected_elements']['circles'])
    basic_rectangles = len(basic_result['detected_elements']['rectangles'])
    basic_total = basic_circles + basic_rectangles

    print(f"圆形: {basic_circles}, 矩形: {basic_rectangles}, 总计: {basic_total}")
    print(f"耗时: {basic_time:.3f}s")

    # 2. 高级检测 - 使用所有功能
    print("\n【高级增强检测】")
    start_time = time.time()

    # 直接调用高级检测器的各个方法
    print("正在执行SIFT特征检测...")
    sift_kp, sift_desc = advanced_detector.detect_features_sift(image)
    print(f"SIFT特征点: {len(sift_kp)}")

    print("正在执行ORB特征检测...")
    orb_kp, orb_desc = advanced_detector.detect_features_orb(image)
    print(f"ORB特征点: {len(orb_kp)}")

    print("正在执行增强圆形检测...")
    enhanced_circles = advanced_detector._detect_enhanced_circles(image)
    print(f"增强圆形检测: {len(enhanced_circles)}")

    print("正在执行增强矩形检测...")
    enhanced_rectangles = advanced_detector._detect_enhanced_rectangles(image)
    print(f"增强矩形检测: {len(enhanced_rectangles)}")

    print("正在执行不规则形状检测...")
    irregular_shapes = advanced_detector._detect_irregular_shapes(image)
    print(f"不规则形状检测: {len(irregular_shapes)}")

    advanced_time = time.time() - start_time
    print(f"高级检测总耗时: {advanced_time:.3f}s")

    # 3. 合并所有检测结果
    print("\n【检测结果合并】")
    all_elements = []

    # 添加基础检测的圆形
    for circle in basic_result['detected_elements']['circles']:
        all_elements.append(circle)

    # 添加增强检测的圆形
    for circle_data in enhanced_circles:
        all_elements.append(circle_data)

    # 添加增强检测的矩形
    for rect_data in enhanced_rectangles:
        all_elements.append(rect_data)

    # 添加不规则形状
    for shape_data in irregular_shapes:
        all_elements.append(shape_data)

    total_elements = len(all_elements)

    # 统计元素类型
    element_types = {}
    for element in all_elements:
        elem_type = element['type']
        element_types[elem_type] = element_types.get(elem_type, 0) + 1

    print(f"合并后总元素数: {total_elements}")
    print(f"元素类型分布: {dict(element_types)}")

    # 4. 语义分析和OCR测试
    print("\n【语义分析和OCR测试】")

    # 对前5个元素进行详细分析
    analyzed_elements = []
    for i, element in enumerate(all_elements[:5]):
        print(f"分析元素 {i+1}/{min(5, total_elements)}...")

        # 智能元素标记
        enhanced_element = advanced_detector.smart_element_labeling(element)

        # 语义分析
        semantic_element = advanced_detector.analyze_element_semantics(enhanced_element, image)

        analyzed_elements.append(semantic_element)

    # 5. 颜色分析测试
    print("\n【颜色分析测试】")
    if all_elements:
        # 对第一个圆形元素进行颜色分析
        for element in all_elements:
            if element['type'] == 'circle':
                center = element['center']
                radius = element['radius']

                # 提取ROI
                x1, y1 = max(0, center[0] - radius), max(0, center[1] - radius)
                x2, y2 = min(image.shape[1], center[0] + radius), min(image.shape[0], center[1] + radius)
                roi = image[y1:y2, x1:x2]

                if roi.size > 0:
                    color_analysis = advanced_detector.analyze_hsv_colors(roi)
                    print(f"颜色分析示例:")
                    print(f"  主要颜色: {color_analysis['primary_color']}")
                    print(f"  颜色多样性: {color_analysis['color_diversity']}")
                    print(f"  主导色彩: {color_analysis['dominant_colors'][:3]}")  # 显示前3个
                break

    # 6. OCR文字识别测试
    print("\n【OCR文字识别测试】")
    # 在图像的几个区域尝试OCR
    height, width = image.shape[:2]
    test_regions = [
        (0, 0, width//3, height//3),           # 左上角
        (width//3, 0, 2*width//3, height//3), # 中上部
        (2*width//3, 0, width, height//3),    # 右上角
    ]

    ocr_results = []
    for i, region in enumerate(test_regions):
        x1, y1, x2, y2 = region
        ocr_result = advanced_detector.extract_text_from_region(image, (x1, y1, x2, y2))
        if ocr_result['text']:
            ocr_results.append(ocr_result)
            print(f"区域 {i+1} OCR结果: '{ocr_result['text']}' (置信度: {ocr_result['confidence']:.1f}%)")

    # 7. 最终统计
    print("\n【最终统计】")
    print("="*60)

    semantic_count = sum(1 for e in analyzed_elements if e.get('semantic_function', 'unknown_element') != 'unknown_element')
    text_count = len(ocr_results)

    print(f"基础检测: {basic_total} 个元素")
    print(f"高级检测总计: {total_elements} 个元素")
    print(f"SIFT特征点: {len(sift_kp)} 个")
    print(f"ORB特征点: {len(orb_kp)} 个")
    print(f"语义分析成功: {semantic_count} 个元素")
    print(f"OCR识别成功: {text_count} 个区域")

    if basic_total > 0:
        print(f"检测能力提升: {total_elements/basic_total:.1f} 倍")

    print(f"基础检测时间: {basic_time:.3f}s")
    print(f"高级检测时间: {advanced_time:.3f}s")

    # 详细显示分析结果
    print(f"\n【详细分析结果】")
    for i, element in enumerate(analyzed_elements):
        print(f"元素 {i+1}:")
        print(f"  类型: {element['type']}")
        print(f"  语义名称: {element.get('semantic_name', 'unknown')}")
        print(f"  置信度: {element.get('confidence', 0):.2f}")
        if element.get('semantic_function'):
            print(f"  推断功能: {element['semantic_function']}")
        if element.get('ocr_result') and element['ocr_result']['text']:
            print(f"  识别文字: '{element['ocr_result']['text']}'")

    print("\n综合检测测试完成! 已使用所有检测功能")
    print("="*60)

if __name__ == "__main__":
    comprehensive_test()