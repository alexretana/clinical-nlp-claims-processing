# BioBERT NLP Demonstration Plan
## Medical Coding with MedCodER Dataset

---

## 1. Project Overview

### Goals
- Demonstrate BioBERT's effectiveness on medical NLP tasks using the MedCodER dataset
- Compare performance between base BERT and domain-specific BioBERT models
- Implement two core medical NLP tasks:
  1. **Named Entity Recognition (NER)**: Extract diagnosis mentions from clinical text
  2. **Multi-label Classification**: Predict ICD-10 codes from medical narratives
- Create a reusable pipeline applicable to VA disability claims processing

### Dataset: MedCodER (Medical Coding with Explanations)
- **Training Set**: 184 clinical documents with SOAP notes
- **Holdout Set**: 20 documents for final evaluation
- **Annotations**:
  - 360 diagnosis annotations with character-level spans
  - 158 unique ICD-10 codes
  - 883 supporting evidence snippets
- **Format**: CSV files (text.csv, diagnosis.csv, supporting_evidence.csv)

### Expected Outcomes
- BioBERT should outperform base BERT by 5-15% on medical domain tasks
- F1 scores for NER: 75-85% (BioBERT) vs 65-75% (base BERT)
- Multi-label classification F1: 70-80% (BioBERT) vs 60-70% (base BERT)
- Insights into medical concept extraction and coding automation

---

## 2. Data Understanding

### Dataset Structure

#### text.csv (184 documents)
```
Document ID | medical_record_text | aci_doc_id
```
- Clinical narratives in SOAP format
- Typical sections: Chief Complaint, HPI, ROS, Physical Exam, Assessment & Plan
- Text length: 1000-4000 characters per document

#### diagnosis.csv (360 entries)
```
Document ID | ICD10 | Diagnosis | Start | End
```
- Character-level span annotations
- 1-4 diagnoses per document (average ~2)
- 158 unique ICD-10 codes
- Diagnosis text extracted from source document

#### supporting_evidence.csv (883 entries)
```
Document ID | ICD-10-CM code | Coordinate | Supporting Evidence Text | Start | End
```
- Multiple evidence snippets per diagnosis (average 2-3)
- Character-level spans of supporting text
- Enables explainability analysis

### Key Insights
- **Multi-label problem**: Documents have multiple ICD-10 codes
- **Span detection**: Character offsets enable precise entity boundary detection
- **Long context**: Clinical notes require handling 512+ token sequences
- **Imbalanced classes**: Some ICD codes are rare (1-2 instances)
- **Evidence data**: Allows attention mechanism validation

---

## 3. Technical Approach

### Task 1: Named Entity Recognition (NER)

**Objective**: Identify and extract diagnosis mentions from clinical text

**Approach**:
- Token classification task using character span annotations
- Convert character offsets to token-level BIO/IOB2 labels
- Labels: `B-DIAGNOSIS`, `I-DIAGNOSIS`, `O` (Outside)
- Handle tokenization alignment (WordPiece/BPE tokens)

**Evaluation Metrics**:
- Token-level: Precision, Recall, F1 (per-token accuracy)
- Span-level: Exact match F1 using `seqeval`
- Entity-level: Strict and relaxed boundary matching

### Task 2: Multi-label Classification

**Objective**: Predict ICD-10 codes from clinical narratives

**Approach**:
- Sequence classification with sigmoid output layer
- Binary classification for each of 158 ICD-10 codes
- Use `[CLS]` token representation for document encoding
- Handle class imbalance with weighted loss or focal loss

**Evaluation Metrics**:
- Micro F1, Macro F1 (account for class imbalance)
- Precision@K, Recall@K (top-K predictions)
- Hamming Loss (multi-label specific)
- Per-class metrics for common vs rare codes

### Model Comparison Strategy

**Baseline Model**:
- `bert-base-uncased` (110M parameters)
- General domain pre-training (Wikipedia + BookCorpus)

**Domain-Specific Model**:
- `dmis-lab/biobert-v1.1` OR `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract`
- Pre-trained on PubMed abstracts and PMC full-text articles
- Medical vocabulary and concepts

**Fair Comparison**:
- Identical hyperparameters (learning rate, batch size, epochs)
- Same data splits and preprocessing
- Same evaluation protocol
- Compare training efficiency (convergence speed, stability)

---

## 4. Implementation Steps

### Notebook Structure

#### Section 1: Setup and Data Loading (15-20 min)

**1.1 Environment Setup**
```python
# Import libraries
import pandas as pd
import numpy as np
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import Dataset, DatasetDict
import evaluate
from seqeval.metrics import classification_report, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
```

**1.2 Load MedCodER Data**
```python
# Load CSVs
text_df = pd.read_csv('data/raw/MedCodER/text.csv')
diagnosis_df = pd.read_csv('data/raw/MedCodER/diagnosis.csv')
evidence_df = pd.read_csv('data/raw/MedCodER/supporting_evidence.csv')

# Holdout set
text_holdout = pd.read_csv('data/raw/MedCodER/text_holdout.csv')
diagnosis_holdout = pd.read_csv('data/raw/MedCodER/diagnosis_holdout.csv')
```

**1.3 Exploratory Data Analysis**
- Document length distribution
- ICD-10 code frequency analysis
- Diagnoses per document histogram
- Sample clinical note visualization
- Word clouds for common medical terms

#### Section 2: Data Preprocessing (20-30 min)

**2.1 Merge DataFrames**
```python
# Create document-level dataset with all diagnoses and evidence
merged_df = text_df.merge(
    diagnosis_df.groupby('Document ID').agg({
        'ICD10': list,
        'Diagnosis': list,
        'Start': list,
        'End': list
    }).reset_index(),
    on='Document ID',
    how='left'
)
```

**2.2 Train/Validation Split**
```python
from sklearn.model_selection import train_test_split

# Stratified split by number of diagnoses
train_df, val_df = train_test_split(
    merged_df,
    test_size=0.2,
    random_state=42,
    stratify=merged_df['ICD10'].apply(len)
)
```

**2.3 Create Multi-label Encoding**
```python
from sklearn.preprocessing import MultiLabelBinarizer

mlb = MultiLabelBinarizer()
mlb.fit(merged_df['ICD10'])

# Create binary label matrix (n_samples x n_classes)
y_train = mlb.transform(train_df['ICD10'])
y_val = mlb.transform(val_df['ICD10'])
```

**2.4 Tokenization for NER**
```python
def align_labels_with_tokens(labels, word_ids):
    """Convert character-span labels to token-level BIO tags"""
    new_labels = []
    current_word = None

    for word_id in word_ids:
        if word_id is None:
            new_labels.append(-100)  # Special tokens
        elif word_id != current_word:
            new_labels.append(labels[word_id])
            current_word = word_id
        else:
            # Sub-word token: use I- tag or -100
            label = labels[word_id]
            new_labels.append(label if label in [1, 2] else -100)

    return new_labels

def create_ner_labels(text, spans, tokenizer):
    """Create BIO labels from character spans"""
    # Implementation details...
    pass
```

#### Section 3: Model Setup - Base BERT (20-30 min)

**3.1 Initialize BERT Models**
```python
# For NER
bert_ner_model = AutoModelForTokenClassification.from_pretrained(
    'bert-base-uncased',
    num_labels=3,  # O, B-DIAGNOSIS, I-DIAGNOSIS
    id2label={0: 'O', 1: 'B-DIAGNOSIS', 2: 'I-DIAGNOSIS'},
    label2id={'O': 0, 'B-DIAGNOSIS': 1, 'I-DIAGNOSIS': 2}
)

# For Classification
bert_clf_model = AutoModelForSequenceClassification.from_pretrained(
    'bert-base-uncased',
    num_labels=len(mlb.classes_),
    problem_type='multi_label_classification'
)
```

**3.2 Training Configuration**
```python
training_args = TrainingArguments(
    output_dir='./models/bert-base-ner',
    evaluation_strategy='epoch',
    save_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model='f1',
    logging_steps=50,
    fp16=True,  # Mixed precision training
)
```

**3.3 Train Base BERT**
```python
# NER Trainer
trainer_ner_bert = Trainer(
    model=bert_ner_model,
    args=training_args,
    train_dataset=train_dataset_ner,
    eval_dataset=val_dataset_ner,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics_ner,
)

# Train
trainer_ner_bert.train()

# Classification Trainer
trainer_clf_bert = Trainer(
    model=bert_clf_model,
    args=training_args,
    train_dataset=train_dataset_clf,
    eval_dataset=val_dataset_clf,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics_clf,
)

trainer_clf_bert.train()
```

#### Section 4: Model Setup - BioBERT (20-30 min)

**4.1 Initialize BioBERT Models**
```python
# Option 1: dmis-lab/biobert-v1.1
biobert_ner_model = AutoModelForTokenClassification.from_pretrained(
    'dmis-lab/biobert-v1.1',
    num_labels=3,
    id2label={0: 'O', 1: 'B-DIAGNOSIS', 2: 'I-DIAGNOSIS'},
    label2id={'O': 0, 'B-DIAGNOSIS': 1, 'I-DIAGNOSIS': 2}
)

# Option 2: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract (alternative)
# biobert_ner_model = AutoModelForTokenClassification.from_pretrained(
#     'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract',
#     ...
# )

biobert_clf_model = AutoModelForSequenceClassification.from_pretrained(
    'dmis-lab/biobert-v1.1',
    num_labels=len(mlb.classes_),
    problem_type='multi_label_classification'
)
```

**4.2 Train BioBERT** (same structure as base BERT)

#### Section 5: Evaluation and Comparison (30-40 min)

**5.1 NER Evaluation Metrics**
```python
def compute_metrics_ner(eval_pred):
    """Compute seqeval metrics for NER"""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (-100)
    true_labels = [[label_list[l] for l in label if l != -100]
                   for label in labels]
    true_predictions = [[label_list[p] for (p, l) in zip(prediction, label) if l != -100]
                       for prediction, label in zip(predictions, labels)]

    # Seqeval metrics
    results = evaluate.load("seqeval").compute(
        predictions=true_predictions,
        references=true_labels
    )

    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }
```

**5.2 Classification Evaluation Metrics**
```python
def compute_metrics_clf(eval_pred):
    """Compute multi-label classification metrics"""
    predictions, labels = eval_pred
    predictions = (predictions > 0.5).astype(int)

    from sklearn.metrics import f1_score, precision_score, recall_score, hamming_loss

    return {
        'micro_f1': f1_score(labels, predictions, average='micro'),
        'macro_f1': f1_score(labels, predictions, average='macro'),
        'precision_micro': precision_score(labels, predictions, average='micro'),
        'recall_micro': recall_score(labels, predictions, average='micro'),
        'hamming_loss': hamming_loss(labels, predictions),
    }
```

**5.3 Holdout Set Evaluation**
```python
# Evaluate both models on holdout set
bert_ner_results = trainer_ner_bert.predict(holdout_dataset_ner)
biobert_ner_results = trainer_ner_biobert.predict(holdout_dataset_ner)

bert_clf_results = trainer_clf_bert.predict(holdout_dataset_clf)
biobert_clf_results = trainer_clf_biobert.predict(holdout_dataset_clf)
```

**5.4 Comparison Visualizations**
```python
# Training curves comparison
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# NER F1 curves
axes[0, 0].plot(bert_ner_history['f1'], label='BERT')
axes[0, 0].plot(biobert_ner_history['f1'], label='BioBERT')
axes[0, 0].set_title('NER F1 Score Over Training')
axes[0, 0].legend()

# Classification F1 curves
axes[0, 1].plot(bert_clf_history['micro_f1'], label='BERT')
axes[0, 1].plot(biobert_clf_history['micro_f1'], label='BioBERT')
axes[0, 1].set_title('Classification Micro F1 Over Training')
axes[0, 1].legend()

# Final metrics comparison (bar chart)
models = ['BERT', 'BioBERT']
ner_f1 = [bert_ner_final_f1, biobert_ner_final_f1]
clf_f1 = [bert_clf_final_f1, biobert_clf_final_f1]

x = np.arange(len(models))
width = 0.35

axes[1, 0].bar(x - width/2, ner_f1, width, label='NER F1')
axes[1, 0].bar(x + width/2, clf_f1, width, label='Classification F1')
axes[1, 0].set_ylabel('F1 Score')
axes[1, 0].set_title('Final Model Comparison')
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels(models)
axes[1, 0].legend()

# Confusion matrix for top-10 ICD codes
# axes[1, 1] - heatmap

plt.tight_layout()
plt.show()
```

#### Section 6: Error Analysis and Insights (20-30 min)

**6.1 Analyze Misclassifications**
```python
# Find examples where BioBERT succeeded but BERT failed
bert_predictions = (bert_clf_results.predictions > 0.5).astype(int)
biobert_predictions = (biobert_clf_results.predictions > 0.5).astype(int)
true_labels = bert_clf_results.label_ids

biobert_correct = (biobert_predictions == true_labels)
bert_correct = (bert_predictions == true_labels)

# Examples where BioBERT is better
biobert_wins = biobert_correct & ~bert_correct
```

**6.2 Attention Visualization**
```python
# Extract attention weights for sample documents
# Compare with supporting evidence annotations
# Visualize which tokens receive highest attention
```

**6.3 Per-Class Performance**
```python
# Classification report for individual ICD codes
from sklearn.metrics import classification_report

print("BioBERT Classification Report:")
print(classification_report(
    true_labels,
    biobert_predictions,
    target_names=mlb.classes_
))
```

#### Section 7: Results Summary (10-15 min)

**7.1 Create Results Table**
```python
results_df = pd.DataFrame({
    'Model': ['BERT', 'BioBERT', 'Improvement'],
    'NER F1': [bert_ner_f1, biobert_ner_f1, f'{(biobert_ner_f1/bert_ner_f1 - 1)*100:.1f}%'],
    'NER Precision': [bert_ner_prec, biobert_ner_prec, f'{(biobert_ner_prec/bert_ner_prec - 1)*100:.1f}%'],
    'NER Recall': [bert_ner_rec, biobert_ner_rec, f'{(biobert_ner_rec/bert_ner_rec - 1)*100:.1f}%'],
    'Clf Micro F1': [bert_clf_micro, biobert_clf_micro, f'{(biobert_clf_micro/bert_clf_micro - 1)*100:.1f}%'],
    'Clf Macro F1': [bert_clf_macro, biobert_clf_macro, f'{(biobert_clf_macro/bert_clf_macro - 1)*100:.1f}%'],
})

display(results_df)
```

**7.2 Key Findings**
- Quantify BioBERT's advantage on medical terminology
- Analyze training efficiency (epochs to convergence)
- Discuss failure cases and limitations
- Relate to VA disability claims use case

---

## 5. Leveraging Available Packages

### Core Deep Learning Stack
- **transformers**: `AutoModel`, `AutoTokenizer`, `Trainer` API for training pipeline
- **torch**: Model architecture, loss functions, optimization
- **datasets**: Efficient data loading and caching with `Dataset` class

### NLP & Evaluation
- **seqeval**: Specialized metrics for sequence labeling (NER)
- **evaluate**: Hugging Face metrics library for standardized evaluation
- **nltk**: Text preprocessing, tokenization statistics, stopwords
- **spacy**: Alternative NER baseline, dependency parsing for feature engineering

### Data Science
- **pandas**: DataFrame manipulation, merging text/diagnosis/evidence data
- **numpy**: Numerical operations, label encoding
- **scikit-learn**:
  - `MultiLabelBinarizer` for ICD-10 encoding
  - `train_test_split` for data splitting
  - Classification metrics (F1, precision, recall, hamming_loss)
  - Stratified sampling

### Visualization
- **matplotlib**: Training curves, loss plots, metric trends
- **seaborn**: Heatmaps (confusion matrix), distribution plots, style
- **wordcloud**: Medical term frequency visualization

### Utilities
- **accelerate**: Multi-GPU training, mixed precision (FP16)
- **jupyterlab**: Interactive notebook environment

---

## 6. Expected Results

### Hypotheses

**H1: BioBERT will outperform base BERT on both tasks**
- NER F1: +8-12% improvement (medical entity understanding)
- Classification F1: +5-10% improvement (ICD code prediction)

**H2: Improvement will be larger for rare ICD codes**
- BioBERT's medical vocabulary helps with uncommon diagnoses
- Base BERT may struggle with domain-specific terminology

**H3: BioBERT will converge faster**
- Requires fewer epochs to reach optimal performance
- Lower validation loss earlier in training

**H4: Attention weights will align with supporting evidence**
- BioBERT attention correlates better with human annotations
- Explainability advantage for clinical deployment

### Performance Targets (Holdout Set)

| Task | Metric | Base BERT | BioBERT | Target Improvement |
|------|--------|-----------|---------|-------------------|
| NER | F1 Score | 68-72% | 78-82% | +10-15% |
| NER | Precision | 70-75% | 80-85% | +10-12% |
| NER | Recall | 65-70% | 75-80% | +10-12% |
| Classification | Micro F1 | 62-68% | 72-78% | +10-15% |
| Classification | Macro F1 | 45-52% | 58-65% | +15-20% |
| Classification | Precision@3 | 70-75% | 80-85% | +10-12% |

### Qualitative Observations
- BioBERT should better handle medical abbreviations (e.g., "HTN", "DM", "CHF")
- Improved understanding of medical context (e.g., "acute" vs "chronic")
- Better disambiguation of polysemous terms in medical context

---

## 7. Future Extensions

### Short-term Enhancements
1. **Multi-task Learning**: Joint training for NER + Classification
2. **Ensemble Methods**: Combine BERT and BioBERT predictions
3. **Advanced Architectures**:
   - BioBERT-large for higher capacity
   - ClinicalBERT (MIMIC-III trained)
   - PubMedBERT (Microsoft's biomedical model)
4. **Class Imbalance**: Focal loss, oversampling, class weights
5. **Hyperparameter Tuning**: Learning rate schedules, batch sizes, dropout

### Medium-term Research
1. **Explainability**:
   - Integrated Gradients for attribution
   - Compare attention with supporting_evidence annotations
   - SHAP values for feature importance
2. **Few-shot Learning**: Adapt to rare ICD codes with limited examples
3. **Hierarchical Classification**: Leverage ICD-10 taxonomy structure
4. **Evidence-based Prediction**: Multi-instance learning with supporting snippets

### Long-term Applications
1. **VA Disability Claims**:
   - Transfer learning to DBQ (Disability Benefits Questionnaires)
   - Condition-specific classifiers (PTSD, TBI, MST, etc.)
   - Evidence extraction from C&P exams
2. **Real-time Coding Assistance**:
   - Deploy as coding suggestion system for medical coders
   - Active learning for continuous improvement
3. **Clinical Decision Support**:
   - Diagnosis recommendation from clinical notes
   - Differential diagnosis generation
4. **Audit and Compliance**:
   - Detect coding errors and inconsistencies
   - Ensure ICD-10 guidelines adherence

---

## 8. Timeline and Effort Estimates

| Section | Task | Estimated Time |
|---------|------|---------------|
| 1 | Setup and Data Loading | 15-20 min |
| 2 | Data Preprocessing | 20-30 min |
| 3 | Base BERT Training | 20-30 min (+ GPU time) |
| 4 | BioBERT Training | 20-30 min (+ GPU time) |
| 5 | Evaluation and Comparison | 30-40 min |
| 6 | Error Analysis | 20-30 min |
| 7 | Results Summary | 10-15 min |
| **Total** | **Notebook Development** | **2.5-3.5 hours** |
| | **Model Training Time** | **2-4 hours (GPU)** |

---

## 9. Technical Requirements

### Hardware
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3060+, V100, A100)
  - Training without GPU possible but slow (10-20x longer)
- **RAM**: 16GB+ system memory
- **Storage**: 5GB+ for models and data

### Software
- Python 3.10+
- CUDA 11.8+ (for GPU acceleration)
- All dependencies specified in `pyproject.toml`

### Environment Setup
```bash
# Already configured in project
uv sync
uv run jupyter lab
```

---

## 10. Success Criteria

### Technical Success
- [ ] Both BERT and BioBERT models successfully trained on MedCodER dataset
- [ ] NER task achieves >70% F1 score on holdout set
- [ ] Classification task achieves >65% Micro F1 on holdout set
- [ ] BioBERT demonstrates measurable improvement over base BERT
- [ ] Training process is reproducible with fixed random seeds

### Demonstration Quality
- [ ] Notebook runs end-to-end without errors
- [ ] Clear visualizations of model comparison
- [ ] Well-documented code with markdown explanations
- [ ] Insightful error analysis and findings
- [ ] Professional presentation suitable for portfolio

### Learning Objectives
- [ ] Understand BioBERT architecture and pre-training
- [ ] Master multi-label classification techniques
- [ ] Implement token-level sequence labeling (NER)
- [ ] Use Hugging Face ecosystem effectively
- [ ] Evaluate medical NLP models rigorously

---

## 11. References and Resources

### Models
- BioBERT: https://huggingface.co/dmis-lab/biobert-v1.1
- PubMedBERT: https://huggingface.co/microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract
- ClinicalBERT: https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT

### Papers
- BioBERT: Lee et al. (2020) "BioBERT: a pre-trained biomedical language representation model"
- PubMedBERT: Gu et al. (2021) "Domain-Specific Language Model Pretraining for Biomedical NLP"
- ICD Coding: Mullenbach et al. (2018) "Explainable Prediction of Medical Codes from Clinical Text"

### Documentation
- Transformers: https://huggingface.co/docs/transformers
- Seqeval: https://huggingface.co/spaces/evaluate-metric/seqeval
- PyTorch: https://pytorch.org/docs/stable/index.html

### Datasets
- MedCodER: https://github.com/uw-bionlp/MedCodER
- MIMIC-III: https://physionet.org/content/mimiciii/
- ICD-10 Codes: https://www.cms.gov/medicare/coding-billing/icd-10-codes

---

## Conclusion

This plan provides a comprehensive roadmap for demonstrating BioBERT's capabilities on medical NLP tasks using the MedCodER dataset. The notebook will showcase:

1. **Technical proficiency** in modern NLP techniques
2. **Domain expertise** in clinical text processing
3. **Rigorous evaluation** methodology
4. **Practical applicability** to VA disability claims

By comparing base BERT and BioBERT, we'll quantify the value of domain-specific pre-training for medical applications. The resulting pipeline will serve as a foundation for VA claims automation and clinical coding assistance.

**Next Steps**: Implement this plan in a Jupyter notebook (`notebooks/biobert_medcoder_demo.ipynb`) following the outlined structure.
