"""
Evaluation C: Coverage/Salience
Tests if the WRITE step captured important facts per chapter
"""

import json
from typing import List, Dict, Any
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from storage.simple_memory_store import SimpleMemoryStore
from eval.utils import load_jsonl, save_jsonl, text_similarity


def run_coverage_eval(
    memory_store_path: str,
    keyfacts_path: str,
    output_dir: str
) -> Dict[str, Any]:
    """Run coverage evaluation using SimpleMemoryStore"""
    
    print("=== Coverage Evaluation (Simple Memory Structure) ===")
    
    # Load data
    print("Loading data...")
    memory_store = SimpleMemoryStore(memory_store_path)
    keyfacts = load_jsonl(keyfacts_path)
    
    print(f"Memory store: {memory_store.get_total_memories()} total memories")
    print(f"Key facts: {len(keyfacts)} facts to check")
    
    # Evaluate coverage
    print("\nEvaluating coverage...")
    
    coverage_results = []
    total_facts = 0
    covered_facts = 0
    
    for fact_entry in keyfacts:
        chapter = fact_entry.get("chapter", 1)
        facts = fact_entry.get("facts", [])
        
        chapter_coverage = []
        chapter_covered = 0
        
        for fact in facts:
            total_facts += 1
            
            # Check if this fact is covered by memories
            coverage_result = check_fact_coverage(fact, memory_store, chapter)
            chapter_coverage.append(coverage_result)
            
            if coverage_result["is_covered"]:
                chapter_covered += 1
                covered_facts += 1
        
        coverage_results.append({
            "chapter": chapter,
            "facts": chapter_coverage,
            "total_facts": len(facts),
            "covered_facts": chapter_covered,
            "coverage_rate": chapter_covered / len(facts) if facts else 0.0
        })
    
    # Calculate overall metrics
    overall_coverage = covered_facts / total_facts if total_facts > 0 else 0.0
    
    # Generate detailed report
    detailed_report = {
        "overall_coverage": overall_coverage,
        "total_facts": total_facts,
        "covered_facts": covered_facts,
        "chapter_coverage": coverage_results,
        "summary": {
            "overall": overall_coverage,
            "by_chapter": {result["chapter"]: result["coverage_rate"] for result in coverage_results}
        }
    }
    
    # Save results
    output_path = Path(output_dir) / "coverage_eval_results.json"
    with open(output_path, 'w') as f:
        json.dump(detailed_report, f, indent=2)
    
    print(f"\n=== Coverage Evaluation Complete ===")
    print(f"Overall Coverage: {overall_coverage:.1%}")
    print(f"Total Facts: {total_facts}")
    print(f"Covered Facts: {covered_facts}")
    print(f"Results saved to: {output_path}")
    
    return detailed_report


def check_fact_coverage(fact: Dict[str, Any], memory_store: SimpleMemoryStore, target_chapter: int) -> Dict[str, Any]:
    """Check if a specific fact is covered by memories"""
    
    fact_text = fact.get("fact", "")
    fact_id = fact.get("id", "unknown")
    subjects = fact.get("subjects", [])
    predicate = fact.get("predicate", "")
    object_val = fact.get("object", "")
    
    # Get memories available at the target chapter
    memories = memory_store.get_memories_at_chapter(target_chapter)
    
    # Check for exact key match first
    exact_match = None
    for memory in memories:
        if (memory.subjects == subjects and 
            memory.predicate == predicate and 
            memory.object == object_val):
            exact_match = memory
            break
    
    if exact_match:
        return {
            "fact_id": fact_id,
            "fact_text": fact_text,
            "is_covered": True,
            "coverage_type": "exact_key_match",
            "matched_memory_id": exact_match.id,
            "matched_memory_text": exact_match.fact_text,
            "confidence": exact_match.confidence,
            "similarity_score": 1.0
        }
    
    # Check for high text similarity
    best_match = None
    best_similarity = 0.0
    
    for memory in memories:
        similarity = text_similarity(fact_text, memory.fact_text)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = memory
    
    # Consider covered if similarity > 0.7
    is_covered = best_similarity > 0.7
    
    return {
        "fact_id": fact_id,
        "fact_text": fact_text,
        "is_covered": is_covered,
        "coverage_type": "text_similarity" if is_covered else "not_covered",
        "matched_memory_id": best_match.id if best_match else None,
        "matched_memory_text": best_match.fact_text if best_match else None,
        "confidence": best_match.confidence if best_match else None,
        "similarity_score": best_similarity
    }


def print_coverage_summary(results: Dict[str, Any]):
    """Print a summary of coverage evaluation results"""
    
    print("\n" + "="*60)
    print("COVERAGE EVALUATION SUMMARY")
    print("="*60)
    
    print(f"Overall Coverage: {results['overall_coverage']:.1%}")
    print(f"Total Facts: {results['total_facts']}")
    print(f"Covered Facts: {results['covered_facts']}")
    
    print(f"\nChapter-wise Coverage:")
    for chapter_result in results["chapter_coverage"]:
        chapter = chapter_result["chapter"]
        coverage_rate = chapter_result["coverage_rate"]
        covered = chapter_result["covered_facts"]
        total = chapter_result["total_facts"]
        print(f"  Chapter {chapter}: {coverage_rate:.1%} ({covered}/{total})")
    
    # Show examples of covered and uncovered facts
    print(f"\nExample Covered Facts:")
    covered_examples = []
    uncovered_examples = []
    
    for chapter_result in results["chapter_coverage"]:
        for fact_result in chapter_result["facts"]:
            if fact_result["is_covered"] and len(covered_examples) < 3:
                covered_examples.append(fact_result)
            elif not fact_result["is_covered"] and len(uncovered_examples) < 3:
                uncovered_examples.append(fact_result)
    
    for i, example in enumerate(covered_examples, 1):
        print(f"  {i}. {example['fact_text'][:60]}...")
        print(f"     Matched: {example['matched_memory_text'][:60]}...")
        print(f"     Similarity: {example['similarity_score']:.3f}")
    
    print(f"\nExample Uncovered Facts:")
    for i, example in enumerate(uncovered_examples, 1):
        print(f"  {i}. {example['fact_text'][:60]}...")
        if example['matched_memory_text']:
            print(f"     Best Match: {example['matched_memory_text'][:60]}...")
            print(f"     Similarity: {example['similarity_score']:.3f}")
        else:
            print(f"     No matches found")


if __name__ == "__main__":
    # Example usage
    results = run_coverage_eval(
        memory_store_path="enhanced_chapter_memories.jsonl",
        keyfacts_path="eval/gold/keyfacts.jsonl",
        output_dir="eval/runs"
    )
    
    print_coverage_summary(results)
