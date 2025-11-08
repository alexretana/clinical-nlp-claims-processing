## MedCodEX - Medical Coding with Explanations Dataset

This repo contains the dataset used in the paper: MedCodERR: A Generative AI Assistant for Medical Coding

There are 5 files:
1. text.csv: Comma separated file containing the document IDs and corresponding medical record text used as a test set.
2. text_holdout.csv: Comma separated file containing the document IDs and corresponding medical record text used as a holdout set for user experiments.
3. diagnosis.csv: Comma separated file containing the document IDs, corresponding diagnosed diseases, their start and end character positions in the medical record text, and mappings to the corresponding ICD code, used as a test set.
4. diagnosis_holdout.csv: Comma separated file containing the document IDs, corresponding diagnosed diseases, their start and end character positions in the medical record text, and mappings to the corresponding ICD code, used as a holdout set for user experiments.
5. suporting_evidence.csv: Comma separated file containing the document IDs,corresponding supporting evidence texts, their start and end character positions in the medical record text, and  mappings to the corresponding ICD code, used as a test set.