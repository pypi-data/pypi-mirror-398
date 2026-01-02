#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Definitive Lightning Detector - 终极闪电图标检测器
彻底解决方案：精确位置约束 + 专用模板 + 排除策略
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Tuple, Optional

class DefinitiveLightningDetector:
    """终极闪电检测器 - 只检测真实的充电闪电图标"""

    def __init__(self):
        # 基于实际分析的精确位置约束
        self.lightning_precise_area = {
            'x_min': 75,    # 精确X范围
            'x_max': 95,
            'y_min': 160,   # 精确Y范围 - 在信号强度和时钟之间
            'y_max': 185,
            'center_target': (83, 170)  # 目标中心点
        }

        # 排除区域定义
        self.exclusion_zones = [
            # 信号强度区域（垂直柱）
            {'name': 'signal_bars', 'x_min': 60, 'x_max': 90, 'y_min': 120, 'y_max': 155},
            # 文字区域
            {'name': 'text_areas', 'x_min': 95, 'x_max': 400, 'y_min': 0, 'y_max': 480},
            # C1仪表区域
            {'name': 'gauge_area', 'x_min': 80, 'x_max': 105, 'y_min': 270, 'y_max': 295},
        ]

    def create_precise_lightning_template(self) -> np.ndarray:
        """创建精确的闪电模板 - 基于真实观察"""
        # 闪电图标实际大小约 10x15
        template = np.zeros((15, 10), dtype=np.uint8)

        # 绘制真实的闪电形状
        # 顶部斜线（左上到右中）
        cv2.line(template, (1, 1), (7, 6), 255, 1)
        # 中间水平线
        cv2.line(template, (3, 6), (6, 6), 255, 1)
        # 底部斜线（左中到右下）
        cv2.line(template, (3, 7), (8, 13), 255, 1)

        return template

    def is_in_exclusion_zone(self, center: Tuple[int, int]) -> Optional[str]:
        """检查点是否在排除区域内"""
        x, y = center

        for zone in self.exclusion_zones:
            if (zone['x_min'] <= x <= zone['x_max'] and
                zone['y_min'] <= y <= zone['y_max']):
                return zone['name']
        return None

    def is_in_lightning_area(self, center: Tuple[int, int]) -> bool:
        """检查点是否在闪电图标精确区域内"""
        x, y = center
        area = self.lightning_precise_area
        return (area['x_min'] <= x <= area['x_max'] and
                area['y_min'] <= y <= area['y_max'])

    def calculate_distance_to_target(self, center: Tuple[int, int]) -> float:
        """计算到目标闪电位置的距离"""
        target = self.lightning_precise_area['center_target']
        return np.sqrt((center[0] - target[0])**2 + (center[1] - target[1])**2)

    def detect_real_lightning_only(self, image: np.ndarray) -> List[Dict]:
        """只检测真实的充电闪电图标"""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        print(f"开始终极闪电检测 - 图像尺寸: {width}x{height}")

        # 第一步：严格的位置预筛选
        area = self.lightning_precise_area
        roi = gray[area['y_min']:area['y_max'], area['x_min']:area['x_max']]
        print(f"闪电搜索区域: ({area['x_min']},{area['y_min']}) 到 ({area['x_max']},{area['y_max']})")

        if roi.size == 0:
            print("搜索区域为空")
            return []

        # 第二步：精确模板匹配
        template = self.create_precise_lightning_template()
        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)

        lightning_candidates = []
        threshold = 0.4  # 相对宽松的阈值，后续用位置精确度筛选

        locations = np.where(result >= threshold)
        for pt in zip(*locations[::-1]):
            x, y = pt
            confidence = float(result[y, x])

            # 转换回全图坐标
            full_x = x + area['x_min']
            full_y = y + area['y_min']
            center = (full_x + template.shape[1]//2, full_y + template.shape[0]//2)

            # 计算到目标位置的距离
            distance = self.calculate_distance_to_target(center)

            candidate = {
                'type': 'icon',
                'icon_type': 'lightning',
                'bounds': (full_x, full_y, template.shape[1], template.shape[0]),
                'center': center,
                'confidence': confidence,
                'distance_to_target': distance,
                'detection_method': 'definitive_template',
                'template_size': template.shape
            }

            lightning_candidates.append(candidate)
            print(f"模板匹配候选: center={center}, confidence={confidence:.3f}, distance={distance:.1f}")

        # 第三步：位置精度排序和筛选
        if lightning_candidates:
            # 按距离目标位置排序
            lightning_candidates.sort(key=lambda x: x['distance_to_target'])

            # 只保留距离目标位置最近的1-2个候选
            filtered_candidates = []
            for candidate in lightning_candidates[:2]:  # 最多2个
                distance = candidate['distance_to_target']
                if distance <= 10:  # 必须在目标位置10像素范围内
                    # 检查是否在排除区域
                    exclusion_zone = self.is_in_exclusion_zone(candidate['center'])
                    if exclusion_zone:
                        print(f"排除候选 {candidate['center']} - 在{exclusion_zone}区域内")
                        continue

                    # 最终验证：必须在精确闪电区域内
                    if self.is_in_lightning_area(candidate['center']):
                        filtered_candidates.append(candidate)
                        print(f"确认真实闪电图标: center={candidate['center']}, distance={distance:.1f}")
                    else:
                        print(f"排除候选 {candidate['center']} - 不在精确闪电区域内")
                else:
                    print(f"排除候选 {candidate['center']} - 距离目标太远: {distance:.1f} > 10")

            return filtered_candidates
        else:
            print("未找到任何模板匹配")
            return []

    def create_verification_image(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """创建验证图像"""
        result_image = image.copy()

        # 绘制搜索区域
        area = self.lightning_precise_area
        cv2.rectangle(result_image,
                     (area['x_min'], area['y_min']),
                     (area['x_max'], area['y_max']),
                     (0, 255, 0), 2)

        # 绘制目标位置
        target = area['center_target']
        cv2.circle(result_image, target, 5, (255, 0, 255), 2)
        cv2.putText(result_image, "TARGET", (target[0]+8, target[1]),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)

        # 绘制排除区域
        for zone in self.exclusion_zones:
            cv2.rectangle(result_image,
                         (zone['x_min'], zone['y_min']),
                         (zone['x_max'], zone['y_max']),
                         (0, 0, 255), 1)
            cv2.putText(result_image, zone['name'][:8],
                       (zone['x_min'], zone['y_min']-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)

        # 绘制检测结果
        for i, detection in enumerate(detections):
            x, y, w, h = detection['bounds']
            center = detection['center']
            confidence = detection['confidence']
            distance = detection['distance_to_target']

            # 用金色标记真实闪电
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 215, 255), 3)
            cv2.circle(result_image, center, 3, (0, 215, 255), -1)

            # 添加标签
            label = f"REAL LIGHTNING #{i+1}"
            detail = f"conf={confidence:.2f} dist={distance:.1f}"

            cv2.putText(result_image, label, (x-10, y-25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 215, 255), 1)
            cv2.putText(result_image, detail, (x-10, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 215, 255), 1)

        return result_image

def test_definitive_detector():
    """测试终极检测器"""
    print("=" * 60)
    print("终极闪电检测器测试")
    print("=" * 60)

    detector = DefinitiveLightningDetector()

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

    # 执行终极检测
    lightning_icons = detector.detect_real_lightning_only(image)

    print(f"\\n检测结果:")
    print(f"找到 {len(lightning_icons)} 个真实闪电充电图标")

    for i, icon in enumerate(lightning_icons):
        print(f"闪电图标 {i+1}:")
        print(f"  位置: {icon['bounds']}")
        print(f"  中心: {icon['center']}")
        print(f"  置信度: {icon['confidence']:.3f}")
        print(f"  距离目标: {icon['distance_to_target']:.1f} 像素")

    # 创建验证图像
    verification_image = detector.create_verification_image(image, lightning_icons)
    output_path = "../../definitive_lightning_result.png"
    cv2.imwrite(output_path, verification_image)

    print(f"\\n验证图像已保存: {output_path}")
    print(f"状态: {'成功' if len(lightning_icons) > 0 else '需要调整参数'}")

    return lightning_icons

if __name__ == "__main__":
    test_definitive_detector()