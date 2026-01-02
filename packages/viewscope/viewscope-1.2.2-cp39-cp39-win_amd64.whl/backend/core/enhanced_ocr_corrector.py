#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced OCR Corrector - Fixes specific recognition errors
Including the "一.KWh/loOkm" -> "--.-kWh/100km" issue
"""

import cv2
import numpy as np
import re
from typing import List, Dict

class EnhancedOCRCorrector:
    """Enhanced OCR corrector for automotive dashboard text"""

    def __init__(self):
        self.correction_rules = self._build_comprehensive_correction_rules()

    def _build_comprehensive_correction_rules(self) -> List[Dict]:
        """Build comprehensive correction rules for automotive dashboard OCR"""
        return [
            # Energy consumption unit corrections
            {
                'pattern': r'一\.KWh',
                'replacement': '--.-kWh',
                'description': 'Energy dash recognition error'
            },
            {
                'pattern': r'一\.kWh',
                'replacement': '--.-kWh',
                'description': 'Energy dash lowercase error'
            },
            {
                'pattern': r'一\.KWH',
                'replacement': '--.-kWh',
                'description': 'Energy dash uppercase error'
            },
            # Distance unit corrections - key fix for loO -> 100
            {
                'pattern': r'loO',
                'replacement': '100',
                'description': 'OCR l/1, o/0, O/0 confusion'
            },
            {
                'pattern': r'l0O',
                'replacement': '100',
                'description': 'OCR l/1, 0/O confusion variant'
            },
            {
                'pattern': r'1oO',
                'replacement': '100',
                'description': 'OCR o/0, O/0 confusion'
            },
            {
                'pattern': r'lOO',
                'replacement': '100',
                'description': 'OCR l/1, O/0 confusion'
            },
            # Complete energy unit pattern
            {
                'pattern': r'--\.-kWh/loO',
                'replacement': '--.-kWh/100',
                'description': 'Complete energy unit with distance error'
            },
            {
                'pattern': r'--\.-kWh/l0O',
                'replacement': '--.-kWh/100',
                'description': 'Complete energy unit variant'
            },
            # Ensure complete km unit
            {
                'pattern': r'--\.-kWh/100(?!km)',
                'replacement': '--.-kWh/100km',
                'description': 'Add missing km suffix'
            },
            {
                'pattern': r'--\.-kWh/100k(?!m)',
                'replacement': '--.-kWh/100km',
                'description': 'Add missing m in km'
            },
            # Temperature corrections
            {
                'pattern': r'^C$',
                'replacement': '--°C',
                'description': 'Temperature symbol correction',
                'context_check': lambda bounds: bounds[2] - bounds[0] < 50 and bounds[0] > 1700
            },
            # Time format corrections
            {
                'pattern': r'(\d{2}):(\d{2})h',
                'replacement': r'\1:\2h',
                'description': 'Time format normalization'
            },
            # Error text corrections
            {
                'pattern': r'ERRORkm',
                'replacement': 'ERROR km',
                'description': 'Error text spacing'
            }
        ]

    def correct_ocr_text(self, text_regions: List[Dict]) -> List[Dict]:
        """Apply enhanced OCR corrections to text regions"""
        corrected_regions = []

        print("Applying enhanced OCR corrections...")

        for i, region in enumerate(text_regions):
            original_content = region['text']
            bounds = region['bounds']
            corrected_content = original_content
            corrections_applied = []

            # Apply each correction rule
            for rule in self.correction_rules:
                pattern = rule['pattern']
                replacement = rule['replacement']
                description = rule['description']

                # Check context if required
                if 'context_check' in rule:
                    if not rule['context_check'](bounds):
                        continue

                # Apply correction
                if re.search(pattern, corrected_content, re.IGNORECASE):
                    new_content = re.sub(pattern, replacement, corrected_content, flags=re.IGNORECASE)
                    if new_content != corrected_content:
                        corrections_applied.append({
                            'rule': description,
                            'before': corrected_content,
                            'after': new_content
                        })
                        corrected_content = new_content
                        print(f"  Applied correction to region {i}: '{original_content}' -> '{corrected_content}' ({description})")

            # Additional smart corrections based on pattern analysis
            smart_corrections = self._apply_smart_corrections(corrected_content, bounds)
            if smart_corrections:
                for correction in smart_corrections:
                    corrections_applied.append(correction)
                    corrected_content = correction['after']

            # Create corrected region
            corrected_region = region.copy()
            corrected_region['text'] = corrected_content
            corrected_region['original_text'] = original_content
            corrected_region['corrections_applied'] = corrections_applied
            corrected_region['correction_count'] = len(corrections_applied)

            corrected_regions.append(corrected_region)

        print(f"OCR correction complete: processed {len(text_regions)} regions")
        return corrected_regions

    def _apply_smart_corrections(self, content: str, bounds: tuple) -> List[Dict]:
        """Apply smart context-aware corrections"""
        corrections = []

        # Smart energy unit reconstruction
        if any(char in content.lower() for char in ['kwh', 'wh', '一', '--']):
            if 'km' in content.lower() or 'loO' in content or 'l0O' in content:
                # This looks like an energy consumption unit
                smart_content = self._reconstruct_energy_unit(content)
                if smart_content != content:
                    corrections.append({
                        'rule': 'Smart energy unit reconstruction',
                        'before': content,
                        'after': smart_content
                    })

        return corrections

    def _reconstruct_energy_unit(self, content: str) -> str:
        """Intelligently reconstruct energy consumption unit"""
        # Pattern: should be "--.-kWh/100km"

        # Step 1: Fix the dash part
        if '一' in content:
            content = content.replace('一', '--')

        # Step 2: Fix the decimal point and unit
        if 'KWh' in content:
            content = content.replace('KWh', 'kWh')
        if 'KWH' in content:
            content = content.replace('KWH', 'kWh')

        # Step 3: Fix the distance part - key correction
        if 'loO' in content:
            content = content.replace('loO', '100')
        elif 'l0O' in content:
            content = content.replace('l0O', '100')
        elif '1oO' in content:
            content = content.replace('1oO', '100')
        elif 'lOO' in content:
            content = content.replace('lOO', '100')

        # Step 4: Ensure complete format
        if '--' in content and 'kWh' in content and '100' in content:
            if not content.endswith('km'):
                if content.endswith('k'):
                    content += 'm'
                elif 'k' in content and not 'km' in content:
                    content = content.replace('k', 'km')
                else:
                    content += 'km'

            # Final format verification and correction
            if not re.match(r'--\.-kWh/100km', content):
                # Rebuild the entire string
                content = '--.-kWh/100km'

        return content

def test_enhanced_ocr_correction():
    """Test the enhanced OCR corrector with specific problem cases"""
    print("=" * 60)
    print("Enhanced OCR Corrector Test")
    print("=" * 60)

    corrector = EnhancedOCRCorrector()

    # Test cases including the reported issue
    test_regions = [
        {
            'text': '一.KWh/loOkm',
            'bounds': (229, 203, 491, 245),
            'language': 'mixed'
        },
        {
            'text': '一.kWh/l0Okm',
            'bounds': (229, 203, 491, 245),
            'language': 'mixed'
        },
        {
            'text': 'C',
            'bounds': (1746, 144, 1812, 176),
            'language': 'english'
        },
        {
            'text': 'loO',
            'bounds': (400, 300, 450, 320),
            'language': 'mixed'
        },
        {
            'text': '--.-KWH/l00km',
            'bounds': (229, 203, 491, 245),
            'language': 'mixed'
        }
    ]

    print("Testing correction rules...")
    corrected = corrector.correct_ocr_text(test_regions)

    print(f"\nResults:")
    for i, region in enumerate(corrected):
        original = region['original_text']
        corrected_text = region['text']
        corrections = region['corrections_applied']

        print(f"\nRegion {i+1}:")
        print(f"  Original: '{original}'")
        print(f"  Corrected: '{corrected_text}'")
        print(f"  Corrections: {len(corrections)}")

        for correction in corrections:
            print(f"    - {correction['rule']}: '{correction['before']}' -> '{correction['after']}'")

    return corrected

if __name__ == "__main__":
    test_enhanced_ocr_correction()