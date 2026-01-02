#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Precise Lightning Detection - Accurately locate the real lightning charging icon
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict

# Import detectors
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_detector import ComprehensiveDetector
from improved_signal_detector import ImprovedSignalDetector
from enhanced_ocr_corrector import EnhancedOCRCorrector

class PreciseLightningDetector:
    """Precise lightning icon detector focusing on the real charging icon"""

    def __init__(self):
        pass

    def detect_real_lightning_icon(self, image: np.ndarray) -> List[Dict]:
        """Detect the real lightning charging icon with high precision"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        # Focus on the actual lightning icon area - very left side
        roi_x1 = 0
        roi_x2 = int(width * 0.1)  # Left 10% only
        roi_y1 = int(height * 0.25)  # From 25% down
        roi_y2 = int(height * 0.6)   # To 60% down - where lightning icon actually is

        roi = gray[roi_y1:roi_y2, roi_x1:roi_x2]

        print(f"Precise lightning search ROI: ({roi_x1},{roi_y1}) to ({roi_x2},{roi_y2})")

        lightning_icons = []

        # Method 1: Template matching with precise templates
        templates = self._create_precise_lightning_templates()
        for i, template in enumerate(templates):
            result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.6)  # Higher threshold for precision

            for pt in zip(*locations[::-1]):
                x, y = pt
                confidence = float(result[y, x])

                # Adjust coordinates back to full image
                full_x = x + roi_x1
                full_y = y + roi_y1

                lightning_icons.append({
                    'type': 'icon',
                    'icon_type': 'lightning',
                    'bounds': (full_x, full_y, template.shape[1], template.shape[0]),
                    'center': (full_x + template.shape[1]//2, full_y + template.shape[0]//2),
                    'confidence': confidence,
                    'detection_method': f'precise_template_{i}',
                    'description': 'Real Lightning Charging Icon'
                })

        # Method 2: Edge-based shape detection
        edges = cv2.Canny(roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if 30 <= area <= 150:  # Lightning icon size range
                x, y, w, h = cv2.boundingRect(contour)

                # Lightning characteristics
                aspect_ratio = h / w if w > 0 else 0
                if 1.5 <= aspect_ratio <= 3.0:  # Tall and narrow

                    # Check if it has the zigzag pattern
                    if self._has_lightning_shape(contour):
                        full_x = x + roi_x1
                        full_y = y + roi_y1

                        lightning_icons.append({
                            'type': 'icon',
                            'icon_type': 'lightning',
                            'bounds': (full_x, full_y, w, h),
                            'center': (full_x + w//2, full_y + h//2),
                            'confidence': 0.8,
                            'detection_method': 'shape_analysis',
                            'description': 'Lightning Icon (Shape Detected)'
                        })

        # Remove duplicates
        lightning_icons = self._remove_duplicate_lightning_icons(lightning_icons)

        print(f"Precise lightning detection found: {len(lightning_icons)} icons")
        for icon in lightning_icons:
            print(f"  - Position: {icon['bounds']}, Confidence: {icon['confidence']:.2f}")

        return lightning_icons

    def _create_precise_lightning_templates(self):
        """Create precise lightning templates based on actual icon appearance"""
        templates = []

        # Create templates matching the actual lightning icon
        sizes = [(8, 16), (10, 18), (12, 20), (14, 22)]

        for width, height in sizes:
            template = np.zeros((height, width), dtype=np.uint8)

            # Draw precise lightning shape
            # Top part: diagonal line from top-left to middle-right
            cv2.line(template, (2, 2), (width-2, height//2), 255, 1)

            # Middle part: small horizontal line (lightning characteristic)
            cv2.line(template, (width//3, height//2-1), (width//2+1, height//2-1), 255, 1)

            # Bottom part: diagonal line from middle-left to bottom-right
            cv2.line(template, (width//3, height//2+1), (width-2, height-2), 255, 1)

            templates.append(template)

        return templates

    def _has_lightning_shape(self, contour):
        """Check if contour has lightning-like zigzag shape"""
        # Approximate the contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Lightning should have at least 4-6 points (zigzag)
        if len(approx) < 4 or len(approx) > 8:
            return False

        # Check if it has alternating directions (zigzag pattern)
        if len(approx) >= 4:
            # Calculate direction changes
            direction_changes = 0
            for i in range(1, len(approx) - 1):
                p1 = approx[i-1][0]
                p2 = approx[i][0]
                p3 = approx[i+1][0]

                # Check if direction changes (zigzag pattern)
                dx1 = p2[0] - p1[0]
                dx2 = p3[0] - p2[0]

                if dx1 * dx2 < 0:  # Direction change in x
                    direction_changes += 1

            return direction_changes >= 1  # At least one direction change

        return False

    def _remove_duplicate_lightning_icons(self, icons):
        """Remove duplicate lightning icon detections"""
        if len(icons) <= 1:
            return icons

        # Sort by confidence
        icons.sort(key=lambda x: x['confidence'], reverse=True)

        filtered = []
        for icon in icons:
            is_duplicate = False
            for existing in filtered:
                # Calculate distance between centers
                dist = np.sqrt((icon['center'][0] - existing['center'][0])**2 +
                             (icon['center'][1] - existing['center'][1])**2)
                if dist < 20:  # Within 20 pixels - considered duplicate
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(icon)

        return filtered[:2]  # Keep max 2 lightning icons


class PreciseRenderer:
    """Renderer for precise lightning detection"""

    def __init__(self):
        self.font = self._load_chinese_font()
        self.colors = {
            'circle_auxiliary': (255, 0, 255),
            'icon_lightning': (255, 215, 0),
            'signal_strength': (255, 140, 0),
            'text_corrected': (0, 255, 0),
            'text_mixed': (0, 255, 255),
        }

    def _load_chinese_font(self):
        try:
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
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

    def draw_chinese_text(self, image, text, position, color, font_size=16):
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)

            if font_size != 16:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", font_size)
                except:
                    font = self.font
            else:
                font = self.font

            draw.text(position, text, font=font, fill=color)
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except:
            return image


def create_precise_lightning_visualization():
    """Create visualization focusing on precise lightning icon detection"""

    print("=" * 60)
    print("PRECISE LIGHTNING ICON DETECTION")
    print("=" * 60)

    # Initialize components
    base_detector = ComprehensiveDetector()
    lightning_detector = PreciseLightningDetector()
    signal_detector = ImprovedSignalDetector()
    ocr_corrector = EnhancedOCRCorrector()
    renderer = PreciseRenderer()

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

    # Execute detections
    print("\nExecuting precise detection...")
    base_result = base_detector.comprehensive_detection(image)

    if not base_result['success']:
        print(f"Base detection failed")
        return

    # Precise lightning detection
    print("Executing PRECISE lightning detection...")
    lightning_icons = lightning_detector.detect_real_lightning_icon(image)

    # Other detections
    signals = signal_detector.detect_signal_strength_bars(image)
    circles = base_result['elements']['circles']
    text_regions = ocr_corrector.correct_ocr_text(base_result['elements']['text_regions'])

    print(f"\nPrecise detection results:")
    print(f"Lightning Icons: {len(lightning_icons)} (PRECISE)")
    print(f"Circles: {len(circles)}")
    print(f"Signals: {len(signals)}")
    print(f"Text: {len(text_regions)}")

    # Create visualization
    result_image = image.copy()

    # Draw lightning icons prominently
    for i, icon in enumerate(lightning_icons):
        bounds = icon['bounds']
        x, y, w, h = bounds
        confidence = icon['confidence']
        method = icon['detection_method']

        color = renderer.colors['icon_lightning']

        # Draw with emphasis
        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 4)
        center = (x + w//2, y + h//2)
        cv2.circle(result_image, center, 3, color, -1)

        # Labels
        main_label = f"FOUND! 闪电图标 #{i+1}"
        detail_label = f"置信:{confidence:.2f} ({method[:8]})"

        label_pos = (x - 10, y - 30)
        detail_pos = (x - 10, y - 15)

        result_image = renderer.draw_chinese_text(result_image, main_label, label_pos, color, font_size=12)
        result_image = renderer.draw_chinese_text(result_image, detail_label, detail_pos, color, font_size=10)

    # Draw other elements simply
    for i, circle in enumerate(circles):
        center = circle['center']
        radius = circle['radius']
        cv2.circle(result_image, center, radius, renderer.colors['circle_auxiliary'], 2)

    for i, signal in enumerate(signals):
        bounds = signal['bounds']
        x, y, w, h = bounds
        cv2.rectangle(result_image, (x, y), (x + w, y + h), renderer.colors['signal_strength'], 2)

    # Status
    status_items = [
        f"PRECISE LIGHTNING DETECTION RESULTS:",
        f"Found: {len(lightning_icons)} lightning charging icons",
        f"Method: Focused ROI + Template + Shape Analysis",
        f"Success: {'YES' if len(lightning_icons) > 0 else 'NO - NEED ADJUSTMENT'}"
    ]

    for i, text in enumerate(status_items):
        y_pos = 30 + i * 16
        color = (0, 255, 0) if len(lightning_icons) > 0 and i == 3 else (255, 255, 255)
        result_image = renderer.draw_chinese_text(result_image, text, (10, y_pos), color, font_size=12)

    # Save result
    output_path = "../../precise_lightning_result.png"
    cv2.imwrite(output_path, result_image)

    print(f"\nPrecise lightning detection saved: {output_path}")
    print(f"Status: {'SUCCESS' if len(lightning_icons) > 0 else 'NEEDS ADJUSTMENT'}")

    return lightning_icons


if __name__ == "__main__":
    result = create_precise_lightning_visualization()