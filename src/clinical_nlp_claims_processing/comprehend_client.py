"""
AWS Comprehend Medical client wrapper.

Provides simplified interface for AWS Comprehend Medical services.
"""

import boto3
from typing import Dict, List


class ComprehendMedicalClient:
    """Wrapper for AWS Comprehend Medical API."""

    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize Comprehend Medical client."""
        self.client = boto3.client(
            service_name='comprehendmedical',
            region_name=region_name
        )

    def extract_entities(self, text: str) -> Dict:
        """Extract entities using AWS Comprehend Medical."""
        response = self.client.detect_entities_v2(Text=text)

        entities = {
            'conditions': [],
            'medications': [],
            'procedures': [],
            'tests': [],
            'anatomy': [],
            'time_expressions': []
        }

        for entity in response['Entities']:
            entity_info = {
                'text': entity['Text'],
                'type': entity['Type'],
                'category': entity['Category'],
                'score': entity['Score'],
                'traits': entity.get('Traits', []),
                'attributes': entity.get('Attributes', [])
            }

            if entity['Category'] == 'MEDICAL_CONDITION':
                entities['conditions'].append(entity_info)
            elif entity['Category'] == 'MEDICATION':
                entities['medications'].append(entity_info)
            elif entity['Category'] == 'TEST_TREATMENT_PROCEDURE':
                if entity['Type'] == 'PROCEDURE_NAME':
                    entities['procedures'].append(entity_info)
                else:
                    entities['tests'].append(entity_info)
            elif entity['Category'] == 'ANATOMY':
                entities['anatomy'].append(entity_info)
            elif entity['Category'] == 'TIME_EXPRESSION':
                entities['time_expressions'].append(entity_info)

        return entities

    def infer_icd10(self, text: str) -> List[Dict]:
        """Infer ICD-10 codes using Comprehend Medical."""
        response = self.client.infer_icd10_cm(Text=text)

        icd_codes = []
        for entity in response['Entities']:
            entity_text = entity['Text']

            for concept in entity.get('ICD10CMConcepts', []):
                icd_codes.append({
                    'entity_text': entity_text,
                    'icd10_code': concept['Code'],
                    'icd10_description': concept['Description'],
                    'score': concept['Score'],
                    'category': entity.get('Category', 'UNKNOWN')
                })

        icd_codes.sort(key=lambda x: x['score'], reverse=True)
        return icd_codes

    def detect_phi(self, text: str) -> Dict:
        """Detect Protected Health Information."""
        response = self.client.detect_phi(Text=text)

        phi_entities = {
            'names': [],
            'dates': [],
            'ids': [],
            'locations': [],
            'ages': [],
            'contacts': []
        }

        for entity in response['Entities']:
            phi_info = {
                'text': entity['Text'],
                'type': entity['Type'],
                'score': entity['Score'],
                'begin_offset': entity['BeginOffset'],
                'end_offset': entity['EndOffset']
            }

            if entity['Type'] == 'NAME':
                phi_entities['names'].append(phi_info)
            elif entity['Type'] == 'DATE':
                phi_entities['dates'].append(phi_info)
            elif entity['Type'] == 'ID':
                phi_entities['ids'].append(phi_info)
            elif entity['Type'] == 'ADDRESS':
                phi_entities['locations'].append(phi_info)
            elif entity['Type'] == 'AGE':
                phi_entities['ages'].append(phi_info)
            elif entity['Type'] in ['PHONE', 'EMAIL']:
                phi_entities['contacts'].append(phi_info)

        return phi_entities
