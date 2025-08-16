#!/usr/bin/env python3
"""
Memory Sets Generator
Processes chapter-by-chapter to build timeline of memories
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from llm.memory_extractor import MemoryExtractor, MockMemoryExtractor
from storage.simple_memory_store import SimpleMemoryStore
from models.memory_unit import MemoryUnit, Provenance
import uuid


def load_chapters(input_file: str) -> List[Dict[str, Any]]:
    """Load chapters from input file"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats: list of chapters or dict with "chapters" key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "chapters" in data:
        return data["chapters"]
    else:
        raise ValueError(f"Invalid data format in {input_file}. Expected list of chapters or dict with 'chapters' key.")


def extract_memories_from_chapter(chapter_data: Dict[str, Any], extractor, chapter_number: int) -> List[MemoryUnit]:
    """Extract memories from a single chapter"""
    memories = []
    synopsis = chapter_data.get("synopsis", "")
    
    if not synopsis:
        return memories
    
    # Split into sentences and extract from each
    sentences = [s.strip() for s in synopsis.split('.') if s.strip()]
    
    print(f"  Processing {len(sentences)} sentences...")
    
    for sentence in sentences:
        if len(sentence) < 10:  # Skip very short sentences
            continue
            
        try:
            memory = extractor.extract_memories_from_sentence(sentence, chapter_number)
            if memory:
                memories.append(memory)
                print(f"    ✓ Extracted: {memory.fact_text[:60]}...")
        except Exception as e:
            print(f"    ✗ Error extracting from: {sentence[:50]}... - {e}")
    
    return memories


def process_chapters_sequentially(chapters: List[Dict[str, Any]], extractor, memory_store: SimpleMemoryStore):
    """Process chapters sequentially, building memory timeline"""
    
    print(f"\n=== Processing {len(chapters)} chapters sequentially ===")
    
    total_new = 0
    total_updated = 0
    
    for i, chapter_data in enumerate(chapters, 1):
        chapter_number = chapter_data.get("chapter_number", i)
        print(f"\n--- Chapter {chapter_number} ---")
        
        # Extract memories from this chapter
        chapter_memories = extract_memories_from_chapter(chapter_data, extractor, chapter_number)
        
        if not chapter_memories:
            print(f"  No memories extracted from Chapter {chapter_number}")
            continue
        
        print(f"  Extracted {len(chapter_memories)} memories")
        
        # Process each memory
        for memory in chapter_memories:
            # Use smart update mechanism
            result_memory, action = memory_store.smart_update_or_create(memory, chapter_number)
            
            if "updated" in action:
                print(f"    🔄 {action}: {memory.fact_text[:50]}...")
                total_updated += 1
            else:
                print(f"    ➕ {action}: {memory.fact_text[:50]}...")
                total_new += 1
        
        # Show current state
        current_total = memory_store.get_total_memories()
        print(f"  Chapter {chapter_number} complete. Total memories: {current_total}")
    
    print(f"\n=== Processing Complete ===")
    print(f"New memories added: {total_new}")
    print(f"Existing memories updated: {total_updated}")
    print(f"Total memories: {memory_store.get_total_memories()}")
    
    return {
        "chapters_processed": len(chapters),
        "new_memories": total_new,
        "updated_memories": total_updated,
        "total_memories": memory_store.get_total_memories()
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Chapter-Based Memory Sets")
    parser.add_argument("--input", required=True, help="Input JSON file with chapter data")
    parser.add_argument("--output", default="chapter_memory_sets.jsonl", help="Output file for memory sets")
    parser.add_argument("--mock", action="store_true", help="Use mock extractor for testing")
    parser.add_argument("--model", choices=["mistral", "qwen"], default="mistral", help="Choose LLM model (default: mistral)")
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics")
    
    args = parser.parse_args()
    
    print("=== Chapter-Based Memory Sets Generator ===")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Model: {args.model}")
    print(f"Mode: {'Mock' if args.mock else 'Real LLM'}")
    print()
    
    # Load chapters
    chapters = load_chapters(args.input)
    print(f"Loaded {len(chapters)} chapters from {args.input}")
    
    # Initialize extractor
    if args.mock:
        extractor = MockMemoryExtractor()
    else:
        model_name = "mistral:7b" if args.model == "mistral" else "qwen3:8b"
        extractor = MemoryExtractor(model_name=model_name)
    
    # Initialize memory store
    memory_store = SimpleMemoryStore(args.output)
    
    # Process chapters sequentially
    results = process_chapters_sequentially(chapters, extractor, memory_store)
    
    # Save all memories
    memory_store.save_memories()
    print(f"\nMemories saved to: {args.output}")
    
    # Show final statistics
    if args.stats:
        print(f"\n=== Final Memory Store Statistics ===")
        print(f"Total memories: {memory_store.get_total_memories()}")
        
        chapter_summary = memory_store.get_chapter_summary()
        print(f"Memories per chapter:")
        for chapter in sorted(chapter_summary.keys()):
            count = chapter_summary[chapter]
            print(f"  Chapter {chapter}: {count} memories")
        
        chapters_with_memories = memory_store.get_chapters_with_memories()
        print(f"Chapters with memories: {chapters_with_memories}")
    
    print(f"\n✅ Memory generation complete!")
    print(f"You can now retrieve memories by chapter using SimpleMemoryStore.get_memories_at_chapter(chapter_number)")


if __name__ == "__main__":
    main()
