"""
Evaluation B: Internal Consistency
Checks for time-overlap conflicts, world future leaks, and scope violations
"""

import json
from typing import List, Dict, Any
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from storage.simple_memory_store import SimpleMemoryStore
from eval.utils import load_jsonl, save_jsonl


def run_consistency_eval(
    memory_store_path: str,
    output_dir: str
) -> Dict[str, Any]:
    """Run consistency evaluation using SimpleMemoryStore"""
    
    print("=== Consistency Evaluation (Simple Memory Structure) ===")
    
    # Load memory store
    print("Loading memory store...")
    memory_store = SimpleMemoryStore(memory_store_path)
    print(f"Total memories: {memory_store.get_total_memories()}")
    print(f"Chapters with memories: {memory_store.get_chapters_with_memories()}")
    
    # Run consistency checks
    print("\nRunning consistency checks...")
    
    # 1. Time overlap conflicts
    time_overlap_conflicts = check_time_overlap_conflicts(memory_store)
    print(f"Time overlap conflicts: {len(time_overlap_conflicts)}")
    
    # 2. World future leaks
    world_future_leaks = check_world_future_leaks(memory_store)
    print(f"World future leaks: {len(world_future_leaks)}")
    
    # 3. Crosstalk/scope violations
    crosstalk_violations = check_crosstalk_violations(memory_store)
    print(f"Crosstalk violations: {len(crosstalk_violations)}")
    
    # 4. Symmetry violations
    symmetry_violations = check_symmetry_violations(memory_store)
    print(f"Symmetry violations: {len(symmetry_violations)}")
    
    # Compile results
    results = {
        "time_overlap_conflicts": time_overlap_conflicts,
        "world_future_leaks": world_future_leaks,
        "crosstalk_violations": crosstalk_violations,
        "symmetry_violations": symmetry_violations,
        "summary": {
            "total_conflicts": len(time_overlap_conflicts) + len(world_future_leaks) + len(crosstalk_violations) + len(symmetry_violations),
            "time_overlap_conflicts": len(time_overlap_conflicts),
            "world_future_leaks": len(world_future_leaks),
            "crosstalk_violations": len(crosstalk_violations),
            "symmetry_violations": len(symmetry_violations)
        }
    }
    
    # Save results
    output_path = Path(output_dir) / "consistency_eval_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Consistency Evaluation Complete ===")
    print(f"Total conflicts found: {results['summary']['total_conflicts']}")
    print(f"Results saved to: {output_path}")
    
    return results


def check_time_overlap_conflicts(memory_store: SimpleMemoryStore) -> List[Dict[str, Any]]:
    """Check for memories that have conflicting temporal information"""
    conflicts = []
    
    # Get all memories
    all_memories = list(memory_store.all_memories.values())
    
    for i, memory1 in enumerate(all_memories):
        for memory2 in all_memories[i+1:]:
            # Check if memories have the same canonical key (same fact)
            if memory1.get_key() == memory2.get_key():
                # Check for temporal conflicts
                if memory1.chapter_start != memory2.chapter_start:
                    # Same fact, different chapters - potential conflict
                    if memory1.is_active and memory2.is_active:
                        conflicts.append({
                            "type": "time_overlap_conflict",
                            "memory1_id": memory1.id,
                            "memory2_id": memory2.id,
                            "canonical_key": memory1.get_key(),
                            "memory1_chapter": memory1.chapter_start,
                            "memory2_chapter": memory2.chapter_start,
                            "memory1_fact": memory1.fact_text,
                            "memory2_fact": memory2.fact_text,
                            "description": f"Same fact appears in chapters {memory1.chapter_start} and {memory2.chapter_start}"
                        })
    
    return conflicts


def check_world_future_leaks(memory_store: SimpleMemoryStore) -> List[Dict[str, Any]]:
    """Check for world memories that reference future events"""
    conflicts = []
    
    for memory in memory_store.all_memories.values():
        if memory.mem_type == "WM" and memory.is_active:
            # Check for future references in world memories
            fact_lower = memory.fact_text.lower()
            
            # Look for future indicators
            future_indicators = [
                "will", "going to", "plan to", "intend to", "future", "upcoming",
                "next week", "next month", "next year", "tomorrow", "later"
            ]
            
            for indicator in future_indicators:
                if indicator in fact_lower:
                    conflicts.append({
                        "type": "world_future_leak",
                        "memory_id": memory.id,
                        "canonical_key": memory.get_key(),
                        "chapter": memory.chapter_start,
                        "fact_text": memory.fact_text,
                        "future_indicator": indicator,
                        "description": f"World memory contains future reference: '{indicator}'"
                    })
                    break
    
    return conflicts


def check_crosstalk_violations(memory_store: SimpleMemoryStore) -> List[Dict[str, Any]]:
    """Check for memories that violate character knowledge boundaries"""
    conflicts = []
    
    # Build character knowledge timeline
    character_knowledge = {}
    
    for memory in memory_store.all_memories.values():
        if memory.is_active:
            for subject in memory.subjects:
                if subject != "world" and subject != "user_123":
                    if subject not in character_knowledge:
                        character_knowledge[subject] = {}
                    
                    chapter = memory.chapter_start
                    if chapter not in character_knowledge[subject]:
                        character_knowledge[subject][chapter] = []
                    
                    character_knowledge[subject][chapter].append(memory)
    
    # Check for knowledge violations
    for character, chapters in character_knowledge.items():
        for chapter in sorted(chapters.keys()):
            # Get what this character knows at this chapter
            known_facts = set()
            for memory in chapters[chapter]:
                key = memory.get_key()
                known_facts.add(key)
            
            # Check if character references facts they shouldn't know yet
            for memory in chapters[chapter]:
                fact_lower = memory.fact_text.lower()
                
                # Look for references to other characters' private information
                for other_char, other_chapters in character_knowledge.items():
                    if other_char != character:
                        for other_chapter, other_memories in other_chapters.items():
                            if other_chapter > chapter:  # Future information
                                for other_memory in other_memories:
                                    if other_memory.mem_type == "C2U":  # Private information
                                        if other_char.lower() in fact_lower:
                                            conflicts.append({
                                                "type": "crosstalk_violation",
                                                "memory_id": memory.id,
                                                "character": character,
                                                "chapter": chapter,
                                                "referenced_character": other_char,
                                                "referenced_chapter": other_chapter,
                                                "fact_text": memory.fact_text,
                                                "description": f"Character {character} at chapter {chapter} references future private information about {other_char}"
                                            })
    
    return conflicts


def check_symmetry_violations(memory_store: SimpleMemoryStore) -> List[Dict[str, Any]]:
    """Check for asymmetric relationship memories"""
    conflicts = []
    
    # Build relationship memory map
    relationships = {}
    
    for memory in memory_store.all_memories.values():
        if memory.mem_type == "IC" and memory.is_active and len(memory.subjects) == 2:
            # Create bidirectional key
            char1, char2 = sorted(memory.subjects)
            rel_key = f"{char1}::{char2}"
            
            if rel_key not in relationships:
                relationships[rel_key] = []
            
            relationships[rel_key].append(memory)
    
    # Check for asymmetric relationships
    for rel_key, memories in relationships.items():
        if len(memories) == 1:
            # Single memory - check if it's asymmetric
            memory = memories[0]
            fact_lower = memory.fact_text.lower()
            
            # Look for asymmetric language
            asymmetric_indicators = [
                "likes", "hates", "loves", "dislikes", "admires", "despises",
                "trusts", "distrusts", "respects", "disrespects"
            ]
            
            for indicator in asymmetric_indicators:
                if indicator in fact_lower:
                    # Check if there's a corresponding memory from the other character
                    char1, char2 = rel_key.split("::")
                    reverse_key = f"{char2}::{char1}"
                    
                    if reverse_key not in relationships:
                        conflicts.append({
                            "type": "symmetry_violation",
                            "memory_id": memory.id,
                            "relationship_key": rel_key,
                            "character1": char1,
                            "character2": char2,
                            "fact_text": memory.fact_text,
                            "asymmetric_indicator": indicator,
                            "description": f"Asymmetric relationship: {char1} {indicator} {char2} but no reciprocal memory found"
                        })
                    break
    
    return conflicts


def print_consistency_summary(results: Dict[str, Any]):
    """Print a summary of consistency evaluation results"""
    
    print("\n" + "="*60)
    print("CONSISTENCY EVALUATION SUMMARY")
    print("="*60)
    
    summary = results["summary"]
    print(f"Total Conflicts Found: {summary['total_conflicts']}")
    print(f"Time Overlap Conflicts: {summary['time_overlap_conflicts']}")
    print(f"World Future Leaks: {summary['world_future_leaks']}")
    print(f"Crosstalk Violations: {summary['crosstalk_violations']}")
    print(f"Symmetry Violations: {summary['symmetry_violations']}")
    
    if summary['total_conflicts'] == 0:
        print("\n✅ No consistency issues found!")
    else:
        print(f"\n⚠️  {summary['total_conflicts']} consistency issues detected")
        
        # Show examples of each type
        for conflict_type in ["time_overlap_conflicts", "world_future_leaks", "crosstalk_violations", "symmetry_violations"]:
            conflicts = results[conflict_type]
            if conflicts:
                print(f"\n{conflict_type.replace('_', ' ').title()}:")
                for i, conflict in enumerate(conflicts[:2], 1):  # Show first 2
                    print(f"  {i}. {conflict['description']}")
                    print(f"     Memory: {conflict['fact_text'][:60]}...")


if __name__ == "__main__":
    # Example usage
    results = run_consistency_eval(
        memory_store_path="enhanced_chapter_memories.jsonl",
        output_dir="eval/runs"
    )
    
    print_consistency_summary(results)
