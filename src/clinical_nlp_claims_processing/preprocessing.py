"""
Text preprocessing utilities for clinical notes.

Functions for cleaning and structuring medical text from various sources.
"""

import re
from typing import Dict


def clean_clinical_text(text: str) -> str:
    """Clean MIMIC clinical notes for NLP processing."""
    # Remove de-identification markers [**...**]
    text = re.sub(r'\[\*\*.*?\*\*\]', '[REDACTED]', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep medical notation
    text = re.sub(r'[^a-zA-Z0-9\s\.\-\/\,]', '', text)

    return text.strip()


def extract_note_sections(text: str) -> Dict[str, str]:
    """Extract structured sections from clinical notes."""
    sections = {}

    section_patterns = {
        'chief_complaint': r'Chief Complaint:(.+?)(?=\n[A-Z][a-z]+:|\n\n|$)',
        'history': r'History of Present Illness:(.+?)(?=\n[A-Z][a-z]+:|\n\n|$)',
        'past_medical': r'Past Medical History:(.+?)(?=\n[A-Z][a-z]+:|\n\n|$)',
        'medications': r'(?:Medications|Discharge Medications):(.+?)(?=\n[A-Z][a-z]+:|\n\n|$)',
        'assessment': r'Assessment and Plan:(.+?)(?=\n[A-Z][a-z]+:|\n\n|$)',
    }

    for section_name, pattern in section_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[section_name] = match.group(1).strip()

    return sections
