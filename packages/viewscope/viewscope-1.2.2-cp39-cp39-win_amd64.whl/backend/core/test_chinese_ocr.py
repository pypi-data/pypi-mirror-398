#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文OCR专项测试 - 修复中文显示问题
"""

import cv2
import numpy as np
import os
import sys
import json

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chinese_ocr():
    """专门测试中文OCR识别和显示"""

    print("=" * 60)
    print("中文OCR专项测试")
    print("=" * 60)

    # 测试图像
    test_image = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image):
        print(f"测试图像不存在: {test_image}")
        return

    # 加载图像
    image = cv2.imread(test_image)
    if image is None:
        print("无法加载图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]} 像素")

    # 初始化OCR引擎
    ocr_engine = None
    ocr_type = None

    try:
        import easyocr
        ocr_engine = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        ocr_type = 'easyocr'
        print("✓ EasyOCR引擎初始化成功")
    except ImportError:
        try:
            import ddddocr
            ocr_engine = ddddocr.DdddOcr()
            ocr_type = 'ddddocr'
            print("✓ ddddocr引擎初始化成功")
        except ImportError:
            print("✗ 未找到可用的OCR引擎")
            return

    # 执行OCR识别
    print("\n执行OCR识别...")

    try:
        if ocr_type == 'easyocr':
            results = ocr_engine.readtext(image)

            print(f"\nEasyOCR识别结果 ({len(results)}个):")
            print("-" * 50)

            for i, (bbox, text, confidence) in enumerate(results):
                # 计算边界框
                points = np.array(bbox, dtype=np.int32)
                x_coords = points[:, 0]
                y_coords = points[:, 1]
                x1, y1 = np.min(x_coords), np.min(y_coords)
                x2, y2 = np.max(x_coords), np.max(y_coords)

                # 检测语言类型
                import re
                has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
                has_english = bool(re.search(r'[a-zA-Z]', text))
                has_numbers = bool(re.search(r'\d', text))

                if has_chinese and has_english:
                    language = '中英混合'
                elif has_chinese:
                    language = '中文'
                elif has_english:
                    language = '英文'
                elif has_numbers:
                    language = '数字'
                else:
                    language = '未知'

                # 安全显示文字内容
                try:
                    display_text = text.strip()
                    # 确保可以正确显示中文
                    if has_chinese:
                        # 验证中文字符
                        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
                        print(f"  {i+1:2d}. [{language:6s}] '{display_text}' (置信度:{confidence:.3f})")
                        if chinese_chars:
                            print(f"      中文字符: {chinese_chars}")
                    else:
                        print(f"  {i+1:2d}. [{language:6s}] '{display_text}' (置信度:{confidence:.3f})")

                    print(f"      位置: ({x1},{y1})-({x2},{y2})")

                except UnicodeError as e:
                    print(f"  {i+1:2d}. [编码错误] 无法显示文字内容 - {e}")
                    print(f"      原始bytes: {text.encode('utf-8', errors='ignore')}")

        elif ocr_type == 'ddddocr':
            # ddddocr需要分割文字区域
            print("使用ddddocr进行文字识别...")

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 形态学操作检测文字区域
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # 二值化
            _, binary = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            print(f"\nddddocr识别结果:")
            print("-" * 50)

            text_count = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                area = w * h

                # 文字区域特征过滤
                if (1.5 < aspect_ratio < 15 and
                    500 < area < 30000 and
                    w > 30 and h > 15):

                    # 提取文字区域进行OCR
                    roi = image[y:y+h, x:x+w]

                    try:
                        _, buffer = cv2.imencode('.png', roi)
                        text = ocr_engine.classification(buffer.tobytes()).strip()

                        if len(text) > 0:
                            text_count += 1

                            # 检测语言
                            import re
                            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
                            has_english = bool(re.search(r'[a-zA-Z]', text))

                            if has_chinese:
                                language = '中文'
                            elif has_english:
                                language = '英文'
                            else:
                                language = '其他'

                            print(f"  {text_count:2d}. [{language:6s}] '{text}'")
                            print(f"      位置: ({x},{y})-({x+w},{y+h})")

                    except Exception as e:
                        print(f"      ddddocr识别失败: {e}")

        # 创建可视化结果
        print(f"\n创建中文OCR可视化结果...")
        result_image = image.copy()

        if ocr_type == 'easyocr':
            # 绘制EasyOCR结果
            for i, (bbox, text, confidence) in enumerate(results):
                if confidence > 0.3:  # 只显示高置信度结果
                    points = np.array(bbox, dtype=np.int32)
                    x_coords = points[:, 0]
                    y_coords = points[:, 1]
                    x1, y1 = np.min(x_coords), np.min(y_coords)
                    x2, y2 = np.max(x_coords), np.max(y_coords)

                    # 检测语言选择颜色
                    import re
                    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))

                    if has_chinese:
                        color = (0, 255, 128)  # 绿色 - 中文
                    else:
                        color = (128, 255, 0)  # 黄绿色 - 其他

                    # 绘制边界框
                    cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)

                    # 添加标签
                    label = f"T{i+1}"
                    cv2.putText(result_image, label, (x1, y1-5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                    # 添加置信度
                    conf_text = f"{confidence:.2f}"
                    cv2.putText(result_image, conf_text, (x2-40, y2+15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # 保存结果
        output_path = "../../chinese_ocr_test.png"
        cv2.imwrite(output_path, result_image)

        print(f"\n中文OCR测试结果已保存: {output_path}")

        # 测试不同的中文显示方法
        print(f"\n测试中文显示编码:")
        print("-" * 30)

        test_texts = ["本次行程", "总里程", "功率"]
        for test_text in test_texts:
            try:
                print(f"原始文字: {test_text}")
                print(f"UTF-8编码: {test_text.encode('utf-8')}")
                print(f"UTF-8解码: {test_text.encode('utf-8').decode('utf-8')}")
                print(f"Unicode码点: {[ord(c) for c in test_text]}")
                print("-" * 20)
            except Exception as e:
                print(f"编码测试失败: {e}")

    except Exception as e:
        print(f"OCR识别失败: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n中文OCR专项测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_chinese_ocr()