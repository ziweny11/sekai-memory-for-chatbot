#!/usr/bin/env python3
"""
Sekai Memory Evaluation Suite
Updated for Simple Memory Structure
"""

import argparse
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from eval.retrieval_eval import run_retrieval_eval
from eval.consistency_eval import run_consistency_eval
from eval.coverage_eval import run_coverage_eval
from eval.scoring import run_scoring


def main():
    parser = argparse.ArgumentParser(description="Sekai Memory Evaluation Suite")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Retrieval evaluation
    retrieval_parser = subparsers.add_parser("retrieval", help="Run retrieval evaluation")
    retrieval_parser.add_argument("--memory-store", default="enhanced_chapter_memories.jsonl", 
                                 help="Path to memory store file")
    retrieval_parser.add_argument("--gold-memories", default="eval/gold/memories_gold.jsonl",
                                 help="Path to gold memories file")
    retrieval_parser.add_argument("--queries", default="eval/gold/queries.jsonl",
                                 help="Path to queries file")
    retrieval_parser.add_argument("--output-dir", default="eval/runs",
                                 help="Output directory for results")
    
    # Consistency evaluation
    consistency_parser = subparsers.add_parser("consistency", help="Run consistency evaluation")
    consistency_parser.add_argument("--memory-store", default="enhanced_chapter_memories.jsonl",
                                   help="Path to memory store file")
    consistency_parser.add_argument("--output-dir", default="eval/runs",
                                   help="Output directory for results")
    
    # Coverage evaluation
    coverage_parser = subparsers.add_parser("coverage", help="Run coverage evaluation")
    coverage_parser.add_argument("--memory-store", default="enhanced_chapter_memories.jsonl",
                                help="Path to memory store file")
    coverage_parser.add_argument("--keyfacts", default="eval/gold/keyfacts.jsonl",
                                help="Path to key facts file")
    coverage_parser.add_argument("--output-dir", default="eval/runs",
                                help="Output directory for results")
    
    # Scoring
    scoring_parser = subparsers.add_parser("score", help="Run scoring and generate report")
    scoring_parser.add_argument("--results-dir", default="eval/runs",
                               help="Directory containing evaluation results")
    scoring_parser.add_argument("--config", default="eval/scoring.yaml",
                               help="Path to scoring configuration file")
    
    # Run all evaluations
    all_parser = subparsers.add_parser("all", help="Run all evaluations")
    all_parser.add_argument("--memory-store", default="enhanced_chapter_memories.jsonl",
                           help="Path to memory store file")
    all_parser.add_argument("--gold-dir", default="eval/gold",
                           help="Directory containing gold standard files")
    all_parser.add_argument("--output-dir", default="eval/runs",
                           help="Output directory for results")
    all_parser.add_argument("--use-updated-gold", action="store_true",
                           help="Use updated gold standard files (memories_gold_updated.jsonl, queries_updated.jsonl, keyfacts_updated.jsonl)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Ensure output directory exists
    if hasattr(args, 'output_dir'):
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    if args.command == "retrieval":
        print("Running retrieval evaluation...")
        run_retrieval_eval(
            memory_store_path=args.memory_store,
            gold_memories_path=args.gold_memories,
            queries_path=args.queries,
            output_dir=args.output_dir
        )
    
    elif args.command == "consistency":
        print("Running consistency evaluation...")
        run_consistency_eval(
            memory_store_path=args.memory_store,
            output_dir=args.output_dir
        )
    
    elif args.command == "coverage":
        print("Running coverage evaluation...")
        run_coverage_eval(
            memory_store_path=args.memory_store,
            keyfacts_path=args.keyfacts,
            output_dir=args.output_dir
        )
    
    elif args.command == "score":
        print("Running scoring...")
        run_scoring(
            retrieval_file=f"{args.results_dir}/retrieval_eval_results.json",
            consistency_file=f"{args.results_dir}/consistency_eval_results.json",
            coverage_file=f"{args.results_dir}/coverage_eval_results.json",
            config_file=args.config,
            output_file=f"{args.results_dir}/final_scoring_results.json"
        )
    
    elif args.command == "all":
        print("Running all evaluations...")
        
        # Choose gold standard files based on flag
        if args.use_updated_gold:
            gold_memories = f"{args.gold_dir}/memories_gold_updated.jsonl"
            queries = f"{args.gold_dir}/queries_updated.jsonl"
            keyfacts = f"{args.gold_dir}/keyfacts_updated.jsonl"
            print("Using updated gold standard files")
        else:
            gold_memories = f"{args.gold_dir}/memories_gold.jsonl"
            queries = f"{args.gold_dir}/queries.jsonl"
            keyfacts = f"{args.gold_dir}/keyfacts.jsonl"
            print("Using original gold standard files")
        
        # Run all three evaluations
        print("\n1. Retrieval Evaluation")
        run_retrieval_eval(
            memory_store_path=args.memory_store,
            gold_memories_path=gold_memories,
            queries_path=queries,
            output_dir=args.output_dir
        )
        
        print("\n2. Consistency Evaluation")
        run_consistency_eval(
            memory_store_path=args.memory_store,
            output_dir=args.output_dir
        )
        
        print("\n3. Coverage Evaluation")
        run_coverage_eval(
            memory_store_path=args.memory_store,
            keyfacts_path=keyfacts,
            output_dir=args.output_dir
        )
        
        print("\n4. Scoring and Final Report")
        run_scoring(
            retrieval_file=f"{args.output_dir}/retrieval_eval_results.json",
            consistency_file=f"{args.output_dir}/consistency_eval_results.json",
            coverage_file=f"{args.output_dir}/coverage_eval_results.json",
            config_file="eval/scoring.yaml",
            output_file=f"{args.output_dir}/final_scoring_results.json"
        )
        
        print("\n✅ All evaluations completed!")
    
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
