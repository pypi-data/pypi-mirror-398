#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved Signal Strength (Vertical Bar) Detector - Enhanced Precision for 2025
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Tuple, Optional

class ImprovedSignalDetector:
    """Enhanced signal strength detector focusing on vertical bar patterns"""

    def __init__(self):
        self.min_bar_width = 3
        self.max_bar_width = 15
        self.min_bar_height = 8
        self.max_bar_height = 40
        self.min_bars_in_signal = 3  # Minimum bars to form signal pattern
        self.max_bar_spacing = 20   # Maximum distance between bars

    def detect_signal_strength_bars(self, image: np.ndarray) -> List[Dict]:
        """Enhanced signal strength detection with strict validation"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        # Focus search on top-left corner where signal bars typically appear
        roi_width = min(width // 4, 300)  # Max 300 pixels wide
        roi_height = min(height // 2, 200)  # Max 200 pixels high

        roi = gray[0:roi_height, 0:roi_width]

        print(f"Signal detection ROI: {roi_width}x{roi_height}")

        # Phase 1: Find vertical bar candidates
        bar_candidates = self._find_vertical_bar_candidates(roi)

        # Phase 2: Group bars into signal patterns
        signal_groups = self._group_bars_into_signals(bar_candidates)

        # Phase 3: Validate signal patterns
        validated_signals = self._validate_signal_patterns(signal_groups, roi)

        print(f"Signal detection: {len(bar_candidates)} candidates -> {len(signal_groups)} groups -> {len(validated_signals)} signals")

        return validated_signals

    def _find_vertical_bar_candidates(self, roi: np.ndarray) -> List[Dict]:
        """Find potential vertical bar elements"""
        candidates = []

        # Enhanced edge detection for small structures
        edges = cv2.Canny(roi, 30, 100)

        # Morphological operations to connect broken edges
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_close)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            analysis = self._analyze_bar_candidate(contour)
            if analysis:
                candidates.append(analysis)

        return candidates

    def _analyze_bar_candidate(self, contour: np.ndarray) -> Optional[Dict]:
        """Analyze if contour could be a signal bar"""
        area = cv2.contourArea(contour)
        if area < 15:  # Too small
            return None

        x, y, w, h = cv2.boundingRect(contour)

        # Size constraints for signal bars
        if not (self.min_bar_width <= w <= self.max_bar_width):
            return None
        if not (self.min_bar_height <= h <= self.max_bar_height):
            return None

        # Aspect ratio - should be taller than wide
        aspect_ratio = h / w if w > 0 else 0
        if aspect_ratio < 1.5:  # Must be significantly taller
            return None

        # Calculate features
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return None

        # Rectangle-like shape check
        rect_area = w * h
        fill_ratio = area / rect_area if rect_area > 0 else 0

        # Signal bars should be fairly solid rectangles
        if fill_ratio < 0.6:
            return None

        return {
            'contour': contour,
            'bounds': (x, y, w, h),
            'area': area,
            'aspect_ratio': aspect_ratio,
            'fill_ratio': fill_ratio,
            'center': (x + w//2, y + h//2)
        }

    def _group_bars_into_signals(self, candidates: List[Dict]) -> List[List[Dict]]:
        """Group nearby bars that could form signal strength patterns"""
        if len(candidates) < self.min_bars_in_signal:
            return []

        # Sort candidates by x-coordinate (left to right)
        sorted_candidates = sorted(candidates, key=lambda c: c['center'][0])

        groups = []
        used = [False] * len(sorted_candidates)

        for i, candidate in enumerate(sorted_candidates):
            if used[i]:
                continue

            # Start a new group
            group = [candidate]
            used[i] = True
            last_x = candidate['center'][0]

            # Find bars to the right that could be part of the same signal
            for j in range(i + 1, len(sorted_candidates)):
                if used[j]:
                    continue

                other_candidate = sorted_candidates[j]
                distance = other_candidate['center'][0] - last_x

                # Check if it's close enough and at similar height
                y_diff = abs(candidate['center'][1] - other_candidate['center'][1])

                if (distance <= self.max_bar_spacing and y_diff <= 15):
                    group.append(other_candidate)
                    used[j] = True
                    last_x = other_candidate['center'][0]
                elif distance > self.max_bar_spacing * 2:
                    break  # Too far, stop looking

            # Only keep groups with enough bars
            if len(group) >= self.min_bars_in_signal:
                groups.append(group)

        return groups

    def _validate_signal_patterns(self, groups: List[List[Dict]], roi: np.ndarray) -> List[Dict]:
        """Validate that grouped bars form actual signal patterns"""
        validated = []

        for group in groups:
            validation = self._validate_single_signal_group(group, roi)
            if validation:
                validated.append(validation)

        return validated

    def _validate_single_signal_group(self, group: List[Dict], roi: np.ndarray) -> Optional[Dict]:
        """Validate a single signal group pattern"""
        if len(group) < self.min_bars_in_signal:
            return None

        # Extract heights and positions
        heights = [bar['bounds'][3] for bar in group]  # height values
        x_positions = [bar['center'][0] for bar in group]
        y_positions = [bar['center'][1] for bar in group]

        # Check for progressive height pattern (typical of signal strength)
        height_pattern_score = self._analyze_height_progression(heights)

        # Check horizontal alignment
        y_variance = np.var(y_positions) if len(y_positions) > 1 else 0
        alignment_score = max(0, 1 - y_variance / 100)  # Penalize poor alignment

        # Check regular spacing
        if len(x_positions) > 1:
            spacings = np.diff(x_positions)
            spacing_variance = np.var(spacings)
            spacing_score = max(0, 1 - spacing_variance / 50)
        else:
            spacing_score = 1.0

        # Overall confidence
        confidence = (height_pattern_score * 0.5 +
                     alignment_score * 0.3 +
                     spacing_score * 0.2)

        # Require minimum confidence
        if confidence < 0.6:
            return None

        # Calculate bounding box for the whole signal
        all_x = []
        all_y = []
        all_w = []
        all_h = []

        for bar in group:
            x, y, w, h = bar['bounds']
            all_x.append(x)
            all_y.append(y)
            all_w.append(w)
            all_h.append(h)

        group_x1 = min(all_x)
        group_y1 = min(all_y)
        group_x2 = max([x + w for x, w in zip(all_x, all_w)])
        group_y2 = max([y + h for y, h in zip(all_y, all_h)])

        return {
            'type': 'signal_strength',
            'chart_type': 'signal_strength',
            'bounds': (group_x1, group_y1, group_x2 - group_x1, group_y2 - group_y1),
            'center': ((group_x1 + group_x2) // 2, (group_y1 + group_y2) // 2),
            'bar_count': len(group),
            'confidence': confidence,
            'semantic_type': 'signal_indicator',
            'description': f'Signal Strength ({len(group)} bars)',
            'pattern_scores': {
                'height_progression': height_pattern_score,
                'alignment': alignment_score,
                'spacing': spacing_score
            },
            'bars': group
        }

    def _analyze_height_progression(self, heights: List[int]) -> float:
        """Analyze if heights show signal-like progression pattern"""
        if len(heights) < 3:
            return 0.5  # Neutral score for too few bars

        # Signal bars typically show increasing height pattern
        increasing_pairs = 0
        total_pairs = len(heights) - 1

        for i in range(total_pairs):
            if heights[i + 1] >= heights[i]:
                increasing_pairs += 1

        # Calculate increasing ratio
        increasing_ratio = increasing_pairs / total_pairs if total_pairs > 0 else 0

        # Bonus for clear progression
        if increasing_ratio >= 0.8:  # Mostly increasing
            height_range = max(heights) - min(heights)
            if height_range >= 10:  # Significant height difference
                return min(1.0, 0.8 + height_range / 100)

        return increasing_ratio * 0.7  # Base score for any increasing pattern

def test_signal_detection():
    """Test the improved signal detector"""
    print("=" * 60)
    print("Improved Signal Strength Detection Test")
    print("=" * 60)

    detector = ImprovedSignalDetector()

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

    # Run signal detection
    signals = detector.detect_signal_strength_bars(image)

    print(f"\nDetected {len(signals)} signal strength indicators")
    print("=" * 40)

    for i, signal in enumerate(signals):
        print(f"Signal {i+1}:")
        print(f"  Position: {signal['bounds']}")
        print(f"  Center: {signal['center']}")
        print(f"  Bar count: {signal['bar_count']}")
        print(f"  Confidence: {signal['confidence']:.3f}")
        print(f"  Description: {signal['description']}")

        if 'pattern_scores' in signal:
            scores = signal['pattern_scores']
            print(f"  Height progression: {scores['height_progression']:.2f}")
            print(f"  Alignment: {scores['alignment']:.2f}")
            print(f"  Spacing: {scores['spacing']:.2f}")

        print()

    return signals

if __name__ == "__main__":
    test_signal_detection()