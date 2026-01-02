#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pixel Level Lightning Finder - 像素级闪电查找器
直接分析精确区域内的像素模式
"""

import cv2
import numpy as np
import os

def analyze_lightning_area():
    """在精确区域内进行像素级分析"""

    # 加载图像
    test_image = "../../resources/20250910-100334.png"
    if not os.path.exists(test_image):
        print(f"图像未找到: {test_image}")
        return

    image = cv2.imread(test_image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 精确的闪电搜索区域
    x_min, x_max = 75, 95
    y_min, y_max = 160, 185

    roi = gray[y_min:y_max, x_min:x_max]
    roi_color = image[y_min:y_max, x_min:x_max]

    print(f"分析区域: ({x_min},{y_min}) 到 ({x_max},{y_max})")
    print(f"区域大小: {roi.shape}")

    # 方法1: 寻找白色像素集群
    print("\\n方法1: 白色像素分析")
    _, binary = cv2.threshold(roi, 200, 255, cv2.THRESH_BINARY)

    # 找到白色像素的位置
    white_pixels = np.where(binary == 255)
    if len(white_pixels[0]) > 0:
        print(f"找到 {len(white_pixels[0])} 个白色像素")

        # 分析白色像素的分布
        y_coords = white_pixels[0]
        x_coords = white_pixels[1]

        if len(x_coords) > 10:  # 有足够的像素
            # 计算边界
            min_y, max_y = np.min(y_coords), np.max(y_coords)
            min_x, max_x = np.min(x_coords), np.max(x_coords)

            width = max_x - min_x + 1
            height = max_y - min_y + 1

            print(f"白色区域边界: ({min_x},{min_y}) 到 ({max_x},{max_y})")
            print(f"白色区域大小: {width}x{height}")

            # 转换回全图坐标
            global_x = x_min + min_x + width // 2
            global_y = y_min + min_y + height // 2

            print(f"推测闪电中心: ({global_x}, {global_y})")

            # 检查这个区域是否像闪电
            center_x = min_x + width // 2
            center_y = min_y + height // 2

            if 5 <= width <= 15 and 10 <= height <= 20:
                aspect_ratio = height / width
                if 1.0 <= aspect_ratio <= 3.0:
                    print(f"✓ 符合闪电图标特征: 宽{width}, 高{height}, 比例{aspect_ratio:.2f}")

                    # 在原图上标记
                    result_image = image.copy()
                    cv2.rectangle(result_image,
                                (x_min + min_x, y_min + min_y),
                                (x_min + max_x, y_min + max_y),
                                (0, 255, 255), 2)
                    cv2.circle(result_image, (global_x, global_y), 3, (0, 255, 255), -1)
                    cv2.putText(result_image, f"LIGHTNING ({global_x},{global_y})",
                              (global_x + 10, global_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

                    # 保存结果
                    cv2.imwrite("../../pixel_level_lightning.png", result_image)
                    print("结果已保存: pixel_level_lightning.png")

                    return (global_x, global_y)

    # 方法2: 轮廓分析
    print("\\n方法2: 轮廓分析")
    edges = cv2.Canny(roi, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if 20 <= area <= 150:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = h / w if w > 0 else 0

            if 1.0 <= aspect_ratio <= 3.0:
                global_x = x_min + x + w // 2
                global_y = y_min + y + h // 2

                print(f"轮廓 {i}: 面积{area:.1f}, 位置({x},{y}), 大小{w}x{h}, 比例{aspect_ratio:.2f}")
                print(f"  全图坐标: ({global_x}, {global_y})")

                return (global_x, global_y)

    # 方法3: 直接像素扫描
    print("\\n方法3: 像素扫描")

    # 创建详细的ROI分析图
    analysis_image = np.zeros((roi.shape[0] * 10, roi.shape[1] * 10, 3), dtype=np.uint8)

    for y in range(roi.shape[0]):
        for x in range(roi.shape[1]):
            pixel_val = roi[y, x]
            color = (int(pixel_val), int(pixel_val), int(pixel_val))

            # 放大10倍显示
            cv2.rectangle(analysis_image,
                         (x * 10, y * 10),
                         ((x + 1) * 10, (y + 1) * 10),
                         color, -1)

            # 标记白色像素
            if pixel_val > 200:
                cv2.rectangle(analysis_image,
                             (x * 10, y * 10),
                             ((x + 1) * 10, (y + 1) * 10),
                             (0, 255, 255), 1)
                cv2.putText(analysis_image, f"{pixel_val}",
                           (x * 10 + 1, y * 10 + 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.2, (255, 255, 255), 1)

    cv2.imwrite("../../lightning_pixel_analysis.png", analysis_image)
    print("像素分析图已保存: lightning_pixel_analysis.png")

    return None

if __name__ == "__main__":
    result = analyze_lightning_area()
    if result:
        print(f"\\n找到闪电图标位置: {result}")
    else:
        print("\\n未找到明确的闪电图标")