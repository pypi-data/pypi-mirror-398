#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightning Location Finder - Interactive tool to locate the exact lightning icon
"""

import cv2
import numpy as np
import os

def find_lightning_icon_location():
    """Interactive tool to help locate the lightning icon"""

    print("=" * 60)
    print("LIGHTNING ICON LOCATION FINDER")
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

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create a detailed analysis of the left side where lightning icon should be
    left_width = 200  # Left 200 pixels
    roi = image[0:image.shape[0], 0:left_width]
    roi_gray = gray[0:gray.shape[0], 0:left_width]

    print(f"Analyzing left region: {left_width}x{image.shape[0]} pixels")

    # Method 1: Look for very small lightning-like shapes
    edges = cv2.Canny(roi_gray, 30, 100)

    # Find all contours in the left area
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"Found {len(contours)} contours in left area")

    # Analyze each small contour that could be a lightning icon
    potential_lightning = []

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)

        # Look for very small shapes that could be lightning icons
        if 5 <= area <= 100 and 4 <= w <= 20 and 8 <= h <= 30:
            aspect_ratio = h / w if w > 0 else 0

            # Lightning should be taller than wide
            if aspect_ratio >= 1.2:
                potential_lightning.append({
                    'contour': contour,
                    'bounds': (x, y, w, h),
                    'area': area,
                    'aspect_ratio': aspect_ratio,
                    'center': (x + w//2, y + h//2)
                })

    print(f"Found {len(potential_lightning)} potential lightning candidates")

    # Create visualization of all candidates
    result_image = roi.copy()

    for i, candidate in enumerate(potential_lightning):
        x, y, w, h = candidate['bounds']
        area = candidate['area']
        aspect_ratio = candidate['aspect_ratio']

        # Draw bounding box
        color = (0, 255, 255)  # Yellow for candidates
        cv2.rectangle(result_image, (x, y), (x + w, y + h), color, 1)

        # Add label
        label = f"{i+1}"
        cv2.putText(result_image, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

        print(f"Candidate {i+1}: pos({x},{y}) size({w}x{h}) area={area} ratio={aspect_ratio:.1f}")

    # Method 2: Template matching with very small templates
    print(f"\nTesting template matching with small templates...")

    # Create very small lightning templates
    small_templates = []

    # Template 1: Minimal lightning (6x12)
    template1 = np.zeros((12, 6), dtype=np.uint8)
    cv2.line(template1, (1, 1), (4, 5), 255, 1)  # Top diagonal
    cv2.line(template1, (2, 6), (5, 10), 255, 1) # Bottom diagonal
    cv2.line(template1, (1, 5), (3, 5), 255, 1)  # Middle horizontal
    small_templates.append(("6x12", template1))

    # Template 2: Slightly larger (8x16)
    template2 = np.zeros((16, 8), dtype=np.uint8)
    cv2.line(template2, (1, 1), (6, 7), 255, 1)   # Top diagonal
    cv2.line(template2, (2, 8), (7, 14), 255, 1)  # Bottom diagonal
    cv2.line(template2, (1, 7), (4, 7), 255, 1)   # Middle horizontal
    small_templates.append(("8x16", template2))

    # Template 3: Unicode-like lightning (10x14)
    template3 = np.zeros((14, 10), dtype=np.uint8)
    cv2.line(template3, (2, 1), (7, 6), 255, 1)   # Top diagonal
    cv2.line(template3, (3, 7), (8, 12), 255, 1)  # Bottom diagonal
    cv2.line(template3, (2, 6), (5, 6), 255, 1)   # Middle horizontal
    small_templates.append(("10x14", template3))

    template_matches = []

    for name, template in small_templates:
        result = cv2.matchTemplate(roi_gray, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.4)  # Lower threshold for small icons

        for pt in zip(*locations[::-1]):
            x, y = pt
            confidence = float(result[y, x])

            template_matches.append({
                'name': name,
                'position': (x, y),
                'confidence': confidence,
                'size': template.shape
            })

            print(f"Template {name} match at ({x},{y}) confidence={confidence:.3f}")

            # Draw on result image
            h, w = template.shape
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 1)  # Blue for template matches
            cv2.putText(result_image, f"T{confidence:.2f}", (x, y-2), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)

    print(f"Found {len(template_matches)} template matches")

    # Method 3: Look for the actual lightning symbol character
    print(f"\nSearching for lightning symbol patterns...")

    # Use different morphological operations to find small symbols
    kernel_cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    # Try different thresholds to find small bright symbols
    for thresh in [200, 220, 240]:
        _, binary = cv2.threshold(roi_gray, thresh, 255, cv2.THRESH_BINARY)

        # Find bright small objects
        contours_bright, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours_bright:
            area = cv2.contourArea(contour)
            if 8 <= area <= 50:  # Very small bright objects
                x, y, w, h = cv2.boundingRect(contour)
                if 3 <= w <= 12 and 6 <= h <= 20:
                    print(f"Bright symbol at ({x},{y}) size({w}x{h}) area={area} thresh={thresh}")
                    cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 1)  # Green for bright symbols

    # Save the analysis result
    output_path = "../../lightning_location_analysis.png"
    cv2.imwrite(output_path, result_image)

    print(f"\nLocation analysis saved: {output_path}")
    print(f"Found {len(potential_lightning)} shape candidates")
    print(f"Found {len(template_matches)} template matches")

    # Give specific recommendations
    print(f"\nRECOMMENDATIONS:")
    if potential_lightning:
        best_candidate = max(potential_lightning, key=lambda x: x['aspect_ratio'])
        x, y, w, h = best_candidate['bounds']
        print(f"Best shape candidate: position({x},{y}) size({w}x{h})")

    if template_matches:
        best_template = max(template_matches, key=lambda x: x['confidence'])
        x, y = best_template['position']
        print(f"Best template match: {best_template['name']} at ({x},{y}) conf={best_template['confidence']:.3f}")

    if not potential_lightning and not template_matches:
        print("No lightning icon detected. Possible reasons:")
        print("1. Lightning icon might be part of a larger UI element")
        print("2. Lightning icon might be very small or stylized")
        print("3. Lightning icon might not be present in this image")
        print("4. Need to adjust detection parameters")

    return {
        'shape_candidates': potential_lightning,
        'template_matches': template_matches,
        'analysis_image': output_path
    }

if __name__ == "__main__":
    result = find_lightning_icon_location()