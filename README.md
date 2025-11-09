# Clinical NLP for Claims Processing

A demonstration project exploring automated ICD-10-CM code extraction from clinical text using BioBERT fine-tuning and AWS Comprehend Medical. This project focuses on evaluating NLP techniques applicable to disability claims processing (such as VA benefits adjudication).

## 📋 Table of Contents

- [Overview](#overview)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Notebooks](#notebooks)
  - [1. BioBERT Fine-Tuning](#1-biobert-fine-tuning)
  - [2. AWS Comprehend Medical](#2-aws-comprehend-medical)
- [Results](#results)
- [Environment Setup](#environment-setup)
- [Key Findings](#key-findings)
- [What to Try Next](#what-to-try-next)

## 🎯 Overview

This project demonstrates two approaches to automated medical coding from clinical text:

1. **BioBERT Fine-Tuning**: Fine-tuning a pre-trained BioBERT model on a small, imbalanced medical coding dataset using data augmentation and LoRA
2. **AWS Comprehend Medical**: Evaluating AWS's pre-trained medical NER service for ICD-10-CM code extraction

The goal is to compare custom fine-tuning approaches with commercial medical NLP services and identify the most effective strategy for automated claims processing.

## 📊 Dataset

### MedCodER Dataset

This project uses the **MedCodER** dataset, which contains:

- **Training**: 500+ clinical documents with ICD-10 diagnosis codes
- **Holdout**: 50+ additional test documents
- **Supporting Evidence**: Character-level spans highlighting diagnostic evidence
- **158 unique ICD-10-CM codes** representing various medical conditions

#### Key Dataset Characteristics:

- **Severe class imbalance**: Most codes have <10 examples
- **Multi-label**: Documents contain 1-10+ diagnosis codes
- **Clinical complexity**: Full medical records (~2000 characters average)
- **Real-world data**: Reflects actual medical documentation challenges

![ICD-10 Class Imbalance](https://github.com/alexretana/clinical-nlp-claims-processing/raw/main/outputs/icd10_class_imbalance.png)

*Figure 1: Distribution showing severe class imbalance in the MedCodER dataset*

## 📁 Project Structure

```
clinical-nlp-claims-processing/
├── notebooks/
│   ├── 01_BioBERT_Fine-Tuning_NLP.ipynb    # BioBERT fine-tuning with LoRA
│   └── 02_AWS_Comprehend_Medical.ipynb      # AWS Comprehend Medical evaluation
├── data/
│   ├── raw/MedCodER/                        # Original dataset files
│   └── processed/                            # Preprocessed data
├── outputs/                                  # Results, metrics, visualizations
├── models/                                   # Saved model checkpoints
└── pyproject.toml                           # Project dependencies
```

## 📓 Notebooks

### 1. BioBERT Fine-Tuning

**Notebook**: [`01_BioBERT_Fine-Tuning_NLP.ipynb`](notebooks/01_BioBERT_Fine-Tuning_NLP.ipynb)

#### Preprocessing & Data Decisions

**Challenge**: Training on full 2000+ character documents dilutes diagnostic signals and creates computational challenges.

**Solution**: Evidence-focused training pipeline
1. **Evidence Extraction**: Extract focused diagnostic spans (~150-200 chars) from `supporting_evidence.csv` with ±50 character context windows
2. **Label Filtering**: Reduce label space from 158 codes to 18 codes with ≥80 examples each
3. **Multi-label handling**: Convert multi-label problem to single-label by treating each document-code pair independently

![Filtered Code Distribution](https://github.com/alexretana/clinical-nlp-claims-processing/raw/main/outputs/filtered_code_distribution.png)

*Figure 2: Distribution of the 18 ICD-10 codes selected for training (≥80 examples each)*

#### Data Augmentation

**Challenge**: Only ~1200 evidence examples for 18 classes (still limited data).

**Solution**: Back-translation augmentation
- **Technique**: Translate English → German → English using MarianMT models
- **Result**: 1.2x data augmentation in demo (4x possible with DE/FR/ES)
- **Validation strategy**: 100% original data in validation set to prevent optimistic bias

#### Training Strategy

**Challenge**: Standard fine-tuning of 110M parameters leads to severe overfitting on small datasets.

**Solution**: Parameter-efficient fine-tuning with LoRA
- **Architecture**: BioBERT-v1.1 (domain-adapted BERT for biomedical text)
- **LoRA Configuration**: 
  - Rank (r): 8
  - Alpha: 16
  - Target modules: Query & Value attention layers
  - **Trainable parameters**: Only 0.1% of total parameters
- **Class Weighting**: Balanced loss function to handle remaining imbalance
- **Optimization**: 
  - Learning rate: 2e-4 (higher for LoRA)
  - Batch size: 16
  - Epochs: 15
  - FP16 training on CUDA

#### Results

| Metric | Score |
|--------|-------|
| **Accuracy** | 94.4% |
| **Macro F1** | 0.944 |
| **Weighted F1** | 0.945 |
| **Macro Precision** | 0.944 |
| **Macro Recall** | 0.950 |

**Key Achievement**: ~**400-700% improvement** over naive full fine-tuning approaches (Macro F1: 0.023 → 0.944)

**Limitations**:
- Only evaluated on 18 most frequent codes (not full 158 code set)
- Small validation set due to data constraints
- Evidence-focused approach may miss contextual information

### 2. AWS Comprehend Medical

**Notebook**: [`02_AWS_Comprehend_Medical.ipynb`](notebooks/02_AWS_Comprehend_Medical.ipynb)

#### Preprocessing & Configuration

**Approach**: Zero-shot inference using AWS's pre-trained `InferICD10CM` API with intelligent filtering.

**Key Preprocessing Decisions**:

1. **Entity Trait Filtering**:
   - ❌ Filter NEGATION (e.g., "no diabetes", "denies fever")
   - ❌ Filter HYPOTHETICAL (e.g., "if patient develops diabetes")
   - ❌ Filter PERTAINS_TO_FAMILY (e.g., "mother has diabetes")
   - ✅ Require DIAGNOSIS trait (not just symptoms/signs)

2. **Confidence Thresholding**: Test multiple thresholds (0.3, 0.5, 0.7)

3. **Multi-Label Evaluation**: Document-level evaluation comparing sets of predicted vs. true codes

![AWS Threshold Analysis](https://github.com/alexretana/clinical-nlp-claims-processing/raw/main/outputs/aws_threshold_analysis.png)

*Figure 3: Precision-recall tradeoff across different confidence thresholds*

#### Evaluation Strategy

**Challenge**: MedCodER is a multi-label problem (documents have multiple ICD-10 codes), requiring appropriate evaluation metrics.

**Solution**: Document-level multi-label evaluation
- **Metrics**:
  - Macro/Micro Precision, Recall, F1
  - Exact Match Accuracy (all codes correct)
  - Jaccard Similarity (set overlap)
  - Per-code recall analysis

#### Results (Best Threshold = 0.5)

| Metric | Score |
|--------|-------|
| **Documents Evaluated** | 184 |
| **Coverage** | 97.3% |
| **Macro F1** | 0.271 |
| **Micro F1** | 0.249 |
| **Macro Precision** | 0.206 |
| **Macro Recall** | 0.599 |
| **Exact Match Accuracy** | 1.1% |
| **Mean Jaccard Similarity** | 0.183 |

**Key Observations**:
- High recall (59.9%) but low precision (20.6%)
- AWS over-predicts codes (many false positives)
- Poor exact match due to multi-label complexity
- Only 1.1% of documents had all codes correctly predicted

**Per-Code Performance**:
- Some codes achieved >80% recall
- Many rare codes had 0% recall
- Performance correlates with code frequency

## 🏆 Results

### Model Comparison

| Model | Evaluation Set | Macro F1 | Precision | Recall | Notes |
|-------|---------------|----------|-----------|--------|-------|
| **BioBERT + LoRA** | 18 frequent codes | **0.944** | 0.944 | 0.950 | Evidence-focused, augmented data |
| **AWS Comprehend** | All 158 codes | **0.271** | 0.206 | 0.599 | Zero-shot, high recall/low precision |

**Important Note**: Direct comparison is challenging because:
- BioBERT was trained/evaluated only on 18 most frequent codes
- AWS Comprehend was evaluated on all 158 codes (including many rare codes)
- Different evaluation strategies (single-label vs. multi-label)

### Key Insights

1. **BioBERT Fine-Tuning**: Excellent performance on frequent codes with sufficient training data
   - Evidence extraction is crucial for small datasets
   - LoRA prevents overfitting effectively
   - Data augmentation provides meaningful improvements

2. **AWS Comprehend Medical**: Moderate performance on full code set without training
   - Zero-shot capability is valuable for rare codes
   - High recall makes it useful for screening
   - Filtering (negation, hypothetical) is essential
   - Low precision requires human review

3. **Class Imbalance**: The primary challenge for both approaches
   - Rare codes (<10 examples) are nearly impossible to learn
   - Commercial services also struggle with rare codes

## 🔧 Environment Setup

This project uses [`uv`](https://github.com/astral-sh/uv) for fast, reliable dependency management.

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/alexretana/clinical-nlp-claims-processing.git
cd clinical-nlp-claims-processing

# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
# On Unix/MacOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Launch Jupyter
jupyter lab
```

### AWS Setup (for AWS Comprehend Medical notebook)

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
```

**Required IAM Permissions**:
- `comprehendmedical:InferICD10CM`
- `comprehendmedical:DetectEntitiesV2`

### Dependencies

Key packages (see [`pyproject.toml`](pyproject.toml) for full list):
- `transformers[torch]>=4.35.0` - Hugging Face transformers
- `torch>=2.1.0` - PyTorch
- `peft>=0.17.1` - Parameter-efficient fine-tuning (LoRA)
- `boto3>=1.29.0` - AWS SDK
- `scikit-learn>=1.3.0` - Metrics and evaluation
- `pandas`, `numpy`, `matplotlib`, `seaborn` - Data processing and visualization

## 🔍 Key Findings

### What Worked Well

✅ **Evidence-focused training**: Extracting diagnostic spans significantly improved signal-to-noise ratio

✅ **LoRA fine-tuning**: Prevented overfitting while maintaining model expressiveness

✅ **Data augmentation**: Back-translation provided meaningful performance gains

✅ **Class filtering**: Focusing on codes with sufficient examples (≥80) ensured viable training

✅ **Entity filtering for AWS**: Removing negations and hypotheticals reduced false positives

### What Didn't Work

❌ **Full fine-tuning**: Led to severe overfitting on small datasets

❌ **Training on full documents**: Diluted diagnostic signals and increased computational cost

❌ **Including rare codes**: Codes with <10 examples couldn't be learned effectively

❌ **Unfiltered AWS predictions**: Generated many false positives without trait filtering

## 🚀 What to Try Next

### For BioBERT Approach

1. **Hierarchical Classification**: 
   - First predict ICD-10 chapter (e.g., "E00-E89: Endocrine diseases")
   - Then predict specific code within chapter
   - Could improve performance on rare codes

2. **Full Back-Translation Augmentation**: 
   - Implement FR and ES augmentation (currently only DE)
   - Target 4x data expansion

3. **Ensemble Methods**: 
   - Combine multiple augmented models
   - Use different random seeds for robustness

4. **Transfer Learning from Related Tasks**: 
   - Pre-train on medical entity recognition
   - Fine-tune on ICD-10 classification

5. **Expand to More Codes**: 
   - Lower threshold to ≥50 or ≥30 examples
   - Evaluate performance degradation

### For AWS Comprehend Medical

1. **Hybrid Thresholding**: 
   - Different confidence thresholds for different code frequencies
   - Higher threshold for common codes, lower for rare codes

2. **Post-Processing Rules**: 
   - Domain-specific filtering based on co-occurrence patterns
   - Temporal reasoning (onset, duration)

3. **Confidence Calibration**: 
   - Analyze score distributions by code
   - Develop code-specific thresholds

4. **Entity Linking**: 
   - Map AWS entities to UMLS concepts
   - Use semantic similarity for better matching

### Hybrid Approaches

1. **BioBERT for Frequent + AWS for Rare**: 
   - Use fine-tuned model for codes with training data
   - Fall back to AWS for zero-shot rare codes

2. **AWS as Feature Extractor**: 
   - Use AWS entities as additional features
   - Train lightweight classifier on top

3. **Active Learning Pipeline**: 
   - Use AWS for initial predictions
   - Human-in-the-loop for uncertain cases
   - Continuously retrain BioBERT

4. **Multi-Model Ensemble**: 
   - Combine predictions from BioBERT and AWS
   - Voting or stacking strategies

### Data & Evaluation

1. **Gather More Data**: 
   - Synthetic data generation using LLMs
   - Data augmentation beyond back-translation (e.g., paraphrasing)

2. **Better Evaluation Metrics**: 
   - Hierarchical F1 (credit partial matches in ICD-10 hierarchy)
   - Clinical relevance weighting (some errors worse than others)

3. **Multi-Label Evaluation for BioBERT**: 
   - Re-evaluate BioBERT with document-level multi-label metrics
   - Direct comparison with AWS on same test set

## 📚 References

- **MedCodER Dataset**: [Link to dataset](https://physionet.org/content/medcoder/1.0.0/)
- **BioBERT**: Lee et al., 2020. "BioBERT: a pre-trained biomedical language representation model"
- **LoRA**: Hu et al., 2021. "LoRA: Low-Rank Adaptation of Large Language Models"
- **AWS Comprehend Medical**: [AWS Documentation](https://docs.aws.amazon.com/comprehend-medical/)

## 📄 License

This project uses the MedCodER dataset which is licensed under CC-BY-NC-ND-4.0. See [`data/raw/MedCodER/LICENSE-CC-BY-NC-ND-4.0.pdf`](data/raw/MedCodER/LICENSE-CC-BY-NC-ND-4.0.pdf) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Project Status**: Demonstration/Research Project

This project demonstrates NLP techniques for medical coding and is intended for research and educational purposes. It is not intended for production use in clinical settings without proper validation and regulatory compliance.
