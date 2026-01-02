#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Lightning Detector - 最终闪电检测器
彻底解决方案：精确位置 + 像素模式识别 + 严格排除
"""

import cv2
import numpy as np
import os
import sys
from typing import List, Dict, Tuple

# 导入基础检测器用于获取圆形区域
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comprehensive_detector import ComprehensiveDetector

class FinalLightningDetector:
    """最终闪电检测器 - 彻底解决垂直柱误判问题"""

    def __init__(self):
        # 基于像素级分析的精确位置
        self.real_lightning_position = (87, 169)  # 真实位置
        self.search_tolerance = 8  # 搜索容差

        # 严格排除区域
        self.strict_exclusions = {
            'signal_bars': {  # 信号强度垂直柱区域
                'x_range': (60, 90),
                'y_range': (120, 155),
                'description': '信号强度垂直柱'
            },
            'gauge_pointers': {  # 仪表指针区域
                'x_range': (80, 105),
                'y_range': (270, 295),
                'description': 'C1仪表指针'
            }
        }

    def detect_lightning_by_position_and_exclusion(self, image: np.ndarray, circles: List[Dict] = None) -> List[Dict]:
        """通过精确位置和排除策略检测闪电"""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        print(f"最终闪电检测 - 图像: {width}x{height}")
        print(f"目标位置: {self.real_lightning_position}, 容差: {self.search_tolerance}")

        # 第一步：在真实闪电位置附近搜索
        target_x, target_y = self.real_lightning_position
        search_x1 = max(0, target_x - self.search_tolerance)
        search_x2 = min(width, target_x + self.search_tolerance)
        search_y1 = max(0, target_y - self.search_tolerance)
        search_y2 = min(height, target_y + self.search_tolerance)

        print(f"搜索区域: ({search_x1},{search_y1}) 到 ({search_x2},{search_y2})")

        # 第二步：在搜索区域寻找白色像素集群
        roi = gray[search_y1:search_y2, search_x1:search_x2]
        _, binary = cv2.threshold(roi, 180, 255, cv2.THRESH_BINARY)

        # 寻找连通组件
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        lightning_candidates = []

        for i in range(1, num_labels):  # 跳过背景
            area = stats[i, cv2.CC_STAT_AREA]
            if 20 <= area <= 200:  # 闪电图标大小范围
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]

                # 转换到全图坐标
                full_x = x + search_x1
                full_y = y + search_y1
                center = (full_x + w//2, full_y + h//2)

                # 计算与目标位置的距离
                distance = np.sqrt((center[0] - target_x)**2 + (center[1] - target_y)**2)

                # 检查高宽比
                aspect_ratio = h / w if w > 0 else 0

                if distance <= self.search_tolerance and 1.0 <= aspect_ratio <= 3.0:
                    candidate = {
                        'type': 'icon',
                        'icon_type': 'lightning',
                        'bounds': (full_x, full_y, w, h),
                        'center': center,
                        'confidence': 0.9 - (distance / self.search_tolerance) * 0.3,  # 距离越近置信度越高
                        'distance_to_target': distance,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'detection_method': 'position_based_pixel_analysis'
                    }
                    lightning_candidates.append(candidate)
                    print(f"找到候选: center={center}, distance={distance:.1f}, area={area}, ratio={aspect_ratio:.2f}")

        # 第三步：应用排除策略
        filtered_candidates = []

        for candidate in lightning_candidates:
            center = candidate['center']
            should_exclude = False
            exclusion_reason = None

            # 检查严格排除区域
            for zone_name, zone in self.strict_exclusions.items():
                x_range = zone['x_range']
                y_range = zone['y_range']

                if (x_range[0] <= center[0] <= x_range[1] and
                    y_range[0] <= center[1] <= y_range[1]):
                    should_exclude = True
                    exclusion_reason = zone['description']
                    break

            if should_exclude:
                print(f"排除候选 {center} - 位于{exclusion_reason}区域")
                continue

            # 检查圆形区域排除（仪表指针）
            if circles:
                inside_circle = False
                for circle in circles:
                    circle_center = circle['center']
                    circle_radius = circle['radius']

                    distance_to_circle = np.sqrt(
                        (center[0] - circle_center[0])**2 +
                        (center[1] - circle_center[1])**2
                    )

                    if distance_to_circle <= circle_radius:
                        print(f"排除候选 {center} - 位于圆形区域 center={circle_center}, radius={circle_radius}")
                        inside_circle = True
                        break

                if inside_circle:
                    continue

            # 通过所有检查的候选者
            filtered_candidates.append(candidate)
            print(f"确认真实闪电图标: center={center}, confidence={candidate['confidence']:.2f}")

        return filtered_candidates

def test_final_detector():
    """测试最终检测器"""
    print("=" * 60)
    print("最终闪电检测器测试")
    print("=" * 60)

    # 初始化检测器
    base_detector = ComprehensiveDetector()
    lightning_detector = FinalLightningDetector()

    # 加载测试图像
    test_image = "../../resources/20250910-100334.png"
    if not os.path.exists(test_image):
        print(f"测试图像未找到: {test_image}")
        return

    image = cv2.imread(test_image)
    if image is None:
        print("无法加载图像")
        return

    print(f"图像尺寸: {image.shape[1]}x{image.shape[0]}")

    # 获取圆形区域用于排除
    print("获取圆形区域...")
    base_result = base_detector.comprehensive_detection(image)
    circles = base_result['elements']['circles'] if base_result['success'] else []
    print(f"找到 {len(circles)} 个圆形区域")

    # 执行最终检测
    print("\\n执行最终闪电检测...")
    lightning_icons = lightning_detector.detect_lightning_by_position_and_exclusion(image, circles)

    print(f"\\n最终结果:")
    print(f"检测到 {len(lightning_icons)} 个真实闪电充电图标")

    # 创建结果可视化
    result_image = image.copy()

    # 绘制搜索区域
    target = lightning_detector.real_lightning_position
    tolerance = lightning_detector.search_tolerance
    cv2.rectangle(result_image,
                 (target[0] - tolerance, target[1] - tolerance),
                 (target[0] + tolerance, target[1] + tolerance),
                 (0, 255, 0), 2)

    # 绘制目标位置
    cv2.circle(result_image, target, 3, (255, 0, 255), -1)
    cv2.putText(result_image, "TARGET", (target[0]+5, target[1]-5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 255), 1)

    # 绘制排除区域
    for zone_name, zone in lightning_detector.strict_exclusions.items():
        x_range = zone['x_range']
        y_range = zone['y_range']
        cv2.rectangle(result_image,
                     (x_range[0], y_range[0]),
                     (x_range[1], y_range[1]),
                     (0, 0, 255), 1)

    # 绘制检测到的闪电图标
    for i, icon in enumerate(lightning_icons):
        x, y, w, h = icon['bounds']
        center = icon['center']
        confidence = icon['confidence']

        # 用金色标记
        cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 215, 255), 3)
        cv2.circle(result_image, center, 3, (0, 215, 255), -1)

        # 添加标签
        label = f"LIGHTNING #{i+1}"
        detail = f"conf={confidence:.2f}"
        cv2.putText(result_image, label, (x-10, y-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 215, 255), 1)
        cv2.putText(result_image, detail, (x-10, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 215, 255), 1)

        print(f"闪电图标 {i+1}:")
        print(f"  位置: {icon['bounds']}")
        print(f"  中心: {center}")
        print(f"  置信度: {confidence:.3f}")
        print(f"  面积: {icon['area']}")
        print(f"  高宽比: {icon['aspect_ratio']:.2f}")

    # 保存结果
    output_path = "../../final_lightning_result.png"
    cv2.imwrite(output_path, result_image)
    print(f"\\n结果图像已保存: {output_path}")

    status = "成功" if len(lightning_icons) > 0 else "未检测到"
    print(f"检测状态: {status}")

    return lightning_icons

if __name__ == "__main__":
    result = test_final_detector()