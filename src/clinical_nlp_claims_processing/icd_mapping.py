"""
ICD-10 code mapping utilities.

Tools for mapping extracted medical conditions to ICD-10 codes.
"""

from difflib import SequenceMatcher
from typing import Dict, List, Tuple
import pandas as pd


class ICD10Mapper:
    """Map extracted medical conditions to ICD-10 codes."""

    def __init__(self, icd10_df: pd.DataFrame):
        self.icd10_df = icd10_df
        self.description_index = self._build_index()

    def _build_index(self) -> Dict[str, str]:
        """Build fast lookup index."""
        index = {}
        for _, row in self.icd10_df.iterrows():
            normalized = row['description'].lower().strip()
            index[normalized] = row['code']
        return index

    def fuzzy_match(self, condition_text: str, threshold: float = 0.6) -> List[Tuple[str, str, float]]:
        """Find ICD-10 codes using fuzzy string matching."""
        condition_lower = condition_text.lower()
        matches = []

        for description, code in self.description_index.items():
            similarity = SequenceMatcher(None, condition_lower, description).ratio()

            if similarity >= threshold:
                matches.append((code, description, similarity))

        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[:5]

    def map_entity_to_icd10(self, entity: Dict) -> Dict:
        """Map extracted entity to ICD-10 code."""
        condition_text = entity['text']
        matches = self.fuzzy_match(condition_text)

        if matches:
            best_match = matches[0]
            return {
                'original_text': condition_text,
                'icd10_code': best_match[0],
                'icd10_description': best_match[1],
                'match_confidence': best_match[2],
                'alternative_codes': matches[1:3]
            }
        else:
            return {
                'original_text': condition_text,
                'icd10_code': None,
                'match_confidence': 0.0
            }
