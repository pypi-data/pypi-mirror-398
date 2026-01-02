#!/usr/bin/env python3
"""
综合检测测试 - 展示所有检测手段的线框标记结果
"""

import cv2
import numpy as np
import os
import sys

# 添加当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector

def test_comprehensive_detection():
    """测试综合检测并生成线框标记可视化"""

    print("=" * 60)
    print("综合检测测试 - 所有检测手段")
    print("=" * 60)

    # 初始化综合检测器
    detector = ComprehensiveDetector()

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

    # 执行综合检测
    print("\n执行综合检测...")
    result = detector.comprehensive_detection(image)

    if not result['success']:
        print(f"检测失败: {result.get('error', '未知错误')}")
        return

    # 提取检测结果
    circles = result['elements']['circles']
    rectangles = result['elements']['rectangles']
    text_regions = result['elements']['text_regions']
    features = result['features']
    stats = result['statistics']

    print(f"\n检测结果统计:")
    print(f"  圆形元素: {stats['circle_count']} 个")
    print(f"  矩形元素: {stats['rectangle_count']} 个")
    print(f"  文字区域: {stats['text_count']} 个")
    print(f"  SIFT特征点: {stats['sift_features']} 个")
    print(f"  ORB特征点: {stats['orb_features']} 个")
    print(f"  总耗时: {result['detection_time']} 秒")

    # 详细显示检测结果
    print(f"\n详细检测结果:")
    print("-" * 50)

    if circles:
        print(f"\n圆形元素 ({len(circles)}个):")
        for i, circle in enumerate(circles):
            center = circle['center']
            radius = circle['radius']
            semantic_type = circle.get('semantic_type', 'unknown')
            confidence = circle.get('validation_score', 0)
            print(f"  {i+1}. 中心({center[0]},{center[1]}) r={radius} - {semantic_type} (评分:{confidence:.3f})")

    if rectangles:
        print(f"\n矩形元素 ({len(rectangles)}个):")
        for i, rect in enumerate(rectangles):
            bounds = rect['bounds']
            semantic_type = rect.get('semantic_type', 'unknown')
            confidence = rect.get('confidence', 0)
            print(f"  {i+1}. 位置({bounds[0]},{bounds[1]})-({bounds[2]},{bounds[3]}) - {semantic_type} (置信度:{confidence:.3f})")

    if text_regions:
        print(f"\n文字区域 ({len(text_regions)}个):")
        for i, text in enumerate(text_regions):
            bounds = text['bounds']
            content = text['text']
            confidence = text.get('confidence', 0)
            language = text.get('language', 'unknown')
            # 修复中文显示问题
            try:
                display_content = content.encode('utf-8').decode('utf-8')
            except:
                display_content = content
            print(f"  {i+1}. '{display_content}' - {language} (置信度:{confidence:.3f}) 位置({bounds[0]},{bounds[1]})")

    # 创建综合可视化结果
    print(f"\n创建综合可视化标记...")
    result_image = image.copy()

    # 定义颜色方案
    colors = {
        # 圆形类型颜色
        'main_gauge': (0, 255, 0),           # 绿色 - 主仪表
        'auxiliary_gauge': (255, 0, 255),    # 紫色 - 辅助仪表
        'control_button': (255, 0, 0),       # 蓝色 - 控制按钮
        'active_indicator': (0, 0, 255),     # 红色 - 活动指示器
        'inactive_indicator': (128, 128, 128), # 灰色 - 非活动指示器
        'small_button': (0, 128, 255),       # 橙色 - 小按钮
        'micro_indicator': (255, 255, 0),    # 青色 - 微指示器

        # 矩形类型颜色
        'horizontal_panel': (0, 255, 255),   # 黄色 - 水平面板
        'vertical_panel': (255, 128, 0),     # 橙蓝色 - 垂直面板
        'rectangular_panel': (128, 0, 255),  # 紫粉色 - 矩形面板
        'square_panel': (255, 255, 128),     # 浅黄色 - 正方形面板

        # 文字和特征点颜色
        'text_chinese': (0, 255, 128),       # 绿青色 - 中文
        'text_english': (128, 255, 0),       # 黄绿色 - 英文
        'text_numeric': (255, 128, 128),     # 粉红色 - 数字
        'text_mixed': (128, 255, 255),       # 浅青色 - 混合

        'sift_point': (0, 255, 0),           # 绿色 - SIFT特征点
        'orb_point': (0, 0, 255),            # 红色 - ORB特征点

        'unknown': (255, 255, 255)           # 白色 - 未知类型
    }

    # 1. 绘制圆形元素
    for i, circle in enumerate(circles):
        center = circle['center']
        radius = circle['radius']
        semantic_type = circle.get('semantic_type', 'unknown')
        validation_score = circle.get('validation_score', 0)

        color = colors.get(semantic_type, colors['unknown'])
        thickness = max(2, int(validation_score * 4))

        # 绘制圆形
        cv2.circle(result_image, center, radius, color, thickness)
        cv2.circle(result_image, center, 3, color, -1)

        # 添加标签
        label = f"C{i+1}:{semantic_type[:4]}"
        cv2.putText(result_image, label,
                   (center[0] - 25, center[1] - radius - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # 添加评分
        score_text = f"{validation_score:.2f}"
        cv2.putText(result_image, score_text,
                   (center[0] - 15, center[1] + radius + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

    # 2. 绘制矩形元素
    for i, rect in enumerate(rectangles):
        bounds = rect['bounds']
        x1, y1, x2, y2 = bounds
        semantic_type = rect.get('semantic_type', 'unknown')
        confidence = rect.get('confidence', 0)

        color = colors.get(semantic_type, colors['unknown'])
        thickness = max(1, int(confidence * 3))

        # 绘制矩形
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, thickness)

        # 添加标签
        label = f"R{i+1}:{semantic_type[:4]}"
        cv2.putText(result_image, label, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # 添加置信度
        conf_text = f"{confidence:.2f}"
        cv2.putText(result_image, conf_text, (x2 - 40, y2 + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

    # 3. 绘制文字区域
    for i, text_region in enumerate(text_regions):
        bounds = text_region['bounds']
        x1, y1, x2, y2 = bounds
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)

        # 选择颜色
        if language == 'chinese':
            color = colors['text_chinese']
        elif language == 'english':
            color = colors['text_english']
        elif language == 'numeric':
            color = colors['text_numeric']
        elif language == 'mixed':
            color = colors['text_mixed']
        else:
            color = colors['unknown']

        thickness = max(1, int(confidence * 2))

        # 绘制文字边界框
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, thickness)

        # 添加文字内容标签
        label = f"T{i+1}:{content[:8]}"
        cv2.putText(result_image, label, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

    # 4. 绘制特征点 (只显示一部分避免过于密集)
    if 'sift_keypoints' in features:
        sift_kp = features['sift_keypoints']
        for i, kp in enumerate(sift_kp[:15]):  # 只显示前15个
            x, y = int(kp.pt[0]), int(kp.pt[1])
            cv2.circle(result_image, (x, y), 3, colors['sift_point'], 1)
            cv2.circle(result_image, (x, y), 1, colors['sift_point'], -1)

    if 'orb_keypoints' in features:
        orb_kp = features['orb_keypoints']
        for i, kp in enumerate(orb_kp[:15]):  # 只显示前15个
            x, y = int(kp.pt[0]), int(kp.pt[1])
            cv2.rectangle(result_image, (x-2, y-2), (x+2, y+2), colors['orb_point'], 1)

    # 5. 添加图例
    print(f"添加图例和统计信息...")
    legend_y = 20
    legend_items = [
        ("C - 圆形检测", colors['auxiliary_gauge']),
        ("R - 矩形检测", colors['rectangular_panel']),
        ("T - 文字识别", colors['text_chinese']),
        ("○ - SIFT特征", colors['sift_point']),
        ("□ - ORB特征", colors['orb_point'])
    ]

    for i, (label, color) in enumerate(legend_items):
        y_pos = legend_y + i * 18
        cv2.putText(result_image, label, (10, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # 6. 添加统计信息
    stats_text = [
        f"圆形: {stats['circle_count']}",
        f"矩形: {stats['rectangle_count']}",
        f"文字: {stats['text_count']}",
        f"SIFT: {stats['sift_features']}",
        f"ORB: {stats['orb_features']}",
        f"耗时: {result['detection_time']}s"
    ]

    stats_x = image.shape[1] - 150
    for i, text in enumerate(stats_text):
        y_pos = 20 + i * 18
        cv2.putText(result_image, text, (stats_x, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # 保存综合检测结果
    output_path = "../../comprehensive_detection_result.png"
    cv2.imwrite(output_path, result_image)

    print(f"\n综合检测可视化结果已保存: {output_path}")

    # 显示最终统计
    print(f"\n最终统计:")
    print("="*50)
    print(f"总检测元素: {result['total_elements']} 个")
    print(f"检测方法覆盖: 圆形+矩形+OCR+特征点")
    print(f"处理性能: {result['detection_time']:.3f} 秒")

    if circles:
        avg_circle_score = np.mean([c.get('validation_score', 0) for c in circles])
        print(f"圆形平均质量评分: {avg_circle_score:.3f}")

    if rectangles:
        avg_rect_confidence = np.mean([r.get('confidence', 0) for r in rectangles])
        print(f"矩形平均置信度: {avg_rect_confidence:.3f}")

    if text_regions:
        avg_text_confidence = np.mean([t.get('confidence', 0) for t in text_regions])
        print(f"文字平均置信度: {avg_text_confidence:.3f}")

    print(f"\n综合检测测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_comprehensive_detection()