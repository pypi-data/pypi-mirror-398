#!/usr/bin/env python3
"""
综合检测器 - 集成所有检测手段的完整解决方案
包括：精确圆形检测、智能矩形检测、OCR文字识别、特征点检测、语义分析
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging
import time

# 导入各个专门检测器
from precise_circle_detector import PreciseCircleDetector

logger = logging.getLogger(__name__)

class ComprehensiveDetector:
    """综合检测器 - 整合所有检测技术"""

    def __init__(self):
        self.logger = logger
        self.circle_detector = PreciseCircleDetector()

        # 初始化OCR引擎
        self.ocr_engine = None
        self._init_ocr()

    def _init_ocr(self):
        """初始化OCR引擎"""
        try:
            import easyocr
            self.ocr_engine = easyocr.Reader(['en', 'ch_sim'], gpu=False)
            self.ocr_type = 'easyocr'
            self.logger.info("EasyOCR引擎初始化成功")
        except ImportError:
            try:
                import ddddocr
                self.ocr_engine = ddddocr.DdddOcr()
                self.ocr_type = 'ddddocr'
                self.logger.info("ddddocr引擎初始化成功")
            except ImportError:
                self.ocr_engine = None
                self.ocr_type = None
                self.logger.warning("未找到可用的OCR引擎")

    def detect_smart_rectangles(self, image: np.ndarray) -> List[Dict]:
        """智能矩形检测 - 只检测有意义的矩形UI元素"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            rectangles = []

            # 方法1: 基于轮廓的矩形检测
            contour_rects = self._detect_contour_rectangles(gray)
            rectangles.extend(contour_rects)

            # 方法2: 基于线段的矩形检测
            line_rects = self._detect_line_rectangles(gray)
            rectangles.extend(line_rects)

            # 过滤和验证
            validated_rects = self._validate_rectangles(rectangles, gray, image.shape)

            self.logger.info(f"智能矩形检测: {len(validated_rects)} 个有效矩形")
            return validated_rects

        except Exception as e:
            self.logger.error(f"智能矩形检测失败: {e}")
            return []

    def _detect_contour_rectangles(self, gray: np.ndarray) -> List[Dict]:
        """基于轮廓的矩形检测"""
        rectangles = []

        # 多种边缘检测策略
        edge_methods = [
            cv2.Canny(gray, 50, 150),
            cv2.Canny(gray, 80, 200),
            cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        ]

        for edges in edge_methods:
            # 形态学操作连接断开的边缘
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 800:  # 最小面积阈值
                    continue

                # 多边形近似
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # 只保留矩形或近似矩形
                if 4 <= len(approx) <= 6:
                    x, y, w, h = cv2.boundingRect(contour)

                    # 长宽比合理性检查
                    aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                    if aspect_ratio > 10:  # 过滤过细长的形状
                        continue

                    # 面积填充度检查
                    bbox_area = w * h
                    if bbox_area > 0:
                        fill_ratio = area / bbox_area
                        if fill_ratio < 0.4:  # 填充度太低
                            continue

                    rectangles.append({
                        'type': 'rectangle',
                        'method': 'contour',
                        'bounds': [x, y, x + w, y + h],
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'fill_ratio': fill_ratio
                    })

        return rectangles

    def _detect_line_rectangles(self, gray: np.ndarray) -> List[Dict]:
        """基于线段检测的矩形检测"""
        rectangles = []

        try:
            # 霍夫线变换检测直线
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                                   minLineLength=50, maxLineGap=10)

            if lines is not None:
                # 分析线段组成的矩形
                # 这里可以添加基于线段的矩形检测逻辑
                # 暂时返回空列表，专注于轮廓方法
                pass

        except Exception as e:
            self.logger.error(f"线段矩形检测失败: {e}")

        return rectangles

    def _validate_rectangles(self, rectangles: List[Dict], gray: np.ndarray,
                           image_shape: Tuple) -> List[Dict]:
        """验证矩形的有效性"""
        validated = []

        for rect in rectangles:
            bounds = rect['bounds']
            x1, y1, x2, y2 = bounds
            w, h = x2 - x1, y2 - y1

            # 基本尺寸检查
            if w < 30 or h < 20:
                continue

            # 位置合理性检查
            if x1 < 0 or y1 < 0 or x2 >= image_shape[1] or y2 >= image_shape[0]:
                continue

            # 提取ROI分析
            roi = gray[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            # 内容分析
            mean_intensity = np.mean(roi)
            std_intensity = np.std(roi)

            # 计算置信度
            confidence = self._calculate_rect_confidence(rect, mean_intensity, std_intensity)

            if confidence > 0.6:
                rect['confidence'] = confidence
                rect['semantic_type'] = self._classify_rectangle(rect, image_shape)
                validated.append(rect)

        return validated

    def _calculate_rect_confidence(self, rect: Dict, mean_intensity: float, std_intensity: float) -> float:
        """计算矩形置信度"""
        confidence = 0.5

        # 面积合理性
        area = rect.get('area', 0)
        if 800 <= area <= 50000:
            confidence += 0.2

        # 长宽比合理性
        aspect_ratio = rect.get('aspect_ratio', 0)
        if 0.2 <= aspect_ratio <= 8:
            confidence += 0.2

        # 填充度
        fill_ratio = rect.get('fill_ratio', 0)
        if fill_ratio > 0.5:
            confidence += 0.2

        # 内容丰富度
        if 10 <= std_intensity <= 70:
            confidence += 0.2

        return min(1.0, max(0.0, confidence))

    def _classify_rectangle(self, rect: Dict, image_shape: Tuple) -> str:
        """矩形语义分类"""
        bounds = rect['bounds']
        x1, y1, x2, y2 = bounds
        w, h = x2 - x1, y2 - y1
        aspect_ratio = rect.get('aspect_ratio', 1.0)

        # 基于长宽比分类
        if aspect_ratio > 4:
            if h < 50:
                return 'horizontal_bar'
            else:
                return 'horizontal_panel'
        elif aspect_ratio < 0.5:
            return 'vertical_bar'
        elif 0.8 <= aspect_ratio <= 1.2:
            return 'square_panel'
        else:
            return 'rectangular_panel'

    def detect_text_regions(self, image: np.ndarray) -> List[Dict]:
        """检测和识别文字区域"""
        try:
            text_regions = []

            if self.ocr_engine is None:
                self.logger.warning("OCR引擎不可用")
                return text_regions

            if self.ocr_type == 'easyocr':
                results = self.ocr_engine.readtext(image)

                for result in results:
                    bbox, text, confidence = result

                    # 计算边界框
                    points = np.array(bbox, dtype=np.int32)
                    x_coords = points[:, 0]
                    y_coords = points[:, 1]
                    x1, y1 = np.min(x_coords), np.min(y_coords)
                    x2, y2 = np.max(x_coords), np.max(y_coords)

                    if confidence > 0.3 and len(text.strip()) > 0:  # 降低阈值捕获更多文字
                        text_regions.append({
                            'type': 'text',
                            'bounds': [x1, y1, x2, y2],
                            'text': text.strip(),
                            'confidence': confidence,
                            'language': self._detect_language(text),
                            'bbox_points': points.tolist()
                        })

            elif self.ocr_type == 'ddddocr':
                # ddddocr需要手动分割文字区域
                # 使用形态学操作检测文字区域
                text_regions = self._detect_text_regions_morphology(image)

            self.logger.info(f"文字检测: {len(text_regions)} 个文字区域")
            return text_regions

        except Exception as e:
            self.logger.error(f"文字检测失败: {e}")
            return []

    def _detect_text_regions_morphology(self, image: np.ndarray) -> List[Dict]:
        """使用形态学操作检测文字区域（用于ddddocr）"""
        text_regions = []

        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 形态学操作检测文字
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

            # 二值化
            _, binary = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

                    if self.ocr_type == 'ddddocr':
                        try:
                            _, buffer = cv2.imencode('.png', roi)
                            text = self.ocr_engine.classification(buffer.tobytes()).strip()

                            if len(text) > 0:
                                text_regions.append({
                                    'type': 'text',
                                    'bounds': [x, y, x + w, y + h],
                                    'text': text,
                                    'confidence': 0.8,  # ddddocr不提供置信度
                                    'language': self._detect_language(text)
                                })
                        except Exception as e:
                            self.logger.debug(f"ddddocr识别失败: {e}")

        except Exception as e:
            self.logger.error(f"形态学文字检测失败: {e}")

        return text_regions

    def _detect_language(self, text: str) -> str:
        """检测文字语言"""
        import re
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        has_english = bool(re.search(r'[a-zA-Z]', text))
        has_numbers = bool(re.search(r'\d', text))

        if has_chinese and has_english:
            return 'mixed'
        elif has_chinese:
            return 'chinese'
        elif has_english:
            return 'english'
        elif has_numbers:
            return 'numeric'
        else:
            return 'unknown'

    def detect_feature_points(self, image: np.ndarray) -> Dict:
        """检测特征点"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            feature_results = {}

            # SIFT特征点
            sift = cv2.SIFT_create(nfeatures=50)  # 减少特征点数量
            sift_kp, sift_desc = sift.detectAndCompute(gray, None)

            # ORB特征点
            orb = cv2.ORB_create(nfeatures=50)
            orb_kp, orb_desc = orb.detectAndCompute(gray, None)

            feature_results = {
                'sift_keypoints': sift_kp,
                'sift_descriptors': sift_desc,
                'orb_keypoints': orb_kp,
                'orb_descriptors': orb_desc,
                'sift_count': len(sift_kp),
                'orb_count': len(orb_kp)
            }

            self.logger.info(f"特征点检测: SIFT={len(sift_kp)}, ORB={len(orb_kp)}")
            return feature_results

        except Exception as e:
            self.logger.error(f"特征点检测失败: {e}")
            return {}

    def comprehensive_detection(self, image: np.ndarray) -> Dict:
        """综合检测 - 整合所有检测手段"""
        try:
            start_time = time.time()

            self.logger.info("开始综合检测...")

            # 1. 精确圆形检测
            print("执行精确圆形检测...")
            circles = self.circle_detector.detect_dashboard_circles(image)

            # 2. 智能矩形检测
            print("执行智能矩形检测...")
            rectangles = self.detect_smart_rectangles(image)

            # 3. 文字区域检测
            print("执行文字区域检测...")
            text_regions = self.detect_text_regions(image)

            # 4. 特征点检测
            print("执行特征点检测...")
            features = self.detect_feature_points(image)

            # 汇总结果
            all_elements = circles + rectangles + text_regions

            detection_time = time.time() - start_time

            result = {
                'success': True,
                'total_elements': len(all_elements),
                'detection_time': round(detection_time, 3),
                'elements': {
                    'circles': circles,
                    'rectangles': rectangles,
                    'text_regions': text_regions,
                    'all_elements': all_elements
                },
                'features': features,
                'statistics': {
                    'circle_count': len(circles),
                    'rectangle_count': len(rectangles),
                    'text_count': len(text_regions),
                    'sift_features': features.get('sift_count', 0),
                    'orb_features': features.get('orb_count', 0)
                }
            }

            self.logger.info(f"综合检测完成: {len(all_elements)}个元素, 耗时{detection_time:.3f}s")
            return result

        except Exception as e:
            self.logger.error(f"综合检测失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_elements': 0,
                'elements': {'all_elements': []},
                'features': {}
            }


import re  # 添加缺失的import