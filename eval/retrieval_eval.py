"""
Evaluation A: Retrieval Quality
Tests precision@k, recall@k, and MRR for memory retrieval
"""

import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from storage.simple_memory_store import SimpleMemoryStore
from retrieval.simple_memory_retriever import SimpleMemoryRetriever
from eval.utils import canonical_key, load_jsonl, save_jsonl, calculate_precision_recall_mrr


def run_retrieval_eval(
    memory_store_path: str,
    gold_memories_path: str,
    queries_path: str,
    output_dir: str
) -> Dict[str, Any]:
    """Run retrieval evaluation using SimpleMemoryStore and SimpleMemoryRetriever"""
    
    print("=== Retrieval Evaluation (Simple Memory Structure) ===")
    
    # Load data
    print("Loading data...")
    memory_store = SimpleMemoryStore(memory_store_path)
    gold_memories = load_jsonl(gold_memories_path)
    queries = load_jsonl(queries_path)
    
    print(f"Memory store: {memory_store.get_total_memories()} total memories")
    print(f"Gold memories: {len(gold_memories)} memories")
    print(f"Queries: {len(queries)} queries")
    
    # Initialize retriever
    retriever = SimpleMemoryRetriever(memory_store)
    
    # Build gold key mapping
    gold_key_map = {}
    for gold_memory in gold_memories:
        key = canonical_key(gold_memory["subjects"], gold_memory["predicate"], gold_memory["object"])
        gold_key_map[key] = gold_memory["id"]
    
    print(f"Gold key mapping: {len(gold_key_map)} unique keys")
    
    # Evaluate each query
    results = []
    total_precision = 0.0
    total_recall = 0.0
    total_mrr = 0.0
    
    print(f"\nEvaluating {len(queries)} queries...")
    
    for i, query in enumerate(queries, 1):
        print(f"Query {i}/{len(queries)}: {query['qid']}")
        
        # Get target chapter from query
        target_chapter = query.get("chapter", 1)
        
        # Retrieve memories for this query
        retrieved_memories = retriever.search_memories_at_chapter(
            query=query.get("query", ""),
            chapter=target_chapter,
            k=query.get("k", 5)
        )
        
        # Evaluate this query
        query_result = _evaluate_query(
            query, retrieved_memories, gold_key_map, target_chapter
        )
        
        results.append(query_result)
        
        # Accumulate metrics
        total_precision += query_result["precision"]
        total_recall += query_result["recall"]
        total_mrr += query_result["mrr"]
        
        print(f"  Precision: {query_result['precision']:.3f}, Recall: {query_result['recall']:.3f}, MRR: {query_result['mrr']:.3f}")
    
    # Calculate overall metrics
    num_queries = len(queries)
    overall_metrics = {
        "precision": total_precision / num_queries,
        "recall": total_recall / num_queries,
        "mrr": total_mrr / num_queries
    }
    
    # Generate detailed report
    detailed_report = _generate_detailed_report(results, overall_metrics)
    
    # Save results
    output_path = Path(output_dir) / "retrieval_eval_results.json"
    with open(output_path, 'w') as f:
        json.dump(detailed_report, f, indent=2)
    
    print(f"\n=== Retrieval Evaluation Complete ===")
    print(f"Overall Precision: {overall_metrics['precision']:.3f}")
    print(f"Overall Recall: {overall_metrics['recall']:.3f}")
    print(f"Overall MRR: {overall_metrics['mrr']:.3f}")
    print(f"Results saved to: {output_path}")
    
    return detailed_report


def _evaluate_query(
    query: Dict[str, Any],
    retrieved_memories: List,
    gold_key_map: Dict[str, str],
    target_chapter: int
) -> Dict[str, Any]:
    """Evaluate a single query"""
    
    query_id = query["qid"]
    gold_ids = set(query.get("gold_ids", []))
    k = query.get("k", 5)
    
    # Convert retrieved memories to evaluation format
    retrieved_keys = []
    retrieval_analysis = []
    
    for i, memory in enumerate(retrieved_memories[:k]):
        # Generate canonical key for this memory
        key = canonical_key(memory.subjects, memory.predicate, memory.object)
        retrieved_keys.append(key)
        
        # Check if this memory matches any gold memory
        gold_id = gold_key_map.get(key)
        is_correct = gold_id in gold_ids if gold_id else False
        
        # Detailed analysis
        retrieval_analysis.append({
            "rank": i + 1,
            "memory_id": memory.id,
            "canonical_key": key,
            "matched_gold_id": gold_id,
            "fact_text": memory.fact_text,
            "subjects": memory.subjects,
            "predicate": memory.predicate,
            "object": memory.object,
            "chapter_start": memory.chapter_start,
            "mem_type": memory.mem_type,
            "confidence": memory.confidence,
            "is_correct": is_correct
        })
    
    # Calculate metrics
    precision, recall, mrr = calculate_precision_recall_mrr(
        retrieved_keys, list(gold_key_map.keys()), gold_ids
    )
    
    return {
        "query_id": query_id,
        "target_chapter": target_chapter,
        "k": k,
        "gold_ids": list(gold_ids),
        "retrieved_keys": retrieved_keys,
        "precision": precision,
        "recall": recall,
        "mrr": mrr,
        "retrieval_analysis": retrieval_analysis
    }


def _generate_detailed_report(results: List[Dict], overall_metrics: Dict) -> Dict[str, Any]:
    """Generate detailed evaluation report"""
    
    # Sort results by performance
    results_by_performance = sorted(results, key=lambda x: x["precision"], reverse=True)
    
    # Find top and bottom performing queries
    top_queries = results_by_performance[:5]
    bottom_queries = results_by_performance[-5:]
    
    # Analyze failure patterns
    failed_queries = [r for r in results if r["precision"] == 0.0]
    partial_queries = [r for r in results if 0.0 < r["precision"] < 1.0]
    perfect_queries = [r for r in results if r["precision"] == 1.0]
    
    # Chapter-wise analysis
    chapter_performance = {}
    for result in results:
        chapter = result["target_chapter"]
        if chapter not in chapter_performance:
            chapter_performance[chapter] = {"count": 0, "precision": 0.0, "recall": 0.0, "mrr": 0.0}
        
        chapter_performance[chapter]["count"] += 1
        chapter_performance[chapter]["precision"] += result["precision"]
        chapter_performance[chapter]["recall"] += result["recall"]
        chapter_performance[chapter]["mrr"] += result["mrr"]
    
    # Calculate averages
    for chapter in chapter_performance:
        count = chapter_performance[chapter]["count"]
        chapter_performance[chapter]["precision"] /= count
        chapter_performance[chapter]["recall"] /= count
        chapter_performance[chapter]["mrr"] /= count
    
    return {
        "overall_metrics": overall_metrics,
        "query_results": results,
        "performance_analysis": {
            "total_queries": len(results),
            "perfect_queries": len(perfect_queries),
            "partial_queries": len(partial_queries),
            "failed_queries": len(failed_queries),
            "success_rate": len(perfect_queries) / len(results)
        },
        "top_performing_queries": [
            {
                "query_id": r["query_id"],
                "precision": r["precision"],
                "recall": r["recall"],
                "mrr": r["mrr"]
            }
            for r in top_queries
        ],
        "bottom_performing_queries": [
            {
                "query_id": r["query_id"],
                "precision": r["precision"],
                "recall": r["recall"],
                "mrr": r["mrr"]
            }
            for r in bottom_queries
        ],
        "chapter_performance": chapter_performance,
        "failure_analysis": {
            "failed_query_ids": [r["query_id"] for r in failed_queries],
            "partial_query_ids": [r["query_id"] for r in partial_queries]
        }
    }


def print_summary_report(results: Dict[str, Any]):
    """Print a summary of the evaluation results"""
    
    print("\n" + "="*60)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("="*60)
    
    overall = results["overall_metrics"]
    print(f"Overall Performance:")
    print(f"  Precision: {overall['precision']:.3f}")
    print(f"  Recall: {overall['recall']:.3f}")
    print(f"  MRR: {overall['mrr']:.3f}")
    
    perf = results["performance_analysis"]
    print(f"\nQuery Performance:")
    print(f"  Total Queries: {perf['total_queries']}")
    print(f"  Perfect Queries: {perf['perfect_queries']} ({perf['success_rate']:.1%})")
    print(f"  Partial Queries: {perf['partial_queries']}")
    print(f"  Failed Queries: {perf['failed_queries']}")
    
    print(f"\nTop Performing Queries:")
    for i, query in enumerate(results["top_performing_queries"][:3], 1):
        print(f"  {i}. {query['query_id']}: P={query['precision']:.3f}, R={query['recall']:.3f}, MRR={query['mrr']:.3f}")
    
    print(f"\nBottom Performing Queries:")
    for i, query in enumerate(results["bottom_performing_queries"][:3], 1):
        print(f"  {i}. {query['query_id']}: P={query['precision']:.3f}, R={query['recall']:.3f}, MRR={query['mrr']:.3f}")
    
    print(f"\nChapter-wise Performance:")
    for chapter in sorted(results["chapter_performance"].keys()):
        perf = results["chapter_performance"][chapter]
        print(f"  Chapter {chapter}: P={perf['precision']:.3f}, R={perf['recall']:.3f}, MRR={perf['mrr']:.3f} ({perf['count']} queries)")


if __name__ == "__main__":
    # Example usage
    results = run_retrieval_eval(
        memory_store_path="enhanced_chapter_memories.jsonl",
        gold_memories_path="eval/gold/memories_gold.jsonl",
        queries_path="eval/gold/queries.jsonl",
        output_dir="eval/runs"
    )
    
    print_summary_report(results)
