#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Precise Lightning Locator - Find the exact position of the real lightning charging icon
Based on user feedback: lightning icon should be between signal strength and C1 gauge
"""

import cv2
import numpy as np
import os

def locate_real_lightning_icon():
    """Locate the real lightning charging icon in the left sidebar"""

    print("=" * 60)
    print("PRECISE LIGHTNING ICON LOCATOR")
    print("=" * 60)

    # Load test image
    test_image = "../../resources/20250910-100334.png"
    if not os.path.exists(test_image):
        print(f"Test image not found: {test_image}")
        return

    image = cv2.imread(test_image)
    if image is None:
        print("Failed to load image")
        return

    print(f"Image size: {image.shape[1]}x{image.shape[0]} pixels")

    # Focus on the left sidebar where all icons are
    sidebar_width = 120  # Left 120 pixels - the icon sidebar
    roi = image[0:image.shape[0], 0:sidebar_width]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    print(f"Analyzing sidebar: {sidebar_width}x{image.shape[0]} pixels")

    # The left sidebar has vertical layout:
    # 1. Signal strength bars (top area ~y=130-140)
    # 2. Lightning charging icon (middle area ~y=170-185) <- TARGET
    # 3. Clock icon (lower area ~y=220-235)
    # 4. C1 gauge (bottom area ~y=270-290)

    # Define search region for lightning icon (between signal and clock)
    lightning_y_min = 160  # Below signal strength
    lightning_y_max = 200  # Above clock icon
    lightning_x_min = 50   # In the icon column
    lightning_x_max = 90   # Right side of icon column

    lightning_roi = gray_roi[lightning_y_min:lightning_y_max, lightning_x_min:lightning_x_max]
    print(f"Lightning search region: ({lightning_x_min},{lightning_y_min}) to ({lightning_x_max},{lightning_y_max})")

    # Method 1: Look for white lightning-shaped pixels
    print("\\nMethod 1: White pixel detection in lightning region...")

    # Threshold for bright pixels (lightning is white)
    _, binary = cv2.threshold(lightning_roi, 200, 255, cv2.THRESH_BINARY)

    # Find contours in lightning region
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    lightning_candidates = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if 10 <= area <= 100:  # Lightning icon size range
            x, y, w, h = cv2.boundingRect(contour)

            # Adjust coordinates back to full image
            full_x = x + lightning_x_min
            full_y = y + lightning_y_min

            aspect_ratio = h / w if w > 0 else 0
            if 1.0 <= aspect_ratio <= 3.0:  # Lightning should be taller than wide
                lightning_candidates.append({
                    'position': (full_x, full_y),
                    'size': (w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'center': (full_x + w//2, full_y + h//2)
                })
                print(f"Candidate {i+1}: pos({full_x},{full_y}) size({w}x{h}) area={area:.1f} ratio={aspect_ratio:.2f}")

    # Method 2: Template matching with very precise templates
    print(f"\\nMethod 2: Template matching in lightning region...")

    # Create small lightning templates specifically for this region
    templates = []

    # Template 1: Standard lightning bolt (10x16)
    template1 = np.zeros((16, 10), dtype=np.uint8)
    # Draw lightning shape
    cv2.line(template1, (2, 2), (7, 6), 255, 1)    # Top diagonal
    cv2.line(template1, (3, 6), (6, 6), 255, 1)    # Middle horizontal
    cv2.line(template1, (3, 7), (8, 14), 255, 1)   # Bottom diagonal
    templates.append(("10x16_bolt", template1))

    # Template 2: Thicker lightning (12x18)
    template2 = np.zeros((18, 12), dtype=np.uint8)
    cv2.line(template2, (2, 2), (8, 7), 255, 2)    # Top diagonal
    cv2.line(template2, (3, 7), (7, 7), 255, 1)    # Middle horizontal
    cv2.line(template2, (4, 8), (9, 16), 255, 2)   # Bottom diagonal
    templates.append(("12x18_thick", template2))

    template_matches = []
    for name, template in templates:
        result = cv2.matchTemplate(lightning_roi, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.3)  # Lower threshold for detection

        for pt in zip(*locations[::-1]):
            x, y = pt
            confidence = float(result[y, x])

            # Adjust coordinates back to full image
            full_x = x + lightning_x_min
            full_y = y + lightning_y_min

            template_matches.append({
                'template': name,
                'position': (full_x, full_y),
                'confidence': confidence,
                'center': (full_x + template.shape[1]//2, full_y + template.shape[0]//2)
            })
            print(f"Template {name}: pos({full_x},{full_y}) confidence={confidence:.3f}")

    # Method 3: Analyze pixel patterns in the expected area
    print(f"\\nMethod 3: Direct pixel analysis...")

    # Look for the exact lightning pattern at expected coordinates
    expected_areas = [
        (60, 170, 80, 190),  # Area 1
        (65, 175, 85, 195),  # Area 2
        (70, 172, 90, 192),  # Area 3
    ]

    pixel_candidates = []
    for i, (x1, y1, x2, y2) in enumerate(expected_areas):
        roi_area = gray_roi[y1:y2, x1:x2]
        if roi_area.size > 0:
            white_pixels = np.sum(roi_area > 200)
            total_pixels = roi_area.size
            white_ratio = white_pixels / total_pixels

            if white_ratio > 0.1:  # At least 10% white pixels
                center_x = x1 + (x2 - x1) // 2
                center_y = y1 + (y2 - y1) // 2
                pixel_candidates.append({
                    'area': i + 1,
                    'position': (x1, y1),
                    'center': (center_x, center_y),
                    'white_ratio': white_ratio,
                    'white_pixels': white_pixels
                })
                print(f"Area {i+1}: pos({x1},{y1}) white_ratio={white_ratio:.3f} pixels={white_pixels}")

    # Create result visualization
    result_image = roi.copy()

    # Draw lightning search region
    cv2.rectangle(result_image, (lightning_x_min, lightning_y_min),
                  (lightning_x_max, lightning_y_max), (0, 255, 0), 2)

    # Mark all candidates
    for i, candidate in enumerate(lightning_candidates):
        x, y = candidate['position']
        w, h = candidate['size']
        cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 1)
        cv2.putText(result_image, f"C{i+1}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)

    for i, match in enumerate(template_matches):
        x, y = match['position']
        cv2.circle(result_image, (x, y), 3, (0, 255, 255), -1)
        cv2.putText(result_image, f"T{i+1}", (x+5, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)

    for i, candidate in enumerate(pixel_candidates):
        center = candidate['center']
        cv2.circle(result_image, center, 5, (255, 255, 0), 2)
        cv2.putText(result_image, f"P{i+1}", (center[0]+8, center[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 0), 1)

    # Save result
    output_path = "../../precise_lightning_location.png"
    cv2.imwrite(output_path, result_image)

    print(f"\\nPrecise location analysis saved: {output_path}")
    print(f"\\nSUMMARY:")
    print(f"White pixel candidates: {len(lightning_candidates)}")
    print(f"Template matches: {len(template_matches)}")
    print(f"Pixel analysis areas: {len(pixel_candidates)}")

    # Recommend best candidate
    all_candidates = []

    # Add shape candidates
    for candidate in lightning_candidates:
        all_candidates.append({
            'type': 'shape',
            'center': candidate['center'],
            'score': candidate['area'] * candidate['aspect_ratio']
        })

    # Add template candidates
    for match in template_matches:
        all_candidates.append({
            'type': 'template',
            'center': match['center'],
            'score': match['confidence'] * 100
        })

    # Add pixel candidates
    for candidate in pixel_candidates:
        all_candidates.append({
            'type': 'pixel',
            'center': candidate['center'],
            'score': candidate['white_ratio'] * 50
        })

    if all_candidates:
        best_candidate = max(all_candidates, key=lambda x: x['score'])
        print(f"\\nRECOMMENDED LIGHTNING POSITION:")
        print(f"Type: {best_candidate['type']}")
        print(f"Center: {best_candidate['center']}")
        print(f"Score: {best_candidate['score']:.2f}")

        return best_candidate['center']
    else:
        print("\\nNo lightning icon candidates found in the expected region!")
        return None

if __name__ == "__main__":
    result = locate_real_lightning_icon()