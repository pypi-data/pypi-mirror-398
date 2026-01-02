#!/usr/bin/env python3
"""
测试精确圆形检测器
"""

import cv2
import numpy as np
import os
import sys

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from precise_circle_detector import PreciseCircleDetector

def test_precise_circle_detection():
    """测试精确圆形检测"""

    print("=" * 60)
    print("精确圆形检测测试")
    print("=" * 60)

    # 初始化精确检测器
    detector = PreciseCircleDetector()

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

    # 执行精确圆形检测
    print("\n执行精确圆形检测...")
    circles = detector.detect_dashboard_circles(image)

    print(f"检测结果: 发现 {len(circles)} 个高质量圆形元素")

    # 显示详细结果
    print(f"\n检测到的圆形元素详情:")
    print("-" * 60)

    for i, circle in enumerate(circles):
        center = circle['center']
        radius = circle['radius']
        validation_score = circle.get('validation_score', 0)
        semantic_type = circle.get('semantic_type', 'unknown')
        functional_category = circle.get('functional_category', 'unknown')
        semantic_confidence = circle.get('semantic_confidence', 0)
        size_category = circle.get('size_category', 'unknown')
        position_category = circle.get('position_category', 'unknown')

        print(f"\n圆形 {i+1}:")
        print(f"  位置: 中心({center[0]},{center[1]}), 半径{radius}")
        print(f"  验证评分: {validation_score:.3f}")
        print(f"  语义类型: {semantic_type}")
        print(f"  功能分类: {functional_category}")
        print(f"  语义置信度: {semantic_confidence:.3f}")
        print(f"  尺寸分类: {size_category}")
        print(f"  位置分类: {position_category}")

    # 创建可视化结果
    print(f"\n创建可视化结果...")
    result_image = image.copy()

    # 定义不同类型的颜色
    type_colors = {
        'main_gauge': (0, 255, 0),          # 绿色 - 主仪表
        'secondary_gauge': (0, 255, 255),   # 黄色 - 次级仪表
        'auxiliary_gauge': (255, 0, 255),   # 紫色 - 辅助仪表
        'control_button': (255, 0, 0),      # 蓝色 - 控制按钮
        'active_indicator': (0, 0, 255),    # 红色 - 活动指示器
        'inactive_indicator': (128, 128, 128),  # 灰色 - 非活动指示器
        'small_button': (0, 128, 255),      # 橙色 - 小按钮
        'micro_indicator': (255, 255, 0),   # 青色 - 微指示器
        'unknown_circle': (255, 255, 255)   # 白色 - 未知
    }

    # 绘制检测结果
    for i, circle in enumerate(circles):
        center = circle['center']
        radius = circle['radius']
        semantic_type = circle.get('semantic_type', 'unknown_circle')
        validation_score = circle.get('validation_score', 0)

        # 选择颜色
        color = type_colors.get(semantic_type, (255, 255, 255))

        # 根据验证评分调整线条粗细
        thickness = max(1, int(validation_score * 4))

        # 绘制圆形
        cv2.circle(result_image, center, radius, color, thickness)
        cv2.circle(result_image, center, 2, color, -1)

        # 添加标签
        label = f"{semantic_type[:8]}{i+1}"
        label_pos = (center[0] - 20, center[1] - radius - 10)

        cv2.putText(result_image, label, label_pos,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # 添加评分
        score_text = f"{validation_score:.2f}"
        score_pos = (center[0] - 15, center[1] + radius + 15)
        cv2.putText(result_image, score_text, score_pos,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

    # 添加图例
    print(f"添加图例...")
    legend_y = 30
    legend_items = [
        ("main_gauge - 主仪表", type_colors['main_gauge']),
        ("auxiliary_gauge - 辅助仪表", type_colors['auxiliary_gauge']),
        ("control_button - 控制按钮", type_colors['control_button']),
        ("active_indicator - 活动指示器", type_colors['active_indicator']),
        ("inactive_indicator - 非活动指示器", type_colors['inactive_indicator'])
    ]

    for i, (label, color) in enumerate(legend_items):
        y_pos = legend_y + i * 20
        cv2.putText(result_image, label, (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # 添加统计信息
    stats_text = [
        f"总计: {len(circles)} 个圆形",
        f"平均评分: {np.mean([c.get('validation_score', 0) for c in circles]):.3f}" if circles else "平均评分: 0",
        f"平均置信度: {np.mean([c.get('semantic_confidence', 0) for c in circles]):.3f}" if circles else "平均置信度: 0"
    ]

    stats_x = image.shape[1] - 200
    for i, text in enumerate(stats_text):
        y_pos = 30 + i * 20
        cv2.putText(result_image, text, (stats_x, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # 保存结果
    output_path = "../../precise_circle_detection.png"
    cv2.imwrite(output_path, result_image)

    print(f"\n精确圆形检测结果已保存: {output_path}")

    # 统计分析
    print(f"\n统计分析:")
    print("-" * 40)

    if circles:
        # 按语义类型分组统计
        type_counts = {}
        for circle in circles:
            semantic_type = circle.get('semantic_type', 'unknown')
            type_counts[semantic_type] = type_counts.get(semantic_type, 0) + 1

        print("语义类型分布:")
        for type_name, count in type_counts.items():
            print(f"  {type_name}: {count} 个")

        # 按大小分组统计
        size_counts = {}
        for circle in circles:
            size_category = circle.get('size_category', 'unknown')
            size_counts[size_category] = size_counts.get(size_category, 0) + 1

        print("\n尺寸分布:")
        for size_name, count in size_counts.items():
            print(f"  {size_name}: {count} 个")

        # 质量统计
        validation_scores = [c.get('validation_score', 0) for c in circles]
        semantic_confidences = [c.get('semantic_confidence', 0) for c in circles]

        print(f"\n质量统计:")
        print(f"  验证评分范围: {min(validation_scores):.3f} - {max(validation_scores):.3f}")
        print(f"  语义置信度范围: {min(semantic_confidences):.3f} - {max(semantic_confidences):.3f}")
        print(f"  高质量元素 (评分>0.8): {sum(1 for s in validation_scores if s > 0.8)} 个")

    else:
        print("未检测到有效圆形元素")

    print(f"\n精确圆形检测测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_precise_circle_detection()