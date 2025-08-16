"""
Utility functions for Sekai Memory evaluation
"""

import json
from typing import List, Dict, Any, Union
from pathlib import Path
import re


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def save_jsonl(data: List[Dict[str, Any]], file_path: str):
    """Save data to JSONL file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')


def canonical_key(subjects: List[str], predicate: str, object_val: str) -> str:
    """Generate canonical key for a memory"""
    subjects_sorted = sorted(subjects)
    return f"{'::'.join(subjects_sorted)}::{predicate}::{object_val}"


def text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using simple word overlap"""
    if not text1 or not text2:
        return 0.0
    
    # Normalize text
    text1_lower = re.sub(r'[^\w\s]', '', text1.lower())
    text2_lower = re.sub(r'[^\w\s]', '', text2.lower())
    
    # Split into words
    words1 = set(text1_lower.split())
    words2 = set(text2_lower.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def calculate_precision_recall_mrr(retrieved_keys: List[str], all_gold_keys: List[str], gold_ids: List[str]) -> tuple[float, float, float]:
    """Calculate precision, recall, and MRR for retrieval evaluation"""
    
    # For now, we'll use a simplified approach since we don't have direct gold ID mapping
    # In practice, you'd want to map retrieved canonical keys to gold IDs
    
    # Count correct retrievals (this is simplified)
    correct = 0
    for key in retrieved_keys:
        if key in all_gold_keys:
            correct += 1
    
    # Calculate metrics
    precision = correct / len(retrieved_keys) if retrieved_keys else 0.0
    recall = correct / len(gold_ids) if gold_ids else 0.0
    
    # Simplified MRR (assuming first correct match)
    mrr = 0.0
    for i, key in enumerate(retrieved_keys):
        if key in all_gold_keys:
            mrr = 1.0 / (i + 1)
            break
    
    return precision, recall, mrr


def timestamp_dir() -> str:
    """Generate timestamped directory name"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")
