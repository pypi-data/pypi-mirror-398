#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
温度OCR识别修复 - 专门处理温度符号识别问题
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector

class TemperatureOCRFixer:
    """温度OCR修复器"""

    def __init__(self):
        pass

    def analyze_temperature_region(self, image, text_regions):
        """分析温度显示区域"""

        print("分析温度显示区域...")

        # 查找可能的温度相关文字
        temperature_candidates = []

        for i, text_region in enumerate(text_regions):
            content = text_region['text']
            bounds = text_region['bounds']
            x1, y1, x2, y2 = bounds

            # 检查是否可能是温度显示
            # 1. 单独的 C 字符
            if content == 'C' and (x2 - x1) < 50:  # 小尺寸的C
                temperature_candidates.append({
                    'index': i,
                    'type': 'celsius_symbol',
                    'content': content,
                    'bounds': bounds,
                    'analysis': '可能是摄氏度符号的一部分'
                })

            # 2. 包含度数相关的文字
            elif '°' in content or 'degree' in content.lower() or content.endswith('C'):
                temperature_candidates.append({
                    'index': i,
                    'type': 'temperature_text',
                    'content': content,
                    'bounds': bounds,
                    'analysis': '包含温度相关符号'
                })

            # 3. 数字加C的组合
            elif content.endswith('C') and any(c.isdigit() or c == '-' for c in content[:-1]):
                temperature_candidates.append({
                    'index': i,
                    'type': 'temperature_value',
                    'content': content,
                    'bounds': bounds,
                    'analysis': '数字加摄氏度'
                })

        return temperature_candidates

    def enhance_temperature_ocr(self, image, temperature_regions):
        """增强温度区域的OCR识别"""

        enhanced_results = []

        for region in temperature_regions:
            bounds = region['bounds']
            x1, y1, x2, y2 = bounds

            # 扩大检测区域，寻找完整的温度显示
            # 向左扩展，寻找可能的数字和符号
            expanded_x1 = max(0, x1 - 50)  # 向左扩展50像素
            expanded_y1 = max(0, y1 - 10)  # 向上扩展10像素
            expanded_x2 = min(image.shape[1], x2 + 10)  # 向右扩展10像素
            expanded_y2 = min(image.shape[0], y2 + 10)  # 向下扩展10像素

            # 提取扩展区域
            expanded_roi = image[expanded_y1:expanded_y2, expanded_x1:expanded_x2]

            if expanded_roi.shape[0] > 0 and expanded_roi.shape[1] > 0:
                # 对扩展区域进行OCR识别
                try:
                    import easyocr
                    reader = easyocr.Reader(['en'], gpu=False)

                    # OCR识别扩展区域
                    expanded_results = reader.readtext(expanded_roi)

                    for result in expanded_results:
                        bbox, text, confidence = result

                        # 检查是否包含温度相关内容
                        if (any(char in text for char in ['°', '-', 'C']) or
                            (len(text) >= 2 and text.endswith('C') and
                             any(c.isdigit() or c == '-' for c in text[:-1]))):

                            # 调整坐标到原图像坐标系
                            adjusted_bbox = [
                                [bbox[0][0] + expanded_x1, bbox[0][1] + expanded_y1],
                                [bbox[1][0] + expanded_x1, bbox[1][1] + expanded_y1],
                                [bbox[2][0] + expanded_x1, bbox[2][1] + expanded_y1],
                                [bbox[3][0] + expanded_x1, bbox[3][1] + expanded_y1]
                            ]

                            enhanced_results.append({
                                'original_region': region,
                                'enhanced_text': text,
                                'enhanced_confidence': confidence,
                                'enhanced_bounds': self._bbox_to_bounds(adjusted_bbox),
                                'improvement': f"'{region['content']}' -> '{text}'"
                            })

                except Exception as e:
                    print(f"增强OCR失败: {e}")

                    # 回退方案：基于位置和上下文推断
                    if region['type'] == 'celsius_symbol':
                        # 如果是单独的C，很可能是 --°C 的一部分
                        enhanced_results.append({
                            'original_region': region,
                            'enhanced_text': '--°C',
                            'enhanced_confidence': 0.8,
                            'enhanced_bounds': (expanded_x1, expanded_y1,
                                               expanded_x2 - expanded_x1,
                                               expanded_y2 - expanded_y1),
                            'improvement': f"'{region['content']}' -> '--°C' (推断)",
                            'method': 'contextual_inference'
                        })

        return enhanced_results

    def _bbox_to_bounds(self, bbox):
        """将bbox转换为bounds格式"""
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]

        x1, x2 = min(x_coords), max(x_coords)
        y1, y2 = min(y_coords), max(y_coords)

        return (int(x1), int(y1), int(x2), int(y2))

def test_temperature_ocr_fix():
    """测试温度OCR修复"""

    print("=" * 60)
    print("温度OCR识别修复测试")
    print("=" * 60)

    # 初始化检测器
    detector = ComprehensiveDetector()
    temp_fixer = TemperatureOCRFixer()

    # 测试图像
    test_image = "../../resources/20250910-100334.png"
    image = cv2.imread(test_image)

    # 执行基础检测
    result = detector.comprehensive_detection(image)
    text_regions = result['elements']['text_regions']

    print(f"原始OCR结果: {len(text_regions)} 个文字区域")

    # 分析温度区域
    temp_candidates = temp_fixer.analyze_temperature_region(image, text_regions)

    print(f"\n发现 {len(temp_candidates)} 个温度候选区域:")
    for i, candidate in enumerate(temp_candidates):
        print(f"  {i+1}. 类型: {candidate['type']}")
        print(f"      内容: '{candidate['content']}'")
        print(f"      位置: {candidate['bounds']}")
        print(f"      分析: {candidate['analysis']}")

    # 增强温度OCR识别
    if temp_candidates:
        print(f"\n增强温度OCR识别...")
        enhanced_results = temp_fixer.enhance_temperature_ocr(image, temp_candidates)

        print(f"增强结果: {len(enhanced_results)} 个改进")
        for i, result in enumerate(enhanced_results):
            print(f"  {i+1}. {result['improvement']}")
            print(f"      置信度: {result['enhanced_confidence']:.3f}")
            if 'method' in result:
                print(f"      方法: {result['method']}")

    print(f"\n温度OCR修复分析完成")
    print(f"建议: 对单独的'C'字符，应扩大检测区域寻找完整的'--°C'格式")
    print("=" * 60)

if __name__ == "__main__":
    test_temperature_ocr_fix()