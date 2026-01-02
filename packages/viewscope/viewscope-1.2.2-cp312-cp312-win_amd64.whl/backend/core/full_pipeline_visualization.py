#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Pipeline Visualization - Complete Detection Coverage Analysis
Shows all detection steps and evaluates 100% recognition achievement
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import time

# Import all detectors
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector
from improved_icon_detector import ImprovedIconDetector
from improved_signal_detector import ImprovedSignalDetector
from precise_circle_detector import PreciseCircleDetector

class FullPipelineRenderer:
    """Complete pipeline renderer for 100% detection analysis"""

    def __init__(self):
        self.font = self._load_chinese_font()
        self.colors = self._define_comprehensive_colors()
        self.detection_stats = {}

    def _load_chinese_font(self):
        """Load Chinese font"""
        try:
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        return ImageFont.truetype(font_path, 16)
                    except:
                        continue
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()

    def _define_comprehensive_colors(self):
        """Define comprehensive color scheme for all elements"""
        return {
            # Circles - Different types
            'circle_auxiliary': (255, 0, 255),      # Purple - Auxiliary gauges
            'circle_main': (128, 0, 255),           # Blue-purple - Main gauges
            'circle_indicator': (255, 128, 0),      # Orange - Status indicators

            # Icons - Specific types
            'icon_lightning': (255, 215, 0),        # Gold - Lightning (charging)
            'icon_signal': (50, 205, 50),           # Lime - Signal bars
            'icon_clock': (255, 140, 0),            # Dark orange - Clock/time
            'icon_status': (255, 69, 0),            # Red-orange - Status

            # Signal strength bars
            'signal_strength': (255, 165, 0),       # Orange - Signal strength
            'signal_battery': (0, 255, 0),          # Green - Battery level

            # Text by language
            'text_chinese': (0, 255, 128),          # Green - Chinese
            'text_english': (255, 255, 0),          # Yellow - English
            'text_numeric': (255, 128, 255),        # Pink - Numbers
            'text_mixed': (0, 255, 255),            # Cyan - Mixed content
            'text_symbol': (255, 192, 203),         # Light pink - Symbols

            # Detection process
            'detection_roi': (128, 128, 128),       # Gray - ROI boundaries
            'exclusion_zone': (255, 0, 0),          # Red - Excluded areas
            'success_mark': (0, 255, 0),            # Green - Successful detection
        }

    def draw_chinese_text(self, image, text, position, color, font_size=16):
        """Draw Chinese text with specified font size"""
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)

            if font_size != 16:
                try:
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                    else:
                        font = self.font
                except:
                    font = self.font
            else:
                font = self.font

            draw.text(position, text, font=font, fill=color)
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except:
            return image

    def analyze_detection_coverage(self, image, all_detections):
        """Analyze detection coverage and identify potential missed elements"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        coverage_analysis = {
            'detected_regions': [],
            'potential_missed': [],
            'coverage_percentage': 0,
            'analysis_details': {}
        }

        # Mark all detected regions
        detected_mask = np.zeros((height, width), dtype=np.uint8)

        for detection in all_detections:
            bounds = detection['bounds']
            if len(bounds) == 4:
                x, y, w, h = bounds
                cv2.rectangle(detected_mask, (x, y), (x + w, y + h), 255, -1)
            else:
                x1, y1, x2, y2 = bounds
                cv2.rectangle(detected_mask, (x1, y1), (x2, y2), 255, -1)

        # Analyze potential missed areas using edge detection
        edges = cv2.Canny(gray, 30, 100)

        # Find contours in edge image
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        potential_missed = 0
        total_significant_areas = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Significant area threshold
                total_significant_areas += 1
                x, y, w, h = cv2.boundingRect(contour)

                # Check if this area overlaps with detected regions
                roi_mask = detected_mask[y:y+h, x:x+w]
                overlap_ratio = np.sum(roi_mask > 0) / (w * h)

                if overlap_ratio < 0.3:  # Less than 30% overlap
                    potential_missed += 1
                    coverage_analysis['potential_missed'].append({
                        'bounds': (x, y, w, h),
                        'area': area,
                        'overlap_ratio': overlap_ratio
                    })

        # Calculate coverage percentage
        if total_significant_areas > 0:
            coverage_percentage = ((total_significant_areas - potential_missed) / total_significant_areas) * 100
        else:
            coverage_percentage = 100

        coverage_analysis['coverage_percentage'] = coverage_percentage
        coverage_analysis['analysis_details'] = {
            'total_significant_areas': total_significant_areas,
            'detected_areas': total_significant_areas - potential_missed,
            'missed_areas': potential_missed
        }

        return coverage_analysis

def create_full_pipeline_visualization():
    """Create comprehensive full pipeline visualization with 100% analysis"""

    print("=" * 80)
    print("FULL PIPELINE VISUALIZATION - 100% DETECTION COVERAGE ANALYSIS")
    print("=" * 80)

    # Initialize all detectors
    base_detector = ComprehensiveDetector()
    icon_detector = ImprovedIconDetector()
    signal_detector = ImprovedSignalDetector()
    circle_detector = PreciseCircleDetector()
    renderer = FullPipelineRenderer()

    # Test image
    test_image = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image):
        print(f"Test image not found: {test_image}")
        return

    image = cv2.imread(test_image)
    if image is None:
        print("Failed to load image")
        return

    print(f"Image size: {image.shape[1]}x{image.shape[0]} pixels")

    # Execute full detection pipeline with timing
    print("\n" + "="*50)
    print("EXECUTING FULL DETECTION PIPELINE")
    print("="*50)

    start_time = time.time()

    # Step 1: Base comprehensive detection
    print("Step 1: Comprehensive base detection...")
    step1_start = time.time()
    base_result = base_detector.comprehensive_detection(image)
    step1_time = time.time() - step1_start
    print(f"  Completed in {step1_time:.2f}s")

    # Step 2: Enhanced icon detection
    print("Step 2: Enhanced lightning icon detection...")
    step2_start = time.time()
    lightning_icons = icon_detector.detect_improved_icons(image)
    step2_time = time.time() - step2_start
    print(f"  Completed in {step2_time:.2f}s")

    # Step 3: Signal strength detection
    print("Step 3: Signal strength detection...")
    step3_start = time.time()
    signals = signal_detector.detect_signal_strength_bars(image)
    step3_time = time.time() - step3_start
    print(f"  Completed in {step3_time:.2f}s")

    # Step 4: Use existing validated circles from base detection
    print("Step 4: Extract validated circles...")
    step4_start = time.time()
    if base_result['success']:
        circles = base_result['elements']['circles']
        # Circles are already validated by the comprehensive detector
        print(f"  Using {len(circles)} pre-validated circles")
    else:
        circles = []
    step4_time = time.time() - step4_start
    print(f"  Completed in {step4_time:.2f}s")

    total_time = time.time() - start_time
    print(f"Total pipeline time: {total_time:.2f}s")

    if not base_result['success']:
        print(f"Base detection failed: {base_result.get('error', 'Unknown error')}")
        return

    # Extract all results
    text_regions = base_result['elements']['text_regions']

    # Collect all detections for coverage analysis
    all_detections = []
    all_detections.extend(circles)
    all_detections.extend(lightning_icons)
    all_detections.extend(signals)
    all_detections.extend(text_regions)

    print(f"\n" + "="*50)
    print("DETECTION RESULTS SUMMARY")
    print("="*50)
    print(f"Circles: {len(circles)}")
    print(f"Lightning Icons: {len(lightning_icons)}")
    print(f"Signal Strength: {len(signals)}")
    print(f"Text Regions: {len(text_regions)}")
    print(f"Total Elements: {len(all_detections)}")

    # Analyze coverage
    print(f"\n" + "="*50)
    print("COVERAGE ANALYSIS")
    print("="*50)
    coverage_analysis = renderer.analyze_detection_coverage(image, all_detections)

    coverage_pct = coverage_analysis['coverage_percentage']
    analysis_details = coverage_analysis['analysis_details']

    print(f"Detection Coverage: {coverage_pct:.1f}%")
    print(f"Total Significant Areas: {analysis_details['total_significant_areas']}")
    print(f"Detected Areas: {analysis_details['detected_areas']}")
    print(f"Potential Missed Areas: {analysis_details['missed_areas']}")

    # Create comprehensive visualization
    print(f"\n" + "="*50)
    print("CREATING COMPREHENSIVE VISUALIZATION")
    print("="*50)

    result_image = image.copy()

    # Draw all circles with detailed information
    for i, circle in enumerate(circles):
        center = circle['center']
        radius = circle['radius']
        semantic_type = circle.get('semantic_type', 'unknown')
        validation_score = circle.get('validation_score', 0)

        # Choose color based on type
        if 'auxiliary' in semantic_type:
            color = renderer.colors['circle_auxiliary']
            type_text = "辅助仪表"
        elif 'main' in semantic_type:
            color = renderer.colors['circle_main']
            type_text = "主仪表"
        else:
            color = renderer.colors['circle_indicator']
            type_text = "状态指示器"

        thickness = max(2, int(validation_score * 6))

        # Draw circle
        cv2.circle(result_image, center, radius, color, thickness)
        cv2.circle(result_image, center, 3, color, -1)

        # Draw label with validation score
        label_text = f"C{i+1}:{type_text}"
        score_text = f"验证:{validation_score:.2f}"
        label_pos = (center[0] - 50, center[1] - radius - 35)
        score_pos = (center[0] - 30, center[1] - radius - 20)

        result_image = renderer.draw_chinese_text(result_image, label_text, label_pos, color, font_size=12)
        result_image = renderer.draw_chinese_text(result_image, score_text, score_pos, color, font_size=10)

    # Draw lightning icons with detailed analysis
    for i, icon in enumerate(lightning_icons):
        bounds = icon['bounds']
        if len(bounds) == 4:
            x, y, w, h = bounds
        else:
            x, y, w, h = bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1]

        confidence = icon['confidence']
        method = icon.get('detection_method', 'unknown')

        color = renderer.colors['icon_lightning']

        # Draw icon with emphasis
        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 3)
        center = (x + w//2, y + h//2)
        cv2.circle(result_image, center, 2, color, -1)

        # Detailed labels
        main_label = f"L{i+1}:闪电图标"
        detail_label = f"置信:{confidence:.2f} {method[:8]}"

        label_pos = (x - 5, y - 30)
        detail_pos = (x - 5, y - 15)

        result_image = renderer.draw_chinese_text(result_image, main_label, label_pos, color, font_size=12)
        result_image = renderer.draw_chinese_text(result_image, detail_label, detail_pos, color, font_size=10)

    # Draw signal strength indicators
    for i, signal in enumerate(signals):
        bounds = signal['bounds']
        x, y, w, h = bounds
        bar_count = signal['bar_count']
        confidence = signal['confidence']

        color = renderer.colors['signal_strength']

        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 2)

        main_label = f"S{i+1}:信号强度({bar_count}柱)"
        detail_label = f"置信:{confidence:.2f}"

        label_pos = (x, y - 25)
        detail_pos = (x, y - 10)

        result_image = renderer.draw_chinese_text(result_image, main_label, label_pos, color, font_size=12)
        result_image = renderer.draw_chinese_text(result_image, detail_label, detail_pos, color, font_size=10)

    # Draw text regions by category
    for i, text_region in enumerate(text_regions):
        bounds = text_region['bounds']
        content = text_region['text']
        language = text_region.get('language', 'unknown')
        confidence = text_region.get('confidence', 0)

        # Choose color by language
        color_map = {
            'chinese': renderer.colors['text_chinese'],
            'english': renderer.colors['text_english'],
            'numeric': renderer.colors['text_numeric'],
            'mixed': renderer.colors['text_mixed']
        }
        color = color_map.get(language, renderer.colors['text_mixed'])

        # Draw bounding box
        if len(bounds) == 4:
            x1, y1, x2, y2 = bounds
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 1)

        # Draw content label
        lang_map = {'chinese': '中', 'english': '英', 'numeric': '数', 'mixed': '混'}
        lang_abbrev = lang_map.get(language, '?')

        content_label = f"[{lang_abbrev}]{content}"
        content_pos = (x1, y1 - 15)
        result_image = renderer.draw_chinese_text(result_image, content_label, content_pos, color, font_size=10)

    # Draw potential missed areas
    for i, missed in enumerate(coverage_analysis['potential_missed'][:5]):  # Show top 5
        x, y, w, h = missed['bounds']
        area = missed['area']

        if area > 200:  # Only show significant missed areas
            color = (0, 0, 255)  # Red for missed
            cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 1)

            missed_label = f"?遗漏区域{area:.0f}"
            missed_pos = (x, y - 10)
            result_image = renderer.draw_chinese_text(result_image, missed_label, missed_pos, color, font_size=9)

    # Add comprehensive legend
    legend_items = [
        (f"FULL PIPELINE ANALYSIS - Coverage: {coverage_pct:.1f}%", (255, 255, 255)),
        ("", (0, 0, 0)),  # Spacer
        ("Circle Detection:", renderer.colors['circle_auxiliary']),
        (f"  Found {len(circles)} validated circles", renderer.colors['circle_auxiliary']),
        ("Lightning Icon Detection:", renderer.colors['icon_lightning']),
        (f"  Found {len(lightning_icons)} charging indicators", renderer.colors['icon_lightning']),
        ("Signal Strength Detection:", renderer.colors['signal_strength']),
        (f"  Found {len(signals)} signal indicators", renderer.colors['signal_strength']),
        ("Text Recognition:", renderer.colors['text_chinese']),
        (f"  Found {len(text_regions)} text regions", renderer.colors['text_chinese']),
        ("", (0, 0, 0)),  # Spacer
        ("Detection Quality:", (255, 255, 255)),
        (f"Total Elements: {len(all_detections)}", (255, 255, 255)),
        (f"Pipeline Time: {total_time:.2f}s", (255, 255, 255))
    ]

    for i, (label, color) in enumerate(legend_items):
        if label:  # Skip empty spacers
            y_pos = 25 + i * 14
            result_image = renderer.draw_chinese_text(result_image, label, (10, y_pos), color, font_size=10)

    # Add performance statistics
    stats_items = [
        f"PERFORMANCE ANALYSIS",
        f"Step 1 (Base): {step1_time:.2f}s",
        f"Step 2 (Icons): {step2_time:.2f}s",
        f"Step 3 (Signals): {step3_time:.2f}s",
        f"Step 4 (Circles): {step4_time:.2f}s",
        f"Total Time: {total_time:.2f}s",
        "",
        f"COVERAGE ASSESSMENT:",
        f"Detected: {analysis_details['detected_areas']}",
        f"Missed: {analysis_details['missed_areas']}",
        f"Coverage: {coverage_pct:.1f}%",
        "",
        f"DETECTION SUCCESS:",
        f"Lightning: {'YES' if len(lightning_icons) > 0 else 'NO'}",
        f"Signals: {'YES' if len(signals) > 0 else 'NO'}",
        f"Circles: {'YES' if len(circles) > 0 else 'NO'}",
        f"Text: {'YES' if len(text_regions) > 0 else 'NO'}"
    ]

    stats_x = image.shape[1] - 200
    for i, text in enumerate(stats_items):
        if text:  # Skip empty lines
            y_pos = 25 + i * 14
            color = (255, 255, 0) if ":" in text and i < 6 else (200, 200, 200)
            result_image = renderer.draw_chinese_text(result_image, text, (stats_x, y_pos), color, font_size=9)

    # Save comprehensive result
    output_path = "../../full_pipeline_analysis.png"
    cv2.imwrite(output_path, result_image)

    print(f"\nFull pipeline analysis saved: {output_path}")

    # Final assessment
    print(f"\n" + "="*50)
    print("FINAL 100% DETECTION ASSESSMENT")
    print("="*50)

    success_criteria = {
        'circles': len(circles) >= 2,
        'lightning_icons': len(lightning_icons) >= 1,
        'signals': len(signals) >= 1,
        'text_regions': len(text_regions) >= 10,
        'coverage': coverage_pct >= 85.0
    }

    passed_criteria = sum(success_criteria.values())
    total_criteria = len(success_criteria)
    overall_success = passed_criteria == total_criteria

    for criterion, passed in success_criteria.items():
        status = "PASS" if passed else "FAIL"
        print(f"{criterion.upper()}: {status}")

    print(f"\nOVERALL SUCCESS RATE: {passed_criteria}/{total_criteria} ({passed_criteria/total_criteria*100:.1f}%)")
    print(f"DETECTION COVERAGE: {coverage_pct:.1f}%")
    print(f"100% TARGET: {'ACHIEVED' if overall_success and coverage_pct >= 95 else 'NEARLY ACHIEVED'}")

    return {
        'overall_success': overall_success,
        'coverage_percentage': coverage_pct,
        'detection_counts': {
            'circles': len(circles),
            'lightning_icons': len(lightning_icons),
            'signals': len(signals),
            'text_regions': len(text_regions)
        },
        'performance_time': total_time
    }

if __name__ == "__main__":
    result = create_full_pipeline_visualization()