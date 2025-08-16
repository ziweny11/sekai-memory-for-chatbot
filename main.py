#!/usr/bin/env python3
"""
Sekai Memory System - Main Application
Converts chapter synopses into structured memories using LLM extraction
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List

from models.chapter import Chapter
from storage.temporal_memory_store import TemporalMemoryStore
from pipeline.memory_pipeline import MemoryPipeline
from llm.memory_extractor import MemoryExtractor, MockMemoryExtractor


def load_chapters(file_path: str) -> List[Chapter]:
    """Load chapters from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chapters_data = json.load(f)
        
        chapters = []
        for chapter_data in chapters_data:
            chapter = Chapter(**chapter_data)
            chapters.append(chapter)
        
        print(f"Loaded {len(chapters)} chapters from {file_path}")
        return chapters
        
    except Exception as e:
        print(f"Error loading chapters: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Sekai Memory System - Temporal Architecture")
    parser.add_argument("--input", required=True, help="Input JSON file with chapter data")
    parser.add_argument("--output", default="temporal_memories.jsonl", help="Output JSONL file for memories")
    parser.add_argument("--mock", action="store_true", help="Use mock extractor for testing")
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics")
    parser.add_argument("--model", choices=["mistral", "qwen"], default="mistral", help="Choose LLM model (default: mistral)")
    
    args = parser.parse_args()
    
    print("=== Sekai Memory System (Temporal Architecture) ===")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Model: {args.model}")
    print(f"Mode: {'Mock' if args.mock else 'Real LLM'}")
    print()
    
    # Load input data
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chapters = data.get("chapters", [])
    print(f"Loaded {len(chapters)} chapters from {args.input}")
    print()
    
    # Initialize memory store
    memory_store = TemporalMemoryStore(args.output)
    
    # Initialize extractor based on model choice
    if args.mock:
        extractor = MockMemoryExtractor()
    else:
        model_name = "mistral:7b" if args.model == "mistral" else "qwen3:8b"
        extractor = MemoryExtractor(model_name=model_name)
    
    # Initialize pipeline
    pipeline = MemoryPipeline(extractor, memory_store)
    
    # Process chapters
    print("Processing chapters...")
    results = pipeline.process_chapters(chapters)
    
    # Show results
    print("\n=== Results ===")
    print(f"Chapters processed: {results['chapters_processed']}")
    print(f"Sentences processed: {results['sentences_processed']}")
    print(f"Memories extracted: {results['memories_extracted']}")
    print(f"Memories written: {results['memories_written']}")
    print(f"LLM errors: {results['llm_errors']}")
    print(f"Validation errors: {results['validation_errors']}")
    
    # Show breakdown by type
    print("\nBy type:")
    for mem_type in ["WM", "IC", "C2U"]:
        count = results.get(f"{mem_type.lower()}_count", 0)
        print(f"  {mem_type}: {count}")
    
    # Show TEMPORAL memory store stats
    print(f"\n=== Temporal Memory Store Stats ===")
    print(f"Total memories: {len(memory_store.memories)}")
    print(f"Chapters available: {sorted(memory_store.chapter_index.keys())}")
    
    for chapter in sorted(memory_store.chapter_index.keys()):
        chapter_memories = memory_store.get_memories_at_chapter(chapter)
        print(f"  Chapter {chapter}: {len(chapter_memories)} memories")
        for i, memory in enumerate(chapter_memories[:3], 1):  # Show first 3
            print(f"    {i}. {memory.fact_text[:60]}...")
    
    # Show character analysis
    print(f"\n=== Character Analysis ===")
    for chapter in sorted(memory_store.chapter_index.keys()):
        characters = memory_store.get_character_memories_at_chapter(chapter)
        if characters:
            char_names = list(set([char for mem in characters for char in mem.subjects]))
            print(f"  Chapter {chapter}: {', '.join(char_names)}")
    
    print(f"\nTemporal memories saved to: {args.output}")

if __name__ == "__main__":
    main()
