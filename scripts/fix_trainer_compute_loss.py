"""
Fix compute_loss method signature in custom trainer classes.
Adds num_items_in_batch parameter to match new Transformers API.
"""

import json
import sys

def fix_trainer_classes(notebook_path):
    """Fix FocalTrainer and AsymmetricTrainer compute_loss signatures."""
    
    # Load notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    changes_made = 0
    
    # Iterate through cells
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = cell['source']
            
            # Convert to string if it's a list
            if isinstance(source, list):
                source_str = ''.join(source)
            else:
                source_str = source
            
            # Check if this cell contains FocalTrainer
            if 'class FocalTrainer(Trainer):' in source_str:
                print("Found FocalTrainer - updating compute_loss signature...")
                
                # Fix the signature
                new_source = []
                for line in cell['source']:
                    if 'def compute_loss(self, model, inputs, return_outputs=False):' in line:
                        new_source.append('    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):\n')
                    elif 'loss = FocalLoss(alpha=0.25, gamma=2.0)(logits, labels)' in line:
                        new_source.append(line)
                        # Add reduction logic after loss calculation
                        new_source.append('        # Apply reduction if num_items_in_batch is provided\n')
                        new_source.append('        if num_items_in_batch is not None:\n')
                        new_source.append('            loss = loss / num_items_in_batch\n')
                    else:
                        new_source.append(line)
                
                cell['source'] = new_source
                changes_made += 1
                print("  [OK] FocalTrainer updated")
            
            # Check if this cell contains AsymmetricTrainer
            if 'class AsymmetricTrainer(Trainer):' in source_str:
                print("Found AsymmetricTrainer - updating compute_loss signature...")
                
                # Fix the signature
                new_source = []
                for line in cell['source']:
                    if 'def compute_loss(self, model, inputs, return_outputs=False):' in line:
                        new_source.append('    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):\n')
                    elif 'loss = AsymmetricLoss(gamma_neg=4, gamma_pos=1, clip=0.05)(logits, labels)' in line:
                        new_source.append(line)
                        # Add reduction logic after loss calculation
                        new_source.append('        # Apply reduction if num_items_in_batch is provided\n')
                        new_source.append('        if num_items_in_batch is not None:\n')
                        new_source.append('            loss = loss / num_items_in_batch\n')
                    else:
                        new_source.append(line)
                
                cell['source'] = new_source
                changes_made += 1
                print("  [OK] AsymmetricTrainer updated")
    
    # Save notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"\n[OK] Fixed {changes_made} trainer classes")
    print(f"[OK] Saved changes to {notebook_path}")
    
    return changes_made

if __name__ == '__main__':
    notebook_path = 'notebooks/01_BioBERT_Fine-Tuning_NLP.ipynb'
    
    print("="*80)
    print("FIXING TRAINER COMPUTE_LOSS SIGNATURES")
    print("="*80)
    print(f"\nNotebook: {notebook_path}\n")
    
    changes = fix_trainer_classes(notebook_path)
    
    if changes == 2:
        print("\n" + "="*80)
        print("SUCCESS: Both trainer classes have been updated!")
        print("="*80)
        print("\nThe compute_loss methods now accept num_items_in_batch parameter")
        print("and properly handle reduction when needed.")
    else:
        print(f"\n[WARNING] Expected 2 changes but made {changes}")
        sys.exit(1)