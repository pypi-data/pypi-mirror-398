#!/usr/bin/env python3
"""
可视化检测结果 - 用线框标记所有检测到的元素
"""

import cv2
import numpy as np
import os
import sys

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_detector import AdvancedDetector
from basic_detector import BasicDetector

def draw_detection_results():
    """绘制检测结果的可视化标记"""

    print("=" * 60)
    print("可视化检测结果")
    print("=" * 60)

    # 初始化检测器
    print("初始化检测器...")
    advanced_detector = AdvancedDetector()
    basic_detector = BasicDetector()

    # 测试图像路径
    test_image = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image):
        print(f"测试图像不存在: {test_image}")
        return

    print(f"加载图像: {test_image}")

    # 加载图像
    image = cv2.imread(test_image)
    if image is None:
        print("无法加载图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]} 像素")

    # 创建结果图像副本
    result_image = image.copy()

    # 执行所有检测
    print("\n执行检测...")

    # 1. 基础检测
    basic_result = basic_detector.detect_all_elements(image)
    basic_circles = basic_result['detected_elements']['circles']
    basic_rectangles = basic_result['detected_elements']['rectangles']

    # 2. 高级检测
    enhanced_circles = advanced_detector._detect_enhanced_circles(image)
    enhanced_rectangles = advanced_detector._detect_enhanced_rectangles(image)
    irregular_shapes = advanced_detector._detect_irregular_shapes(image)

    # 3. 特征点检测
    sift_kp, sift_desc = advanced_detector.detect_features_sift(image)
    orb_kp, orb_desc = advanced_detector.detect_features_orb(image)

    print(f"检测完成:")
    print(f"  基础圆形: {len(basic_circles)}")
    print(f"  增强圆形: {len(enhanced_circles)}")
    print(f"  增强矩形: {len(enhanced_rectangles)}")
    print(f"  不规则形状: {len(irregular_shapes)}")
    print(f"  SIFT特征点: {len(sift_kp)}")
    print(f"  ORB特征点: {len(orb_kp)}")

    # 定义颜色方案
    colors = {
        'basic_circle': (0, 255, 0),      # 绿色 - 基础圆形
        'enhanced_circle': (0, 255, 255), # 黄色 - 增强圆形
        'enhanced_rect': (255, 0, 0),     # 蓝色 - 增强矩形
        'triangle': (0, 0, 255),          # 红色 - 三角形
        'pentagon': (255, 0, 255),        # 紫色 - 五边形
        'hexagon': (255, 255, 0),         # 青色 - 六边形
        'square': (128, 0, 128),          # 深紫色 - 正方形
        'irregular': (255, 128, 0),       # 橙色 - 不规则形状
        'other': (128, 128, 128),         # 灰色 - 其他形状
        'sift': (0, 255, 0),              # 绿色 - SIFT特征点
        'orb': (0, 0, 255)                # 红色 - ORB特征点
    }

    element_count = 0

    # 绘制基础检测的圆形 - 绿色粗线框
    print(f"\n绘制基础圆形检测结果...")
    for i, circle in enumerate(basic_circles):
        center = circle['center']
        radius = circle['radius']

        # 绘制圆形边框
        cv2.circle(result_image, center, radius, colors['basic_circle'], 3)
        cv2.circle(result_image, center, 2, colors['basic_circle'], -1)

        # 标记编号
        cv2.putText(result_image, f"BC{i+1}",
                   (center[0] - 15, center[1] - radius - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors['basic_circle'], 2)
        element_count += 1

    # 绘制增强检测的圆形 - 黄色细线框
    print(f"绘制增强圆形检测结果...")
    for i, circle in enumerate(enhanced_circles):
        center = circle['center']
        radius = circle['radius']

        # 检查是否与基础检测重复
        is_duplicate = False
        for basic_circle in basic_circles:
            bc_center = basic_circle['center']
            bc_radius = basic_circle['radius']
            dist = np.sqrt((center[0] - bc_center[0])**2 + (center[1] - bc_center[1])**2)
            if dist < max(radius, bc_radius) * 0.7:
                is_duplicate = True
                break

        if not is_duplicate:
            # 绘制圆形边框
            cv2.circle(result_image, center, radius, colors['enhanced_circle'], 2)
            cv2.circle(result_image, center, 1, colors['enhanced_circle'], -1)

            # 标记编号
            cv2.putText(result_image, f"EC{i+1}",
                       (center[0] - 15, center[1] + radius + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, colors['enhanced_circle'], 1)
            element_count += 1

    # 绘制增强检测的矩形 - 蓝色线框
    print(f"绘制增强矩形检测结果...")
    for i, rect in enumerate(enhanced_rectangles):
        bounds = rect['bounds']
        x1, y1, x2, y2 = bounds

        # 绘制矩形边框
        cv2.rectangle(result_image, (x1, y1), (x2, y2), colors['enhanced_rect'], 2)

        # 标记编号
        cv2.putText(result_image, f"ER{i+1}",
                   (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, colors['enhanced_rect'], 1)
        element_count += 1

    # 绘制不规则形状 - 根据类型使用不同颜色
    print(f"绘制不规则形状检测结果...")
    for i, shape in enumerate(irregular_shapes):
        bounds = shape['bounds']
        x1, y1, x2, y2 = bounds
        shape_type = shape['type']

        # 选择颜色
        if shape_type == 'triangle':
            color = colors['triangle']
        elif shape_type == 'pentagon':
            color = colors['pentagon']
        elif shape_type == 'hexagon':
            color = colors['hexagon']
        elif shape_type == 'square':
            color = colors['square']
        elif 'irregular' in shape_type:
            color = colors['irregular']
        else:
            color = colors['other']

        # 绘制边界框
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)

        # 标记类型和编号
        label = f"{shape_type[:3]}{i+1}"
        cv2.putText(result_image, label,
                   (x1, y2 + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        element_count += 1

    # 绘制SIFT特征点 - 绿色小圆点
    print(f"绘制SIFT特征点...")
    for i, kp in enumerate(sift_kp[:20]):  # 只显示前20个
        x, y = int(kp.pt[0]), int(kp.pt[1])
        cv2.circle(result_image, (x, y), 3, colors['sift'], 1)

    # 绘制ORB特征点 - 红色小方块
    print(f"绘制ORB特征点...")
    for i, kp in enumerate(orb_kp[:20]):  # 只显示前20个
        x, y = int(kp.pt[0]), int(kp.pt[1])
        cv2.rectangle(result_image, (x-2, y-2), (x+2, y+2), colors['orb'], 1)

    # 添加图例
    print(f"添加图例...")
    legend_y = 30
    legend_x = 10
    legend_items = [
        ("BC - 基础圆形", colors['basic_circle']),
        ("EC - 增强圆形", colors['enhanced_circle']),
        ("ER - 增强矩形", colors['enhanced_rect']),
        ("tri - 三角形", colors['triangle']),
        ("pen - 五边形", colors['pentagon']),
        ("hex - 六边形", colors['hexagon']),
        ("squ - 正方形", colors['square']),
        ("irr - 不规则", colors['irregular']),
        ("○ - SIFT特征点", colors['sift']),
        ("□ - ORB特征点", colors['orb'])
    ]

    for i, (label, color) in enumerate(legend_items):
        y_pos = legend_y + i * 25
        cv2.putText(result_image, label, (legend_x, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # 添加统计信息
    stats_text = [
        f"总检测元素: {element_count}",
        f"SIFT特征: {len(sift_kp)}",
        f"ORB特征: {len(orb_kp)}",
        f"图像尺寸: {image.shape[1]}x{image.shape[0]}"
    ]

    stats_x = image.shape[1] - 200
    for i, text in enumerate(stats_text):
        y_pos = 30 + i * 25
        cv2.putText(result_image, text, (stats_x, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # 保存结果图像
    output_path = "../../detection_visualization.png"
    cv2.imwrite(output_path, result_image)

    print(f"\n可视化结果已保存: {output_path}")
    print(f"总共标记了 {element_count} 个检测元素")
    print(f"SIFT特征点: {len(sift_kp)} (显示前20个)")
    print(f"ORB特征点: {len(orb_kp)} (显示前20个)")

    # 尝试显示图像 (如果可能)
    try:
        # 缩放图像以适应显示
        height, width = result_image.shape[:2]
        if width > 1200:
            scale = 1200 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            display_image = cv2.resize(result_image, (new_width, new_height))
        else:
            display_image = result_image

        cv2.imshow('检测结果可视化', display_image)
        print(f"\n图像窗口已打开，按任意键关闭...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print(f"无法显示图像窗口，但图像已保存到文件")

    print(f"\n可视化完成!")
    print("="*60)

if __name__ == "__main__":
    draw_detection_results()