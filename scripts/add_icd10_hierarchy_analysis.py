"""
Script to add ICD-10 hierarchy analysis cells to the BioBERT notebook.
This will enhance the data exploration section with hierarchical structure analysis.
"""

import json
import sys

def create_code_cell(code_lines):
    """Create a code cell with the given code lines."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": code_lines
    }

def create_markdown_cell(text):
    """Create a markdown cell with the given text."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [text] if isinstance(text, list) else [text]
    }

# Define the new cells to add
new_cells = [
    # Section header
    create_markdown_cell(["### 2.1 ICD-10 Hierarchical Structure Analysis\n"]),
    
    # ICD-10 parsing functions
    create_code_cell([
        "# ICD-10 Hierarchy Parsing Functions\n",
        "\n",
        "def parse_icd10_code(code):\n",
        "    \"\"\"\n",
        "    Parse ICD-10 code into hierarchical components.\n",
        "    Returns dict with chapter, category, subcategory levels, and extension.\n",
        "    \"\"\"\n",
        "    if pd.isna(code) or not code:\n",
        "        return {\n",
        "            'chapter_letter': None,\n",
        "            'category': None,\n",
        "            'subcategory_4': None,\n",
        "            'subcategory_5': None,\n",
        "            'subcategory_6': None,\n",
        "            'extension': None,\n",
        "            'has_extension': False,\n",
        "            'code_length': 0\n",
        "        }\n",
        "    \n",
        "    # Clean the code (remove dots, spaces, convert to uppercase)\n",
        "    clean_code = str(code).replace('.', '').replace(' ', '').upper()\n",
        "    \n",
        "    # Extract components\n",
        "    result = {\n",
        "        'chapter_letter': clean_code[0] if len(clean_code) >= 1 else None,\n",
        "        'category': clean_code[:3] if len(clean_code) >= 3 else clean_code,\n",
        "        'subcategory_4': clean_code[:4] if len(clean_code) >= 4 else None,\n",
        "        'subcategory_5': clean_code[:5] if len(clean_code) >= 5 else None,\n",
        "        'subcategory_6': clean_code[:6] if len(clean_code) >= 6 else None,\n",
        "        'extension': clean_code[6] if len(clean_code) == 7 else None,\n",
        "        'has_extension': len(clean_code) == 7,\n",
        "        'code_length': len(clean_code)\n",
        "    }\n",
        "    \n",
        "    return result\n",
        "\n",
        "# ICD-10 Chapter mapping (22 chapters)\n",
        "CHAPTER_MAP = {\n",
        "    'A': 'Ch01_Infectious_Parasitic',\n",
        "    'B': 'Ch01_Infectious_Parasitic',\n",
        "    'C': 'Ch02_Neoplasms',\n",
        "    'D': 'Ch02-03_Neoplasms_Blood',\n",
        "    'E': 'Ch04_Endocrine_Metabolic',\n",
        "    'F': 'Ch05_Mental_Behavioral',\n",
        "    'G': 'Ch06_Nervous_System',\n",
        "    'H': 'Ch07-08_Eye_Ear',\n",
        "    'I': 'Ch09_Circulatory',\n",
        "    'J': 'Ch10_Respiratory',\n",
        "    'K': 'Ch11_Digestive',\n",
        "    'L': 'Ch12_Skin',\n",
        "    'M': 'Ch13_Musculoskeletal',\n",
        "    'N': 'Ch14_Genitourinary',\n",
        "    'O': 'Ch15_Pregnancy',\n",
        "    'P': 'Ch16_Perinatal',\n",
        "    'Q': 'Ch17_Congenital',\n",
        "    'R': 'Ch18_Symptoms_Signs',\n",
        "    'S': 'Ch19_Injury_Poisoning',\n",
        "    'T': 'Ch19_Injury_Poisoning',\n",
        "    'V': 'Ch20_External_Causes',\n",
        "    'W': 'Ch20_External_Causes',\n",
        "    'X': 'Ch20_External_Causes',\n",
        "    'Y': 'Ch20_External_Causes',\n",
        "    'Z': 'Ch21_Health_Status',\n",
        "    'U': 'Ch22_Special_Purposes'\n",
        "}\n",
        "\n",
        "print(\"ICD-10 parsing functions defined\")\n"
    ]),
    
    # Apply hierarchy parsing
    create_code_cell([
        "# Parse ICD-10 codes and add hierarchy columns\n",
        "\n",
        "print(\"Parsing ICD-10 codes into hierarchical components...\")\n",
        "\n",
        "# Parse all diagnosis codes\n",
        "parsed_codes = diagnosis_df['ICD10'].apply(parse_icd10_code)\n",
        "hierarchy_df = pd.DataFrame(parsed_codes.tolist())\n",
        "\n",
        "# Add chapter name mapping\n",
        "hierarchy_df['chapter_name'] = hierarchy_df['chapter_letter'].map(CHAPTER_MAP)\n",
        "\n",
        "# Combine with original diagnosis dataframe\n",
        "diagnosis_enriched = pd.concat([diagnosis_df, hierarchy_df], axis=1)\n",
        "\n",
        "print(f\"\\nEnriched diagnosis dataframe shape: {diagnosis_enriched.shape}\")\n",
        "print(f\"\\nNew columns added: {hierarchy_df.columns.tolist()}\")\n",
        "print(f\"\\nSample enriched data:\")\n",
        "print(diagnosis_enriched[['ICD10', 'chapter_letter', 'chapter_name', 'category', 'code_length']].head(10))\n"
    ]),
    
    # Chapter distribution analysis
    create_code_cell([
        "# ICD-10 Chapter Distribution Analysis\n",
        "\n",
        "print(\"\\n\" + \"=\"*80)\n",
        "print(\"ICD-10 CHAPTER DISTRIBUTION\")\n",
        "print(\"=\"*80)\n",
        "\n",
        "# Count codes by chapter\n",
        "chapter_counts = diagnosis_enriched['chapter_name'].value_counts().sort_index()\n",
        "\n",
        "print(f\"\\nTotal unique chapters present: {diagnosis_enriched['chapter_name'].nunique()}\")\n",
        "print(f\"\\nCodes per chapter:\")\n",
        "for chapter, count in chapter_counts.items():\n",
        "    print(f\"  {chapter}: {count:,} codes\")\n",
        "\n",
        "# Document-level chapter analysis\n",
        "doc_chapter_df = diagnosis_enriched.groupby('Document ID')['chapter_name'].apply(list).reset_index()\n",
        "doc_chapter_df['num_chapters'] = doc_chapter_df['chapter_name'].apply(lambda x: len(set(x)))\n",
        "doc_chapter_df['unique_chapters'] = doc_chapter_df['chapter_name'].apply(lambda x: list(set(x)))\n",
        "\n",
        "print(f\"\\nChapters per document statistics:\")\n",
        "print(doc_chapter_df['num_chapters'].describe())\n",
        "\n",
        "# Most common chapter combinations\n",
        "chapter_combos = doc_chapter_df['unique_chapters'].apply(lambda x: tuple(sorted(x)))\n",
        "combo_counts = chapter_combos.value_counts().head(10)\n",
        "\n",
        "print(f\"\\nTop 10 chapter combinations:\")\n",
        "for combo, count in combo_counts.items():\n",
        "    chapter_str = \", \".join([c.split('_')[0] for c in combo])\n",
        "    print(f\"  {chapter_str}: {count} documents\")\n"
    ]),
    
    # Visualization: Chapter distribution
    create_code_cell([
        "# Visualize ICD-10 Chapter Distribution\n",
        "\n",
        "fig, axes = plt.subplots(2, 2, figsize=(16, 12))\n",
        "\n",
        "# 1. Chapter frequency bar chart\n",
        "chapter_counts_sorted = diagnosis_enriched['chapter_name'].value_counts()\n",
        "ax1 = axes[0, 0]\n",
        "chapter_counts_sorted.plot(kind='barh', ax=ax1, color='steelblue', edgecolor='black')\n",
        "ax1.set_xlabel('Number of Diagnosis Codes')\n",
        "ax1.set_ylabel('ICD-10 Chapter')\n",
        "ax1.set_title('Distribution of ICD-10 Codes Across Chapters', fontsize=12, fontweight='bold')\n",
        "ax1.invert_yaxis()\n",
        "\n",
        "# 2. Chapters per document histogram\n",
        "ax2 = axes[0, 1]\n",
        "ax2.hist(doc_chapter_df['num_chapters'], bins=range(1, doc_chapter_df['num_chapters'].max() + 2), \n",
        "         edgecolor='black', color='coral', align='left')\n",
        "ax2.set_xlabel('Number of Unique Chapters per Document')\n",
        "ax2.set_ylabel('Number of Documents')\n",
        "ax2.set_title('Documents by Chapter Diversity', fontsize=12, fontweight='bold')\n",
        "ax2.grid(axis='y', alpha=0.3)\n",
        "\n",
        "# 3. Code length distribution\n",
        "ax3 = axes[1, 0]\n",
        "code_length_counts = diagnosis_enriched['code_length'].value_counts().sort_index()\n",
        "ax3.bar(code_length_counts.index, code_length_counts.values, color='mediumseagreen', edgecolor='black')\n",
        "ax3.set_xlabel('ICD-10 Code Length (characters)')\n",
        "ax3.set_ylabel('Number of Codes')\n",
        "ax3.set_title('ICD-10 Hierarchical Depth Distribution', fontsize=12, fontweight='bold')\n",
        "ax3.set_xticks(range(3, 8))\n",
        "ax3.grid(axis='y', alpha=0.3)\n",
        "\n",
        "# Add text annotations\n",
        "for i, v in enumerate(code_length_counts.values):\n",
        "    ax3.text(code_length_counts.index[i], v + 50, str(v), ha='center', va='bottom')\n",
        "\n",
        "# 4. Top categories (3-char codes) frequency\n",
        "ax4 = axes[1, 1]\n",
        "top_categories = diagnosis_enriched['category'].value_counts().head(15)\n",
        "ax4.barh(range(len(top_categories)), top_categories.values, color='mediumpurple', edgecolor='black')\n",
        "ax4.set_yticks(range(len(top_categories)))\n",
        "ax4.set_yticklabels(top_categories.index)\n",
        "ax4.set_xlabel('Frequency')\n",
        "ax4.set_ylabel('ICD-10 Category (3-char)')\n",
        "ax4.set_title('Top 15 Most Common ICD-10 Categories', fontsize=12, fontweight='bold')\n",
        "ax4.invert_yaxis()\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.savefig('../outputs/icd10_hierarchy_analysis.png', dpi=300, bbox_inches='tight')\n",
        "plt.show()\n",
        "\n",
        "print(\"\\nVisualization saved to '../outputs/icd10_hierarchy_analysis.png'\")\n"
    ]),
    
    # Category-level analysis
    create_code_cell([
        "# ICD-10 Category (3-character) Analysis\n",
        "\n",
        "print(\"\\n\" + \"=\"*80)\n",
        "print(\"ICD-10 CATEGORY-LEVEL ANALYSIS\")\n",
        "print(\"=\"*80)\n",
        "\n",
        "# Unique categories overall\n",
        "total_categories = diagnosis_enriched['category'].nunique()\n",
        "print(f\"\\nTotal unique ICD-10 categories (3-char): {total_categories}\")\n",
        "\n",
        "# Categories per chapter\n",
        "categories_per_chapter = diagnosis_enriched.groupby('chapter_name')['category'].nunique().sort_values(ascending=False)\n",
        "\n",
        "print(f\"\\nCategories per chapter:\")\n",
        "for chapter, count in categories_per_chapter.items():\n",
        "    chapter_short = chapter.split('_')[0]\n",
        "    print(f\"  {chapter_short}: {count} unique categories\")\n",
        "\n",
        "# Category frequency distribution\n",
        "category_freq = diagnosis_enriched['category'].value_counts()\n",
        "print(f\"\\nCategory frequency statistics:\")\n",
        "print(f\"  Mean occurrences per category: {category_freq.mean():.1f}\")\n",
        "print(f\"  Median occurrences per category: {category_freq.median():.1f}\")\n",
        "print(f\"  Categories appearing only once: {(category_freq == 1).sum()}\")\n",
        "print(f\"  Categories appearing >10 times: {(category_freq > 10).sum()}\")\n",
        "print(f\"  Categories appearing >50 times: {(category_freq > 50).sum()}\")\n"
    ]),
    
    # Class imbalance analysis by hierarchy
    create_code_cell([
        "# Class Imbalance Analysis by Hierarchical Level\n",
        "\n",
        "print(\"\\n\" + \"=\"*80)\n",
        "print(\"CLASS IMBALANCE ANALYSIS BY HIERARCHY LEVEL\")\n",
        "print(\"=\"*80)\n",
        "\n",
        "# Calculate imbalance at different levels\n",
        "levels = {\n",
        "    'Chapter (1-char)': 'chapter_name',\n",
        "    'Category (3-char)': 'category',\n",
        "    'Subcategory-4': 'subcategory_4',\n",
        "    'Subcategory-5': 'subcategory_5',\n",
        "    'Full Code': 'ICD10'\n",
        "}\n",
        "\n",
        "imbalance_stats = []\n",
        "\n",
        "for level_name, column in levels.items():\n",
        "    if column in diagnosis_enriched.columns:\n",
        "        freq = diagnosis_enriched[column].value_counts()\n",
        "        \n",
        "        stats = {\n",
        "            'Level': level_name,\n",
        "            'Unique Codes': len(freq),\n",
        "            'Mean Frequency': freq.mean(),\n",
        "            'Median Frequency': freq.median(),\n",
        "            'Max Frequency': freq.max(),\n",
        "            'Min Frequency': freq.min(),\n",
        "            'Std Dev': freq.std(),\n",
        "            'Codes with <5 samples': (freq < 5).sum(),\n",
        "            'Codes with <10 samples': (freq < 10).sum(),\n",
        "            'Imbalance Ratio': freq.max() / freq.min() if freq.min() > 0 else np.inf\n",
        "        }\n",
        "        imbalance_stats.append(stats)\n",
        "\n",
        "imbalance_df = pd.DataFrame(imbalance_stats)\n",
        "\n",
        "print(\"\\nClass imbalance by hierarchical level:\")\n",
        "print(imbalance_df.to_string(index=False))\n",
        "\n",
        "# Visualize imbalance\n",
        "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
        "\n",
        "# Unique codes per level\n",
        "ax1 = axes[0]\n",
        "ax1.bar(range(len(imbalance_df)), imbalance_df['Unique Codes'], color='indianred', edgecolor='black')\n",
        "ax1.set_xticks(range(len(imbalance_df)))\n",
        "ax1.set_xticklabels(imbalance_df['Level'], rotation=45, ha='right')\n",
        "ax1.set_ylabel('Number of Unique Codes')\n",
        "ax1.set_title('Label Space Size by Hierarchy Level', fontweight='bold')\n",
        "ax1.set_yscale('log')\n",
        "ax1.grid(axis='y', alpha=0.3)\n",
        "\n",
        "# Add value labels\n",
        "for i, v in enumerate(imbalance_df['Unique Codes']):\n",
        "    ax1.text(i, v * 1.1, str(v), ha='center', va='bottom')\n",
        "\n",
        "# Codes with insufficient samples\n",
        "ax2 = axes[1]\n",
        "x = np.arange(len(imbalance_df))\n",
        "width = 0.35\n",
        "ax2.bar(x - width/2, imbalance_df['Codes with <5 samples'], width, label='<5 samples', \n",
        "        color='lightcoral', edgecolor='black')\n",
        "ax2.bar(x + width/2, imbalance_df['Codes with <10 samples'], width, label='<10 samples', \n",
        "        color='salmon', edgecolor='black')\n",
        "ax2.set_xticks(x)\n",
        "ax2.set_xticklabels(imbalance_df['Level'], rotation=45, ha='right')\n",
        "ax2.set_ylabel('Number of Codes')\n",
        "ax2.set_title('Rare Classes by Hierarchy Level', fontweight='bold')\n",
        "ax2.legend()\n",
        "ax2.grid(axis='y', alpha=0.3)\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.savefig('../outputs/icd10_class_imbalance.png', dpi=300, bbox_inches='tight')\n",
        "plt.show()\n",
        "\n",
        "print(\"\\nVisualization saved to '../outputs/icd10_class_imbalance.png'\")\n"
    ]),
    
    # Extension analysis
    create_code_cell([
        "# ICD-10 Extension (7th Character) Analysis\n",
        "\n",
        "print(\"\\n\" + \"=\"*80)\n",
        "print(\"ICD-10 EXTENSION (7TH CHARACTER) ANALYSIS\")\n",
        "print(\"=\"*80)\n",
        "\n",
        "# Count codes with extensions\n",
        "codes_with_extension = diagnosis_enriched['has_extension'].sum()\n",
        "total_codes = len(diagnosis_enriched)\n",
        "\n",
        "print(f\"\\nCodes with 7th character extension: {codes_with_extension:,} ({codes_with_extension/total_codes*100:.1f}%)\")\n",
        "print(f\"Codes without extension: {total_codes - codes_with_extension:,} ({(total_codes - codes_with_extension)/total_codes*100:.1f}%)\")\n",
        "\n",
        "# Extension character frequency\n",
        "if codes_with_extension > 0:\n",
        "    extension_freq = diagnosis_enriched[diagnosis_enriched['has_extension']]['extension'].value_counts()\n",
        "    print(f\"\\nExtension character distribution:\")\n",
        "    for ext, count in extension_freq.items():\n",
        "        print(f\"  '{ext}': {count:,} codes ({count/codes_with_extension*100:.1f}%)\")\n",
        "    \n",
        "    # Extension meaning (common patterns)\n",
        "    print(f\"\\nCommon extension meanings:\")\n",
        "    print(f\"  'A' = Initial encounter\")\n",
        "    print(f\"  'D' = Subsequent encounter\")\n",
        "    print(f\"  'S' = Sequela\")\n",
        "    print(f\"  Numbers = Specific anatomic sites or severity\")\n",
        "else:\n",
        "    print(\"\\nNo codes with 7th character extensions found in this dataset.\")\n"
    ]),
    
    # Key insights summary
    create_code_cell([
        "# Key Insights from Hierarchical Analysis\n",
        "\n",
        "print(\"\\n\" + \"=\"*80)\n",
        "print(\"KEY INSIGHTS FROM ICD-10 HIERARCHICAL ANALYSIS\")\n",
        "print(\"=\"*80)\n",
        "\n",
        "# Calculate key metrics\n",
        "n_chapters = diagnosis_enriched['chapter_name'].nunique()\n",
        "n_categories = diagnosis_enriched['category'].nunique()\n",
        "n_full_codes = diagnosis_enriched['ICD10'].nunique()\n",
        "\n",
        "category_freq = diagnosis_enriched['category'].value_counts()\n",
        "full_code_freq = diagnosis_enriched['ICD10'].value_counts()\n",
        "\n",
        "rare_categories = (category_freq < 10).sum()\n",
        "rare_full_codes = (full_code_freq < 10).sum()\n",
        "\n",
        "print(f\"\\n1. LABEL SPACE REDUCTION OPPORTUNITY:\")\n",
        "print(f\"   - Full codes (current approach): {n_full_codes} classes\")\n",
        "print(f\"   - Categories (3-char): {n_categories} classes ({n_categories/n_full_codes*100:.1f}% reduction)\")\n",
        "print(f\"   - Chapters: {n_chapters} classes ({n_chapters/n_full_codes*100:.1f}% reduction)\")\n",
        "print(f\"   → Using categories instead of full codes reduces label space by {100 - n_categories/n_full_codes*100:.1f}%\")\n",
        "\n",
        "print(f\"\\n2. RARE CLASS PROBLEM:\")\n",
        "print(f\"   - Full codes with <10 samples: {rare_full_codes} ({rare_full_codes/n_full_codes*100:.1f}%)\")\n",
        "print(f\"   - Categories with <10 samples: {rare_categories} ({rare_categories/n_categories*100:.1f}%)\")\n",
        "print(f\"   → Rolling up to categories reduces rare classes by {rare_full_codes - rare_categories} codes\")\n",
        "\n",
        "print(f\"\\n3. HIERARCHICAL MODELING STRATEGY:\")\n",
        "most_common_chapter = diagnosis_enriched['chapter_name'].value_counts().index[0]\n",
        "most_common_category = diagnosis_enriched['category'].value_counts().index[0]\n",
        "print(f\"   - Most common chapter: {most_common_chapter.split('_')[0]}\")\n",
        "print(f\"   - Most common category: {most_common_category}\")\n",
        "print(f\"   - Average codes per document: {len(diagnosis_enriched)/diagnosis_enriched['Document ID'].nunique():.1f}\")\n",
        "print(f\"   - Average chapters per document: {doc_chapter_df['num_chapters'].mean():.1f}\")\n",
        "\n",
        "print(f\"\\n4. RECOMMENDED APPROACHES (in order of priority):\")\n",
        "print(f\"   A. CATEGORY-LEVEL CLASSIFICATION:\")\n",
        "print(f\"      → Train model to predict 3-character categories ({n_categories} classes)\")\n",
        "print(f\"      → Reduces label space and rare class problems significantly\")\n",
        "print(f\"      → Expected improvement: +20-40% Macro F1\")\n",
        "\n",
        "print(f\"\\n   B. HIERARCHICAL CLASSIFICATION:\")\n",
        "print(f\"      → Step 1: Predict ICD-10 chapter ({n_chapters} classes)\")\n",
        "print(f\"      → Step 2: Predict category within chapter\")\n",
        "print(f\"      → Expected improvement: +15-30% Macro F1\")\n",
        "\n",
        "print(f\"\\n   C. CHAPTER-SPECIFIC MODELS:\")\n",
        "print(f\"      → Train separate models for each major chapter\")\n",
        "print(f\"      → Each model handles fewer, more related codes\")\n",
        "print(f\"      → Expected improvement: +10-25% Macro F1\")\n",
        "\n",
        "print(f\"\\n   D. FILTER TO FREQUENT CODES:\")\n",
        "print(f\"      → Keep only categories/codes with ≥10 samples\")\n",
        "print(f\"      → Reduces from {n_full_codes} to {(full_code_freq >= 10).sum()} codes\")\n",
        "print(f\"      → Expected improvement: +20-35% Macro F1\")\n",
        "\n",
        "print(f\"\\n\" + \"=\"*80)\n",
        "print(f\"RECOMMENDATION: Start with approach A or D for quick wins, then explore B/C.\")\n",
        "print(\"=\"*80)\n"
    ]),
    
    # Save enriched data
    create_code_cell([
        "# Save enriched diagnosis data with hierarchy columns\n",
        "\n",
        "output_path = '../data/processed/diagnosis_enriched.csv'\n",
        "diagnosis_enriched.to_csv(output_path, index=False)\n",
        "\n",
        "print(f\"\\nEnriched diagnosis data saved to: {output_path}\")\n",
        "print(f\"Columns included: {diagnosis_enriched.columns.tolist()}\")\n"
    ])
]

def main():
    notebook_path = 'notebooks/01_BioBERT_Fine-Tuning_NLP.ipynb'
    
    # Load the notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Find the insertion point (after cell 9, which is "Top 20 most common ICD-10 codes")
    # We want to insert after the exploration cells but before preprocessing
    insertion_index = 10  # This is where "## 3. Data Preprocessing" starts
    
    print(f"Original notebook has {len(notebook['cells'])} cells")
    print(f"Inserting {len(new_cells)} new cells at position {insertion_index}")
    
    # Insert the new cells
    notebook['cells'] = (
        notebook['cells'][:insertion_index] + 
        new_cells + 
        notebook['cells'][insertion_index:]
    )
    
    print(f"Updated notebook now has {len(notebook['cells'])} cells")
    
    # Save the updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)
    
    print(f"\n✅ Successfully updated {notebook_path}")
    print(f"\nAdded sections:")
    print("  - ICD-10 parsing functions")
    print("  - Hierarchical structure analysis")
    print("  - Chapter distribution analysis")
    print("  - Category-level analysis")
    print("  - Class imbalance by hierarchy")
    print("  - Extension (7th character) analysis")
    print("  - Key insights and recommendations")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())