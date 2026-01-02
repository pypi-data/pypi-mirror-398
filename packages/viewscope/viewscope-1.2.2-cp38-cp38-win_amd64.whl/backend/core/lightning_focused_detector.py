#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightning Focused Detector - Specifically for the real lightning icon
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Tuple, Optional

class LightningFocusedDetector:
    """Specialized detector for the actual lightning icon in the dashboard"""

    def __init__(self):
        self.create_precise_lightning_templates()

    def create_precise_lightning_templates(self) -> List[np.ndarray]:
        """Create templates specifically for the actual lightning icon shape"""
        templates = []

        # Based on the actual icon in the image, create a more accurate template
        sizes = [(10, 16), (12, 18), (14, 20), (16, 22)]

        for width, height in sizes:
            template = np.zeros((height, width), dtype=np.uint8)

            # More accurate lightning shape based on the real icon
            # Top diagonal line (from top-left to right-middle)
            cv2.line(template, (2, 2), (width-2, height//2-1), 255, 2)

            # Middle horizontal segment (lightning characteristic)
            cv2.line(template, (width//3, height//2-2), (width//2+1, height//2-2), 255, 2)

            # Bottom diagonal line (from left-middle to bottom-right)
            cv2.line(template, (width//3, height//2+1), (width-2, height-2), 255, 2)

            # Small thickness variation
            kernel = np.ones((2,2), np.uint8)
            template = cv2.dilate(template, kernel, iterations=1)

            templates.append(template)

        self.lightning_templates = templates
        return templates

    def detect_real_lightning_icon(self, image: np.ndarray) -> List[Dict]:
        """Detect the actual lightning icon with precise positioning"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        # Very focused ROI based on actual icon location
        roi_x1 = 0
        roi_x2 = int(width * 0.12)  # Only left 12%
        roi_y1 = int(height * 0.25) # Start from 25% down
        roi_y2 = int(height * 0.75) # End at 75% down

        roi = gray[roi_y1:roi_y2, roi_x1:roi_x2]
        print(f"Lightning focused ROI: ({roi_x1},{roi_y1}) to ({roi_x2},{roi_y2})")

        lightning_candidates = []

        # Method 1: Template matching with high precision
        for i, template in enumerate(self.lightning_templates):
            result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)

            # Lower threshold but in focused area
            locations = np.where(result >= 0.4)

            for pt in zip(*locations[::-1]):
                x, y = pt
                confidence = float(result[y, x])

                # Adjust back to full image coordinates
                full_x = x + roi_x1
                full_y = y + roi_y1

                lightning_candidates.append({
                    'type': 'icon',
                    'icon_type': 'lightning',
                    'bounds': (full_x, full_y, template.shape[1], template.shape[0]),
                    'center': (full_x + template.shape[1]//2, full_y + template.shape[0]//2),
                    'confidence': confidence,
                    'detection_method': f'focused_template_{i}',
                    'template_size': template.shape
                })

        # Method 2: Shape analysis in focused area
        shape_candidates = self._focused_shape_analysis(roi, roi_x1, roi_y1)
        lightning_candidates.extend(shape_candidates)

        # Method 3: Contour analysis for zigzag pattern
        contour_candidates = self._zigzag_contour_analysis(roi, roi_x1, roi_y1)
        lightning_candidates.extend(contour_candidates)

        # Remove duplicates and select best candidates
        final_candidates = self._select_best_lightning_candidates(lightning_candidates)

        print(f"Lightning detection: {len(lightning_candidates)} candidates -> {len(final_candidates)} final")

        return final_candidates

    def _focused_shape_analysis(self, roi: np.ndarray, offset_x: int, offset_y: int) -> List[Dict]:
        """Focused shape analysis for lightning patterns"""
        candidates = []

        # Multiple edge detection approaches
        edges1 = cv2.Canny(roi, 30, 90)
        edges2 = cv2.Canny(roi, 50, 120)
        combined_edges = cv2.bitwise_or(edges1, edges2)

        # Morphological operations to enhance lightning shape
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        combined_edges = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(combined_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            analysis = self._analyze_lightning_contour(contour, offset_x, offset_y)
            if analysis:
                candidates.append(analysis)

        return candidates

    def _analyze_lightning_contour(self, contour: np.ndarray, offset_x: int, offset_y: int) -> Optional[Dict]:
        """Analyze if contour matches lightning characteristics"""
        area = cv2.contourArea(contour)
        if area < 20 or area > 200:  # Size constraints for lightning icon
            return None

        x, y, w, h = cv2.boundingRect(contour)

        # Lightning icon should be relatively small and tall
        if not (6 <= w <= 20 and 10 <= h <= 25):
            return None

        # Aspect ratio check (taller than wide)
        aspect_ratio = h / w if w > 0 else 0
        if aspect_ratio < 1.2:
            return None

        # Shape complexity analysis
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return None

        complexity = (perimeter ** 2) / area
        if complexity < 12:  # Lightning should have complex edges
            return None

        # Convexity analysis
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        if solidity > 0.9:  # Lightning should be non-convex
            return None

        # Position validation - should be in left area
        center_x = x + w // 2
        if center_x > 100:  # Too far right for lightning icon
            return None

        confidence = self._calculate_lightning_confidence(complexity, solidity, aspect_ratio, area)

        return {
            'type': 'icon',
            'icon_type': 'lightning',
            'bounds': (x + offset_x, y + offset_y, w, h),
            'center': (x + offset_x + w//2, y + offset_y + h//2),
            'confidence': confidence,
            'detection_method': 'focused_shape_analysis',
            'features': {
                'area': area,
                'complexity': complexity,
                'solidity': solidity,
                'aspect_ratio': aspect_ratio
            }
        }

    def _zigzag_contour_analysis(self, roi: np.ndarray, offset_x: int, offset_y: int) -> List[Dict]:
        """Analyze contours for zigzag patterns typical of lightning"""
        candidates = []

        # Binary threshold for clear contours
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert if needed (lightning might be white on dark or dark on white)
        if np.mean(binary) > 127:  # Mostly white, invert
            binary = cv2.bitwise_not(binary)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if self._has_zigzag_pattern(contour):
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)

                if 8 <= w <= 18 and 12 <= h <= 24 and 30 <= area <= 150:
                    confidence = 0.7  # High confidence for zigzag pattern

                    candidates.append({
                        'type': 'icon',
                        'icon_type': 'lightning',
                        'bounds': (x + offset_x, y + offset_y, w, h),
                        'center': (x + offset_x + w//2, y + offset_y + h//2),
                        'confidence': confidence,
                        'detection_method': 'zigzag_pattern_analysis',
                        'pattern_detected': True
                    })

        return candidates

    def _has_zigzag_pattern(self, contour: np.ndarray) -> bool:
        """Check if contour has zigzag pattern characteristic of lightning"""
        # Simplify contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) < 4:  # Need at least 4 points for zigzag
            return False

        # Calculate angles between consecutive segments
        angles = []
        for i in range(len(approx)):
            p1 = approx[i-1][0]
            p2 = approx[i][0]
            p3 = approx[(i+1) % len(approx)][0]

            # Calculate vectors
            v1 = p2 - p1
            v2 = p3 - p2

            # Calculate angle
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1, 1))
            angles.append(angle)

        # Check for alternating angles (zigzag pattern)
        sharp_angles = sum(1 for angle in angles if angle < np.pi/3)  # Less than 60 degrees

        return sharp_angles >= 2  # At least 2 sharp turns

    def _calculate_lightning_confidence(self, complexity: float, solidity: float,
                                      aspect_ratio: float, area: float) -> float:
        """Calculate confidence for lightning detection"""
        confidence = 0.0

        # Complexity score
        if 15 <= complexity <= 40:
            confidence += 0.3
        elif complexity > 12:
            confidence += 0.2

        # Solidity score (non-convex is good)
        if solidity < 0.8:
            confidence += 0.3
        elif solidity < 0.9:
            confidence += 0.15

        # Aspect ratio score
        if 1.5 <= aspect_ratio <= 2.5:
            confidence += 0.25
        elif 1.2 <= aspect_ratio <= 3.0:
            confidence += 0.15

        # Area score
        if 40 <= area <= 120:
            confidence += 0.15
        elif 20 <= area <= 200:
            confidence += 0.1

        return min(1.0, confidence)

    def _select_best_lightning_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Select the best lightning candidates"""
        if not candidates:
            return []

        # Remove duplicates by position
        filtered = []
        for candidate in candidates:
            is_duplicate = False
            for existing in filtered:
                if self._calculate_distance(candidate['center'], existing['center']) < 15:
                    # Keep the one with higher confidence
                    if candidate['confidence'] > existing['confidence']:
                        filtered.remove(existing)
                        filtered.append(candidate)
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(candidate)

        # Sort by confidence and keep top candidates
        filtered.sort(key=lambda x: x['confidence'], reverse=True)

        # Return top 2 candidates maximum
        return filtered[:2]

    def _calculate_distance(self, center1: Tuple[int, int], center2: Tuple[int, int]) -> float:
        """Calculate distance between two centers"""
        return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

def test_lightning_focused_detection():
    """Test the focused lightning detector"""
    print("=" * 60)
    print("Lightning Focused Detection Test")
    print("=" * 60)

    detector = LightningFocusedDetector()

    # Test image
    test_image_path = "../../resources/20250910-100334.png"

    if not os.path.exists(test_image_path):
        print(f"Test image not found: {test_image_path}")
        return

    image = cv2.imread(test_image_path)
    if image is None:
        print("Failed to load test image")
        return

    print(f"Image size: {image.shape[1]}x{image.shape[0]}")

    # Run focused lightning detection
    lightning_icons = detector.detect_real_lightning_icon(image)

    print(f"\nFocused detection results: {len(lightning_icons)} lightning icons found")
    print("=" * 40)

    for i, icon in enumerate(lightning_icons):
        print(f"Lightning Icon {i+1}:")
        print(f"  Position: {icon['bounds']}")
        print(f"  Center: {icon['center']}")
        print(f"  Confidence: {icon['confidence']:.3f}")
        print(f"  Method: {icon['detection_method']}")

        if 'features' in icon:
            features = icon['features']
            print(f"  Area: {features.get('area', 0)}")
            print(f"  Complexity: {features.get('complexity', 0):.1f}")
            print(f"  Solidity: {features.get('solidity', 0):.2f}")
            print(f"  Aspect Ratio: {features.get('aspect_ratio', 0):.2f}")

        if 'template_size' in icon:
            print(f"  Template Size: {icon['template_size']}")

        print()

    return lightning_icons

if __name__ == "__main__":
    test_lightning_focused_detection()