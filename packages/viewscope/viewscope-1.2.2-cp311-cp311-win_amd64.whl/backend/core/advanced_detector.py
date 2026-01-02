"""
高级视觉检测器模块
使用SIFT/ORB特征检测、多尺度模板匹配和智能分析算法
优化UI元素检测精度和鲁棒性
"""

import cv2
import numpy as np
import imagehash
from PIL import Image
from typing import List, Dict, Optional, Tuple, Any
import logging
import json
from pathlib import Path
try:
    import easyocr
    OCR_ENGINE = 'easyocr'
except ImportError:
    try:
        import ddddocr
        OCR_ENGINE = 'ddddocr'
    except ImportError:
        try:
            import pytesseract
            OCR_ENGINE = 'pytesseract'
        except ImportError:
            OCR_ENGINE = None

import re

logger = logging.getLogger(__name__)


class AdvancedDetector:
    """高级视觉检测器 - 基于SIFT/ORB特征检测和多尺度匹配"""
    
    def __init__(self):
        self.logger = logger
        self.sift = None
        self.orb = None
        self.bf_matcher = None
        self.flann_matcher = None
        self.template_database = {}
        self.detection_cache = {}
        self.last_detection_results = []
        
        # 初始化特征检测器
        self._init_feature_detectors()
        
        # 初始化匹配器
        self._init_matchers()
        
        # 加载模板数据库
        self._load_template_database()
        
        # 初始化OCR引擎
        self.ocr_engine = None
        self._init_ocr_engine()
        
    def _init_feature_detectors(self):
        """初始化SIFT和ORB特征检测器 - QNX优化版本"""
        try:
            # SIFT检测器 - 优化参数提升特征检测能力
            self.sift = cv2.SIFT_create(
                nfeatures=200,           # 增加特征点数量以捕获更多UI细节
                nOctaveLayers=4,         # 增加金字塔层数提升多尺度检测
                contrastThreshold=0.02,  # 降低对比度阈值，保留更多弱特征
                edgeThreshold=15,        # 增加边缘阈值，减少边缘噪声干扰
                sigma=1.6               # 标准值: Lowe论文推荐
            )
            
            # ORB检测器 - 优化参数提升实时检测性能
            self.orb = cv2.ORB_create(
                nfeatures=200,          # 增加特征点数量，提升匹配稳定性
                scaleFactor=1.1,        # 减小缩放因子，获得更精细的尺度变化
                nlevels=12,             # 增加金字塔层数，提升多尺度检测能力
                edgeThreshold=25,       # 优化边缘阈值，平衡检测灵敏度和噪声
                firstLevel=0,           # 保持起始层
                WTA_K=2,               # 标准值: 二进制描述符
                scoreType=cv2.ORB_HARRIS_SCORE,  # Harris评分更准确
                patchSize=31            # 标准值: 标准patch大小
            )
            
            self.logger.info("特征检测器初始化完成")
            
        except Exception as e:
            self.logger.error(f"特征检测器初始化失败: {e}")
    
    def _init_matchers(self):
        """初始化特征匹配器"""
        try:
            # 暴力匹配器 - 适用于ORB
            self.bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            
            # FLANN匹配器 - QNX优化版本 (减少搜索次数提升速度)
            flann_params = dict(algorithm=1, trees=4)  # QNX优化: 减少树数量
            search_params = dict(checks=30)           # QNX优化: 减少检查次数
            self.flann_matcher = cv2.FlannBasedMatcher(flann_params, search_params)
            
            self.logger.info("特征匹配器初始化完成")
            
        except Exception as e:
            self.logger.error(f"特征匹配器初始化失败: {e}")
    
    def _load_template_database(self):
        """加载UI元素模板数据库"""
        self.template_database = {
            "buttons": {
                "radio_button": {
                    "size_range": [20, 60],
                    "aspect_ratio_range": [0.8, 1.2],
                    "color_hints": ["blue", "green", "gray"],
                    "context_keywords": ["radio", "am", "fm"]
                },
                "power_button": {
                    "size_range": [30, 80],
                    "aspect_ratio_range": [0.9, 1.1],
                    "color_hints": ["red", "green", "white"],
                    "context_keywords": ["power", "on", "off"]
                }
            },
            "indicators": {
                "volume_indicator": {
                    "size_range": [10, 40],
                    "aspect_ratio_range": [0.5, 2.0],
                    "color_hints": ["green", "blue", "white"]
                },
                "signal_indicator": {
                    "size_range": [15, 50],
                    "aspect_ratio_range": [0.8, 1.5],
                    "color_hints": ["green", "yellow", "red"]
                }
            },
            "sliders": {
                "volume_slider": {
                    "size_range": [100, 300],
                    "aspect_ratio_range": [3.0, 8.0],
                    "color_hints": ["blue", "gray", "white"]
                },
                "brightness_slider": {
                    "size_range": [80, 250],
                    "aspect_ratio_range": [2.5, 6.0],
                    "color_hints": ["yellow", "white", "gray"]
                }
            }
        }
        
        self.logger.info("模板数据库加载完成")
    
    def _init_ocr_engine(self):
        """初始化OCR引擎 - 优先使用EasyOCR"""
        try:
            if OCR_ENGINE == 'easyocr':
                self.ocr_engine = easyocr.Reader(['en', 'ch_sim'])  # 英文+中文
                self.logger.info("使用EasyOCR引擎初始化成功")
            elif OCR_ENGINE == 'ddddocr':
                self.ocr_engine = ddddocr.DdddOcr()
                self.logger.info("使用ddddocr引擎初始化成功")
            elif OCR_ENGINE == 'pytesseract':
                self.ocr_engine = 'pytesseract'
                self.logger.info("使用pytesseract引擎")
            else:
                self.logger.warning("未找到可用的OCR引擎")
        except Exception as e:
            self.logger.error(f"OCR引擎初始化失败: {e}")
    
    def detect_features_sift(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """
        使用SIFT算法检测特征点和描述符
        
        Args:
            image: 输入图像
            
        Returns:
            Tuple[List, np.ndarray]: 关键点列表和描述符数组
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 检测关键点和计算描述符
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)
            
            # 特征质量过滤 - 使用宽松阈值
            if keypoints and descriptors is not None:
                filtered_keypoints, filtered_descriptors = self._filter_quality_features(
                    keypoints, descriptors, method='sift'
                )
                self.logger.info(f"SIFT检测到 {len(keypoints)} 个特征点，过滤后保留 {len(filtered_keypoints)} 个高质量特征")
                return filtered_keypoints, filtered_descriptors
            else:
                self.logger.info("SIFT未检测到特征点")
                return [], None
            
        except Exception as e:
            self.logger.error(f"SIFT特征检测失败: {e}")
            return [], None
    
    def detect_features_orb(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """
        使用ORB算法检测特征点和描述符
        
        Args:
            image: 输入图像
            
        Returns:
            Tuple[List, np.ndarray]: 关键点列表和描述符数组
        """
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 检测关键点和计算描述符
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            # 特征质量过滤 - 使用宽松阈值  
            if keypoints and descriptors is not None:
                filtered_keypoints, filtered_descriptors = self._filter_quality_features(
                    keypoints, descriptors, method='orb'
                )
                self.logger.info(f"ORB检测到 {len(keypoints)} 个特征点，过滤后保留 {len(filtered_keypoints)} 个高质量特征")
                return filtered_keypoints, filtered_descriptors
            else:
                self.logger.info("ORB未检测到特征点")
                return [], None
            
        except Exception as e:
            self.logger.error(f"ORB特征检测失败: {e}")
            return [], None
    
    def multi_scale_template_matching(self, image: np.ndarray, template: np.ndarray, 
                                    scales: List[float] = None) -> Dict:
        """
        多尺度模板匹配
        
        Args:
            image: 输入图像
            template: 模板图像
            scales: 尺度列表
            
        Returns:
            Dict: 最佳匹配结果
        """
        if scales is None:
            # QNX优化: 使用更少的尺度以提升实时性能
            scales = [0.75, 1.0, 1.25]
        
        try:
            best_match = None
            best_score = 0
            
            for scale in scales:
                # 缩放模板
                scaled_template = cv2.resize(template, None, fx=scale, fy=scale)
                
                # 检查缩放后的模板是否小于图像
                if (scaled_template.shape[0] > image.shape[0] or 
                    scaled_template.shape[1] > image.shape[1]):
                    continue
                
                # 模板匹配
                result = cv2.matchTemplate(image, scaled_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_score:
                    best_score = max_val
                    best_match = {
                        'score': max_val,
                        'location': max_loc,
                        'scale': scale,
                        'template_size': scaled_template.shape[:2]
                    }
            
            return best_match if best_match else {}
            
        except Exception as e:
            self.logger.error(f"多尺度模板匹配失败: {e}")
            return {}
    
    def analyze_hsv_colors(self, roi: np.ndarray, k: int = 3) -> Dict:
        """
        HSV颜色空间分析和K-means聚类
        
        Args:
            roi: 感兴趣区域
            k: 聚类数量
            
        Returns:
            Dict: 颜色分析结果
        """
        try:
            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            data = hsv.reshape((-1, 3)).astype(np.float32)
            
            # K-means聚类
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # 统计颜色分布
            unique, counts = np.unique(labels, return_counts=True)
            color_percentages = counts / len(data) * 100
            
            # 颜色分类
            dominant_colors = []
            for i, center in enumerate(centers):
                h, s, v = center
                color_name = self._classify_hsv_color(h, s, v)
                dominant_colors.append({
                    'color_name': color_name,
                    'hsv': [int(h), int(s), int(v)],
                    'percentage': color_percentages[i] if i < len(color_percentages) else 0
                })
            
            # 按百分比排序
            dominant_colors.sort(key=lambda x: x['percentage'], reverse=True)
            
            return {
                'dominant_colors': dominant_colors,
                'primary_color': dominant_colors[0]['color_name'] if dominant_colors else 'unknown',
                'color_diversity': len(dominant_colors)
            }
            
        except Exception as e:
            self.logger.error(f"HSV颜色分析失败: {e}")
            return {'dominant_colors': [], 'primary_color': 'unknown', 'color_diversity': 0}
    
    def _classify_hsv_color(self, h: float, s: float, v: float) -> str:
        """
        HSV颜色分类
        
        Args:
            h: 色调
            s: 饱和度
            v: 明度
            
        Returns:
            str: 颜色名称
        """
        # 低饱和度为灰度色
        if s < 30:
            if v < 50:
                return 'black'
            elif v > 200:
                return 'white'
            else:
                return 'gray'
        
        # 基于色调分类
        if h < 10 or h > 170:
            return 'red'
        elif 10 <= h < 25:
            return 'orange'
        elif 25 <= h < 35:
            return 'yellow'
        elif 35 <= h < 85:
            return 'green'
        elif 85 <= h < 125:
            return 'blue'
        elif 125 <= h < 150:
            return 'purple'
        else:
            return 'pink'
    
    def smart_element_labeling(self, element: Dict) -> Dict:
        """
        智能元素标记
        
        Args:
            element: 元素信息
            
        Returns:
            Dict: 增强的元素信息
        """
        try:
            # 提取基础特征
            width = element.get('width', 0)
            height = element.get('height', 0)
            aspect_ratio = element.get('aspect_ratio', 1.0)
            element_type = element.get('type', 'unknown')
            
            # 颜色信息
            avg_color = element.get('avg_color', {})
            primary_color = avg_color.get('primary_color', 'unknown')
            
            # 模板匹配评分
            best_template_match = self._match_against_templates(width, height, aspect_ratio, primary_color)
            
            # 智能标记决策
            if best_template_match['confidence'] > 0.3:
                semantic_name = best_template_match['template_name']
                confidence = best_template_match['confidence']
            else:
                # 回退到几何特征推理
                semantic_name = self._geometric_inference(element_type, width, height, aspect_ratio)
                confidence = 0.2
            
            # 增强元素信息
            element.update({
                'semantic_name': semantic_name,
                'confidence': confidence,
                'template_match': best_template_match,
                'enhanced_features': {
                    'size_category': self._categorize_size(width, height),
                    'shape_category': self._categorize_shape(aspect_ratio),
                    'color_category': primary_color
                }
            })
            
            return element
            
        except Exception as e:
            self.logger.error(f"智能元素标记失败: {e}")
            return element
    
    def extract_text_from_region(self, image: np.ndarray, region_bounds: Tuple[int, int, int, int]) -> Dict:
        """
        从指定区域提取文字信息
        
        Args:
            image: 输入图像
            region_bounds: 区域边界 (x1, y1, x2, y2)
            
        Returns:
            Dict: 文字识别结果
        """
        try:
            x1, y1, x2, y2 = region_bounds
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return {'text': '', 'confidence': 0, 'language': 'unknown'}
            
            # 预处理提高OCR准确性 - 针对小文本优化
            if len(roi.shape) == 3:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray_roi = roi.copy()
            
            # 小文本区域特殊处理
            max_dimension = max(gray_roi.shape[:2])
            if max_dimension < 100:  # 小文本区域(<100px)
                # 超分辨率增强: 2倍放大
                enhanced_roi = cv2.resize(gray_roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                
                # 锐化滤波处理
                sharpening_kernel = np.array([[-1, -1, -1], 
                                            [-1,  9, -1], 
                                            [-1, -1, -1]])
                sharpened = cv2.filter2D(enhanced_roi, -1, sharpening_kernel)
                
                # 自适应直方图均衡化
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(sharpened)
            else:
                # 标准文本处理
                enhanced = cv2.convertScaleAbs(gray_roi, alpha=1.5, beta=30)
            
            # 高级去噪 - 双边滤波保留边缘
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # 二值化处理 - 自适应阈值
            binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # 执行OCR - 优先使用EasyOCR，并使用增强的二值化图像
            if OCR_ENGINE == 'easyocr' and self.ocr_engine:
                try:
                    # 对小文本使用二值化图像，大文本使用去噪图像
                    ocr_input = binary if max_dimension < 100 else denoised
                    results = self.ocr_engine.readtext(ocr_input)
                    if results:
                        # 合并所有识别结果
                        texts = [result[1] for result in results]
                        confidences = [result[2] for result in results]
                        text = ' '.join(texts).strip()
                        avg_confidence = sum(confidences) / len(confidences) * 100
                    else:
                        text = ""
                        avg_confidence = 0
                except Exception as e:
                    self.logger.error(f"EasyOCR识别失败: {e}")
                    text = ""
                    avg_confidence = 0
            elif OCR_ENGINE == 'ddddocr' and self.ocr_engine:
                try:
                    # ddddocr需要bytes格式
                    _, buffer = cv2.imencode('.png', denoised)
                    img_bytes = buffer.tobytes()
                    text = self.ocr_engine.classification(img_bytes).strip()
                    avg_confidence = 85  # ddddocr默认较高置信度
                except Exception as e:
                    self.logger.error(f"ddddocr识别失败: {e}")
                    text = ""
                    avg_confidence = 0
            elif OCR_ENGINE == 'pytesseract':
                try:
                    # pytesseract配置
                    config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz一二三四五六七八九十本次行程总里程功率时间电量公里小时千瓦度分钟秒°C℃PWRkmhkWhERROR.:-+%'
                    text = pytesseract.image_to_string(denoised, lang='chi_sim+eng', config=config).strip()
                    
                    # 获取置信度
                    data = pytesseract.image_to_data(denoised, lang='chi_sim+eng', config=config, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                except Exception as e:
                    self.logger.error(f"pytesseract识别失败: {e}")
                    text = ""
                    avg_confidence = 0
            else:
                text = ""
                avg_confidence = 0
            
            # 检测语言类型
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
            has_english = bool(re.search(r'[a-zA-Z]', text))
            has_numbers = bool(re.search(r'\d', text))
            
            language = 'mixed'
            if has_chinese and not has_english:
                language = 'chinese'
            elif has_english and not has_chinese:
                language = 'english'
            elif has_numbers and not has_chinese and not has_english:
                language = 'numeric'
            
            return {
                'text': text,
                'confidence': avg_confidence,
                'language': language,
                'has_chinese': has_chinese,
                'has_english': has_english,
                'has_numbers': has_numbers,
                'char_count': len(text)
            }
            
        except Exception as e:
            self.logger.error(f"OCR文字提取失败: {e}")
            return {'text': '', 'confidence': 0, 'language': 'unknown'}
    
    def analyze_element_semantics(self, element: Dict, image: np.ndarray) -> Dict:
        """
        分析元素语义信息
        
        Args:
            element: 元素信息
            image: 完整图像
            
        Returns:
            Dict: 增强的语义信息
        """
        try:
            # 提取元素周围文字信息
            if element['type'] == 'circle':
                center = element['center']
                radius = element['radius']
                # 扩大搜索区域到圆形周围
                search_x1 = max(0, center[0] - radius * 2)
                search_y1 = max(0, center[1] - radius * 2)
                search_x2 = min(image.shape[1], center[0] + radius * 2)
                search_y2 = min(image.shape[0], center[1] + radius * 2)
            else:
                bounds = element['bounds']
                # 扩大搜索区域
                margin = 30
                search_x1 = max(0, bounds[0] - margin)
                search_y1 = max(0, bounds[1] - margin) 
                search_x2 = min(image.shape[1], bounds[2] + margin)
                search_y2 = min(image.shape[0], bounds[3] + margin)
            
            # 提取周围文字
            ocr_result = self.extract_text_from_region(image, (search_x1, search_y1, search_x2, search_y2))
            
            # 基于文字内容推断功能
            text = ocr_result['text'].lower()
            semantic_info = self._infer_function_from_text(text, element)
            
            # 合并信息
            element['ocr_result'] = ocr_result
            element['semantic_function'] = semantic_info['function']
            element['semantic_confidence'] = semantic_info['confidence']
            element['context_keywords'] = semantic_info['keywords']
            
            return element
            
        except Exception as e:
            self.logger.error(f"语义分析失败: {e}")
            return element
    
    def _infer_function_from_text(self, text: str, element: Dict) -> Dict:
        """基于文字内容推断元素功能"""
        
        # 汽车仪表盘关键词映射
        function_keywords = {
            'trip_display': ['本次行程', 'trip', '里程', 'km', '行程'],
            'total_mileage': ['总里程', 'total', 'odometer'],
            'power_indicator': ['功率', 'power', 'pwr', '电力'],
            'speed_display': ['速度', 'speed', 'km/h', 'mph'],
            'time_display': ['时间', 'time', ':', '小时', 'h'],
            'temperature': ['温度', 'temp', '°c', '℃'],
            'battery': ['电量', 'battery', '%', '电池'],
            'fuel': ['油量', 'fuel', 'gas'],
            'warning': ['warning', '警告', 'error', '故障'],
            'gear': ['档位', 'gear', 'p', 'r', 'n', 'd'],
            'indicator_light': ['指示', 'light', '灯', '信号']
        }
        
        # 分析文字匹配度
        best_function = 'unknown_element'
        best_confidence = 0.1
        matched_keywords = []
        
        for function, keywords in function_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                confidence = matches / len(keywords) * 0.8 + 0.2
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_function = function
                    matched_keywords = [kw for kw in keywords if kw in text]
        
        # 结合元素类型和位置信息
        if element['type'] == 'circle':
            if 'power' in text or 'pwr' in text:
                best_function = 'power_button'
                best_confidence = max(best_confidence, 0.7)
            elif any(word in text for word in ['warning', 'error', '故障']):
                best_function = 'warning_indicator'  
                best_confidence = max(best_confidence, 0.8)
        
        return {
            'function': best_function,
            'confidence': min(best_confidence, 0.95),
            'keywords': matched_keywords
        }
    
    def _match_against_templates(self, width: int, height: int, 
                               aspect_ratio: float, color: str) -> Dict:
        """
        模板数据库匹配
        
        Args:
            width: 宽度
            height: 高度  
            aspect_ratio: 长宽比
            color: 主要颜色
            
        Returns:
            Dict: 最佳匹配结果
        """
        best_match = {'template_name': 'unknown', 'confidence': 0.0, 'category': 'unknown'}
        
        try:
            max_size = max(width, height)
            
            for category, templates in self.template_database.items():
                for template_name, template_info in templates.items():
                    # 尺寸匹配评分
                    size_range = template_info['size_range']
                    size_score = 1.0 if size_range[0] <= max_size <= size_range[1] else 0.0
                    
                    # 长宽比匹配评分
                    ratio_range = template_info['aspect_ratio_range']
                    ratio_score = 1.0 if ratio_range[0] <= aspect_ratio <= ratio_range[1] else 0.0
                    
                    # 颜色匹配评分
                    color_hints = template_info['color_hints']
                    color_score = 1.0 if color in color_hints else 0.0
                    
                    # 综合评分 (权重: 尺寸30%, 长宽比30%, 颜色20%, 上下文20%)
                    total_score = (size_score * 0.3 + ratio_score * 0.3 + 
                                 color_score * 0.2 + 0.2)  # 上下文评分默认0.2
                    
                    if total_score > best_match['confidence']:
                        best_match = {
                            'template_name': template_name,
                            'confidence': total_score,
                            'category': category
                        }
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return best_match
    
    def _geometric_inference(self, element_type: str, width: int, 
                           height: int, aspect_ratio: float) -> str:
        """
        基于几何特征的推理
        
        Args:
            element_type: 元素类型
            width: 宽度
            height: 高度
            aspect_ratio: 长宽比
            
        Returns:
            str: 推理的语义名称
        """
        if element_type == 'circle':
            radius = max(width, height) // 2
            if radius < 20:
                return "small_indicator"
            elif radius < 50:
                return "medium_button"
            else:
                return "large_control"
        
        elif element_type == 'rectangle':
            if aspect_ratio > 3:
                if height < 50:
                    return "horizontal_slider"
                else:
                    return "horizontal_panel"
            elif aspect_ratio < 0.5:
                return "vertical_indicator"
            else:
                size = max(width, height)
                if size < 30:
                    return "small_button"
                elif size < 80:
                    return "medium_button"
                else:
                    return "large_panel"
        
        # 处理不规则形状
        elif element_type in ['triangle', 'pentagon', 'hexagon']:
            size = max(width, height)
            if size < 40:
                return f"small_{element_type}_indicator"
            elif size < 100:
                return f"medium_{element_type}_button"
            else:
                return f"large_{element_type}_element"
        
        elif element_type == 'square':
            size = max(width, height)
            if size < 30:
                return "small_square_button"
            elif size < 80:
                return "medium_square_button"
            else:
                return "large_square_panel"
        
        elif element_type in ['horizontal_strip', 'vertical_strip']:
            return f"{element_type}_control"
        
        elif element_type in ['quadrilateral', 'convex_polygon', 'circular_polygon']:
            size = max(width, height)
            if size < 50:
                return f"small_{element_type}"
            elif size < 150:
                return f"medium_{element_type}"
            else:
                return f"large_{element_type}"
        
        elif element_type == 'irregular_shape':
            size = max(width, height)
            if size < 60:
                return "small_custom_element"
            elif size < 120:
                return "medium_custom_element"
            else:
                return "large_custom_element"
        
        return "unknown_element"
    
    def _categorize_size(self, width: int, height: int) -> str:
        """尺寸分类"""
        max_size = max(width, height)
        if max_size < 50:
            return 'small'
        elif max_size < 150:
            return 'medium'
        else:
            return 'large'
    
    def _categorize_shape(self, aspect_ratio: float) -> str:
        """形状分类"""
        if 0.8 <= aspect_ratio <= 1.2:
            return 'square'
        elif aspect_ratio > 2:
            return 'horizontal_rectangle'
        elif aspect_ratio < 0.5:
            return 'vertical_rectangle'
        else:
            return 'rectangle'
    
    def enhanced_detect_all_elements(self, image: np.ndarray, 
                                   use_sift: bool = True, 
                                   use_orb: bool = True) -> Dict:
        """
        增强版元素检测 - 整合所有高级算法
        
        Args:
            image: 输入图像
            use_sift: 是否使用SIFT
            use_orb: 是否使用ORB
            
        Returns:
            Dict: 完整的检测结果
        """
        try:
            # 基础几何检测 + 增强检测
            from core.basic_detector import BasicDetector
            basic_detector = BasicDetector()
            basic_results = basic_detector.detect_all_elements(image)
            
            detected_elements = []
            
            # 增强形状检测 - 使用更敏感的参数
            enhanced_circles = self._detect_enhanced_circles(image)
            enhanced_rectangles = self._detect_enhanced_rectangles(image)
            enhanced_polygons = self._detect_irregular_shapes(image)
            
            # 合并基础检测和增强检测的圆形
            all_circles = basic_results['detected_elements'].get('circles', []) + enhanced_circles
            
            # 处理检测到的圆形元素
            for circle in all_circles:
                # 提取ROI进行颜色分析
                center = circle['center']
                radius = circle['radius']
                x1, y1 = max(0, center[0] - radius), max(0, center[1] - radius)
                x2, y2 = min(image.shape[1], center[0] + radius), min(image.shape[0], center[1] + radius)
                roi = image[y1:y2, x1:x2]
                
                if roi.size > 0:
                    # HSV颜色分析
                    color_analysis = self.analyze_hsv_colors(roi)
                    circle['color_analysis'] = color_analysis
                    circle['avg_color']['primary_color'] = color_analysis['primary_color']
                    
                    # 智能标记
                    circle['width'] = radius * 2
                    circle['height'] = radius * 2
                    circle['aspect_ratio'] = 1.0
                    enhanced_circle = self.smart_element_labeling(circle)
                    
                    # 语义分析 - 让程序理解图像内容
                    semantic_circle = self.analyze_element_semantics(enhanced_circle, image)
                    detected_elements.append(semantic_circle)
            
            # 合并基础检测和增强检测的矩形
            all_rectangles = basic_results['detected_elements'].get('rectangles', []) + enhanced_rectangles
            
            # 处理检测到的矩形元素
            for rectangle in all_rectangles:
                # 提取ROI进行颜色分析
                bounds = rectangle['bounds']
                x1, y1, x2, y2 = bounds
                roi = image[y1:y2, x1:x2]
                
                if roi.size > 0:
                    # HSV颜色分析
                    color_analysis = self.analyze_hsv_colors(roi)
                    rectangle['color_analysis'] = color_analysis
                    rectangle['avg_color']['primary_color'] = color_analysis['primary_color']
                    
                    # 智能标记
                    enhanced_rectangle = self.smart_element_labeling(rectangle)
                    
                    # 语义分析 - 让程序理解图像内容
                    semantic_rectangle = self.analyze_element_semantics(enhanced_rectangle, image)
                    detected_elements.append(semantic_rectangle)
            
            # 处理检测到的不规则形状
            for polygon in enhanced_polygons:
                # 提取ROI进行颜色分析
                bounds = polygon['bounds']
                x1, y1, x2, y2 = bounds
                roi = image[y1:y2, x1:x2]
                
                if roi.size > 0:
                    # HSV颜色分析
                    color_analysis = self.analyze_hsv_colors(roi)
                    polygon['color_analysis'] = color_analysis
                    polygon['avg_color'] = {'primary_color': color_analysis['primary_color']}
                    
                    # 智能标记
                    enhanced_polygon = self.smart_element_labeling(polygon)
                    detected_elements.append(enhanced_polygon)
            
            # 特征点检测结果
            feature_results = {}
            
            if use_sift:
                sift_kp, sift_desc = self.detect_features_sift(image)
                feature_results['sift'] = {
                    'keypoints_count': len(sift_kp),
                    'has_descriptors': sift_desc is not None
                }
            
            if use_orb:
                orb_kp, orb_desc = self.detect_features_orb(image)
                feature_results['orb'] = {
                    'keypoints_count': len(orb_kp),
                    'has_descriptors': orb_desc is not None
                }
            
            # 验证和过滤检测到的元素
            validated_elements = self._validate_detected_elements(detected_elements, image.shape)
            
            # 构建完整结果
            result = {
                'success': True,
                'image_info': basic_results['image_info'],
                'detected_elements': {
                    'enhanced_elements': validated_elements,
                    'total_count': len(validated_elements)
                },
                'feature_detection': feature_results,
                'detection_metadata': {
                    'detector_type': 'advanced_opencv',
                    'algorithms_used': ['hough_circles', 'contour_rectangles', 'hsv_analysis', 'smart_labeling'],
                    'feature_detectors': []
                }
            }
            
            if use_sift:
                result['detection_metadata']['algorithms_used'].append('sift_features')
                result['detection_metadata']['feature_detectors'].append('SIFT')
            
            if use_orb:
                result['detection_metadata']['algorithms_used'].append('orb_features')
                result['detection_metadata']['feature_detectors'].append('ORB')
            
            # 缓存结果
            image_hash = basic_results['image_info']['hash']
            self.last_detection_results = result
            self.detection_cache[image_hash] = result
            
            self.logger.info(f"增强版检测完成: 原始元素={len(detected_elements)}, 验证通过={len(validated_elements)}, "
                           f"SIFT特征={feature_results.get('sift', {}).get('keypoints_count', 0)}, "
                           f"ORB特征={feature_results.get('orb', {}).get('keypoints_count', 0)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"增强版元素检测失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'detected_elements': {'enhanced_elements': [], 'total_count': 0},
                'feature_detection': {}
            }
    
    def find_element_by_template(self, image: np.ndarray, template: np.ndarray, 
                               threshold: float = 0.8) -> List[Dict]:
        """
        基于模板的元素查找
        
        Args:
            image: 输入图像
            template: 模板图像
            threshold: 匹配阈值
            
        Returns:
            List[Dict]: 匹配的元素列表
        """
        try:
            # 多尺度模板匹配
            match_result = self.multi_scale_template_matching(image, template)
            
            matches = []
            if match_result and match_result.get('score', 0) >= threshold:
                location = match_result['location']
                scale = match_result['scale']
                template_size = match_result['template_size']
                
                matches.append({
                    'type': 'template_match',
                    'location': location,
                    'scale': scale,
                    'score': match_result['score'],
                    'bounds': [
                        location[0], 
                        location[1],
                        location[0] + template_size[1],
                        location[1] + template_size[0]
                    ],
                    'confidence': match_result['score']
                })
            
            return matches
            
        except Exception as e:
            self.logger.error(f"模板查找失败: {e}")
            return []
    
    def _detect_enhanced_circles(self, image: np.ndarray) -> List[Dict]:
        """增强圆形检测 - 使用更敏感的参数"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # 应用高斯模糊
            gray = cv2.GaussianBlur(gray, (9, 9), 2)
            
            # 优化多参数圆形检测 - 覆盖不同尺寸
            all_circles = []
            param_sets = [
                (1, 30, 50, 30, 8, 25),    # 小圆形 - 指示灯
                (1, 40, 100, 45, 15, 50),  # 中圆形 - 按钮（保守参数）
                (1, 50, 100, 40, 35, 80),  # 大圆形 - 主控件
            ]
            
            for dp, minDist, param1, param2, minR, maxR in param_sets:
                circles = cv2.HoughCircles(
                    gray, cv2.HOUGH_GRADIENT,
                    dp=dp, minDist=minDist,
                    param1=param1, param2=param2,
                    minRadius=minR, maxRadius=maxR
                )
                
                if circles is not None:
                    circles = np.round(circles[0, :]).astype("int")
                    for (x, y, r) in circles:
                        # 去重 - 避免重复检测
                        is_duplicate = False
                        for existing_circle in all_circles:
                            ex, ey, er = existing_circle
                            dist = np.sqrt((x - ex)**2 + (y - ey)**2)
                            if dist < max(r, er) * 0.8:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            all_circles.append((x, y, r))
            
            detected_circles = []
            for (x, y, r) in all_circles:
                    # 创建圆形元素信息
                    circle_info = {
                        'type': 'circle',
                        'center': (int(x), int(y)),
                        'radius': int(r),
                        'bounds': [max(0, x-r), max(0, y-r), min(image.shape[1], x+r), min(image.shape[0], y+r)],
                        'area': np.pi * r * r,
                        'avg_color': {'r': 128, 'g': 128, 'b': 128},  # 默认值，后续会更新
                        'semantic_name': 'unknown_circle',
                        'confidence': 0.6,  # 增强检测的初始置信度
                        'detection_method': 'enhanced_hough'
                    }
                    detected_circles.append(circle_info)
            
            return detected_circles
            
        except Exception as e:
            self.logger.error(f"增强圆形检测失败: {e}")
            return []
    
    def _detect_enhanced_rectangles(self, image: np.ndarray) -> List[Dict]:
        """增强矩形检测 - 使用多种方法"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            detected_rectangles = []
            
            # 方法1: 更敏感的Canny边缘检测
            edges1 = cv2.Canny(gray, 30, 100, apertureSize=3)
            
            # 方法2: 形态学操作增强边缘
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges2 = cv2.morphologyEx(edges1, cv2.MORPH_CLOSE, kernel)
            
            # 合并两种边缘检测结果
            edges = cv2.bitwise_or(edges1, edges2)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # 计算轮廓面积
                area = cv2.contourArea(contour)
                if area < 50:  # 降低最小面积阈值
                    continue
                
                # 使用更宽松的多边形近似
                epsilon = 0.02 * cv2.arcLength(contour, True)  # 增加epsilon
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 检测矩形（4个顶点）或近似矩形（3-6个顶点）
                if len(approx) >= 3 and len(approx) <= 6:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 计算长宽比
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    # 汽车HMI界面元素长宽比优化
                    if 0.2 <= aspect_ratio <= 8 and area >= 200:
                        rectangle_info = {
                            'type': 'rectangle',
                            'bounds': [x, y, x + w, y + h],
                            'area': area,
                            'width': w,
                            'height': h,
                            'aspect_ratio': aspect_ratio,
                            'vertices_count': len(approx),
                            'avg_color': {'r': 128, 'g': 128, 'b': 128},  # 默认值
                            'semantic_name': 'unknown_rectangle',
                            'confidence': 0.6,  # 增强检测的初始置信度
                            'detection_method': 'enhanced_contour'
                        }
                        detected_rectangles.append(rectangle_info)
            
            return detected_rectangles
            
        except Exception as e:
            self.logger.error(f"增强矩形检测失败: {e}")
            return []
    
    def _detect_irregular_shapes(self, image: np.ndarray) -> List[Dict]:
        """检测不规则形状和多边形"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            detected_shapes = []
            
            # 使用多种边缘检测方法
            # 方法1: 自适应阈值
            adaptive_thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 方法2: Canny边缘检测 - 多个参数组合
            edges_low = cv2.Canny(gray, 50, 150)
            edges_high = cv2.Canny(gray, 100, 200)
            edges_combined = cv2.bitwise_or(edges_low, edges_high)
            
            # 方法3: 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            edges_morphed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_GRADIENT, kernel)
            
            # 合并所有边缘检测结果
            final_edges = cv2.bitwise_or(edges_combined, edges_morphed)
            
            # 查找轮廓
            contours, _ = cv2.findContours(final_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # 计算轮廓面积
                area = cv2.contourArea(contour)
                if area < 100:  # 过滤小轮廓
                    continue
                
                # 计算轮廓周长
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                
                # 多边形近似
                epsilon = 0.03 * perimeter
                approx = cv2.approxPolyDP(contour, epsilon, True)
                vertices_count = len(approx)
                
                # 计算形状特征
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # 计算圆度 (4π*面积/周长²)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # 计算凸包和凸度
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                # 分类不规则形状
                shape_type = "unknown_polygon"
                confidence = 0.5
                
                if vertices_count == 3:
                    shape_type = "triangle"
                    confidence = 0.8
                elif vertices_count == 5:
                    shape_type = "pentagon" 
                    confidence = 0.7
                elif vertices_count == 6:
                    shape_type = "hexagon"
                    confidence = 0.7
                elif vertices_count > 6:
                    if circularity > 0.7:
                        shape_type = "circular_polygon"
                        confidence = 0.6
                    elif solidity > 0.9:
                        shape_type = "convex_polygon"
                        confidence = 0.6
                    else:
                        shape_type = "irregular_shape"
                        confidence = 0.5
                elif vertices_count == 4:
                    # 进一步区分四边形类型
                    if 0.8 <= aspect_ratio <= 1.2:
                        shape_type = "square"
                        confidence = 0.8
                    elif aspect_ratio > 2.0:
                        shape_type = "horizontal_strip"
                        confidence = 0.7
                    elif aspect_ratio < 0.5:
                        shape_type = "vertical_strip" 
                        confidence = 0.7
                    else:
                        shape_type = "quadrilateral"
                        confidence = 0.6
                
                # 过滤极端形状
                if 0.05 <= aspect_ratio <= 20 and 0.1 <= circularity <= 2.0:
                    shape_info = {
                        'type': shape_type,
                        'bounds': [x, y, x + w, y + h],
                        'area': area,
                        'perimeter': perimeter,
                        'vertices_count': vertices_count,
                        'aspect_ratio': aspect_ratio,
                        'circularity': circularity,
                        'solidity': solidity,
                        'contour_points': approx.reshape(-1, 2).tolist(),  # 简化轮廓点
                        'avg_color': {'r': 128, 'g': 128, 'b': 128},  # 默认值
                        'semantic_name': f'unknown_{shape_type}',
                        'confidence': confidence,
                        'detection_method': 'enhanced_contour_analysis',
                        'width': w,
                        'height': h
                    }
                    detected_shapes.append(shape_info)
            
            # 按面积排序，保留较大的形状
            detected_shapes.sort(key=lambda x: x['area'], reverse=True)
            
            return detected_shapes[:50]  # 最多返回50个不规则形状
            
        except Exception as e:
            self.logger.error(f"不规则形状检测失败: {e}")
            return []
    
    def _filter_quality_features(self, keypoints: List, descriptors: np.ndarray, 
                               method: str = 'sift') -> Tuple[List, np.ndarray]:
        """
        过滤低质量特征点，保留高质量的UI相关特征
        
        Args:
            keypoints: 原始关键点列表
            descriptors: 原始描述符数组
            method: 特征检测方法 ('sift' 或 'orb')
            
        Returns:
            Tuple[List, np.ndarray]: 过滤后的关键点和描述符
        """
        try:
            if not keypoints or descriptors is None:
                return [], None
            
            filtered_keypoints = []
            filtered_indices = []
            
            for i, kp in enumerate(keypoints):
                # 基于响应强度过滤 - 放宽阈值  
                if method == 'sift':
                    response_threshold = 0.0001
                    if kp.response < response_threshold:
                        continue
                # ORB响应值范围不同，暂不过滤
                
                # 基于尺度过滤 - UI元素通常有合理的尺度 (暂时禁用)
                # if method == 'sift':
                #     if kp.octave < -1 or kp.octave > 3:  # 过滤极端尺度
                #         continue
                # else:  # ORB
                #     if kp.octave < 0 or kp.octave > 5:  # ORB octave范围
                #         continue
                
                # 基于位置过滤 - 避免边缘噪声
                img_margin = 10  # 图像边缘margin
                x, y = kp.pt
                # 这里需要图像尺寸，先跳过位置过滤
                
                filtered_keypoints.append(kp)
                filtered_indices.append(i)
            
            # 过滤描述符
            if filtered_indices and descriptors is not None:
                filtered_descriptors = descriptors[filtered_indices]
            else:
                filtered_descriptors = None
            
            # 基于响应强度排序，保留前N个最强特征
            if len(filtered_keypoints) > 80:  # 增加特征数量限制
                # 按响应强度排序
                sorted_pairs = sorted(zip(filtered_keypoints, range(len(filtered_keypoints))), 
                                    key=lambda x: x[0].response, reverse=True)
                
                filtered_keypoints = [pair[0] for pair in sorted_pairs[:80]]
                if filtered_descriptors is not None:
                    indices = [pair[1] for pair in sorted_pairs[:80]]
                    filtered_descriptors = filtered_descriptors[indices]
            
            return filtered_keypoints, filtered_descriptors
            
        except Exception as e:
            self.logger.error(f"特征过滤失败: {e}")
            return keypoints, descriptors
    
    def _validate_detected_elements(self, elements: List[Dict], image_shape: Tuple) -> List[Dict]:
        """
        验证检测到的元素，移除明显的误检
        
        Args:
            elements: 检测到的元素列表
            image_shape: 图像尺寸 (height, width, channels)
            
        Returns:
            List[Dict]: 验证后的元素列表
        """
        try:
            validated_elements = []
            img_height, img_width = image_shape[:2]
            
            for element in elements:
                # 基本尺寸验证
                if element['type'] == 'circle':
                    radius = element.get('radius', 0)
                    # 圆形半径合理性检查
                    if radius < 5 or radius > min(img_width, img_height) // 4:
                        continue
                
                elif element['type'] in ['rectangle', 'square']:
                    bounds = element.get('bounds', [0, 0, 0, 0])
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]
                    
                    # 矩形尺寸合理性检查
                    if width < 10 or height < 10:
                        continue
                    if width > img_width * 0.8 or height > img_height * 0.8:
                        continue
                    
                    # 长宽比合理性检查
                    aspect_ratio = width / height if height > 0 else 0
                    if aspect_ratio < 0.1 or aspect_ratio > 10:
                        continue
                
                # 位置合理性检查
                if element['type'] == 'circle':
                    center = element.get('center', (0, 0))
                    if (center[0] < 0 or center[0] >= img_width or 
                        center[1] < 0 or center[1] >= img_height):
                        continue
                else:
                    bounds = element.get('bounds', [0, 0, 0, 0])
                    if (bounds[0] < 0 or bounds[1] < 0 or 
                        bounds[2] > img_width or bounds[3] > img_height):
                        continue
                
                # 置信度检查
                confidence = element.get('confidence', 0)
                if confidence < 0.1:  # 过滤置信度过低的检测
                    continue
                
                validated_elements.append(element)
            
            self.logger.info(f"元素验证: 输入{len(elements)}个，验证通过{len(validated_elements)}个")
            return validated_elements
            
        except Exception as e:
            self.logger.error(f"元素验证失败: {e}")
            return elements