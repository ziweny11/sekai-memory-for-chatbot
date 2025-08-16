"""
Scoring and orchestration for Sekai Memory evaluation
"""

import json
import yaml
from typing import Dict, Any, List
from pathlib import Path
from .utils import timestamp_dir


def load_scoring_config(config_file: str) -> Dict[str, Any]:
    """Load scoring configuration from YAML file"""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config


def apply_gates(metrics: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply pass/fail gates to metrics"""
    gates = config.get("gates", {})
    status = "PASS"
    gate_results = {}
    
    # Check retrieval gates
    if "retrieval" in gates:
        retrieval_gates = gates["retrieval"]
        retrieval_metrics = metrics.get("retrieval", {})
        
        for gate_name, gate_config in retrieval_gates.items():
            min_value = gate_config.get("min", 0.0)
            
            # Map gate names to actual metric names in the results
            metric_mapping = {
                "precision_at_5": "precision",
                "recall_at_10": "recall", 
                "mrr": "mrr"
            }
            
            actual_metric_name = metric_mapping.get(gate_name, gate_name)
            
            # Look for the metric in the overall_metrics section
            actual_value = retrieval_metrics.get("overall_metrics", {}).get(actual_metric_name, 0.0)
            
            # Ensure we have a numeric value for comparison
            if isinstance(actual_value, (list, dict)):
                print(f"Warning: {gate_name} returned {type(actual_value).__name__}, skipping comparison")
                actual_value = 0.0
            
            if actual_value < min_value:
                status = "FAIL"
                gate_results[gate_name] = {
                    "status": "FAIL",
                    "expected": f">= {min_value}",
                    "actual": actual_value
                }
            else:
                gate_results[gate_name] = {
                    "status": "PASS",
                    "expected": f">= {min_value}",
                    "actual": actual_value
                }
    
    # Check consistency gates
    if "consistency" in gates:
        consistency_gates = gates["consistency"]
        consistency_metrics = metrics.get("consistency", {})
        
        for gate_name, gate_config in consistency_gates.items():
            max_value = gate_config.get("max", 0)
            actual_value = consistency_metrics.get(gate_name, 0)
            
            if isinstance(actual_value, (int, float)) and actual_value > max_value:
                status = "FAIL"
                gate_results[gate_name] = {
                    "status": "FAIL",
                    "expected": f"<= {max_value}",
                    "actual": actual_value
                }
            else:
                gate_results[gate_name] = {
                    "status": "PASS",
                    "expected": f"<= {max_value}",
                    "actual": actual_value
                }
    
    # Check coverage gates
    if "coverage" in gates:
        coverage_gates = gates["coverage"]
        coverage_metrics = metrics.get("coverage", {})
        
        for gate_name, gate_config in coverage_gates.items():
            min_value = gate_config.get("min", 0.0)
            # Map gate names to actual metric names
            metric_name = gate_name.replace("min_", "")
            
            # Map coverage metric names to actual result names
            coverage_mapping = {
                "overall": "overall_coverage",
                "per_chapter": "chapter_coverage"
            }
            actual_metric_name = coverage_mapping.get(metric_name, metric_name)
            actual_value = coverage_metrics.get(actual_metric_name, 0.0)
            
            # Handle chapter_coverage list by calculating average
            if metric_name == "per_chapter" and isinstance(actual_value, list):
                if actual_value:
                    # Calculate average coverage rate across all chapters
                    total_coverage = sum(chapter.get("coverage_rate", 0.0) for chapter in actual_value)
                    actual_value = total_coverage / len(actual_value)
                else:
                    actual_value = 0.0
            
            # Ensure we have a numeric value for comparison
            if isinstance(actual_value, (list, dict)):
                print(f"Warning: {gate_name} returned {type(actual_value).__name__}, skipping comparison")
                actual_value = 0.0
            
            if actual_value < min_value:
                status = "FAIL"
                gate_results[gate_name] = {
                    "status": "FAIL",
                    "expected": f">= {min_value}",
                    "actual": actual_value
                }
            else:
                gate_results[gate_name] = {
                    "status": "PASS",
                    "expected": f">= {min_value}",
                    "actual": actual_value
                }
    
    return {
        "status": status,
        "gate_results": gate_results,
        "timestamp": timestamp_dir()
    }


def consolidate_metrics(retrieval_file: str, consistency_file: str, coverage_file: str) -> Dict[str, Any]:
    """Consolidate metrics from all evaluation files"""
    metrics = {}
    
    # Load retrieval metrics
    if Path(retrieval_file).exists():
        with open(retrieval_file, 'r') as f:
            metrics["retrieval"] = json.load(f)
    
    # Load consistency results
    if Path(consistency_file).exists():
        with open(consistency_file, 'r') as f:
            metrics["consistency"] = json.load(f)
    
    # Load coverage results
    if Path(coverage_file).exists():
        with open(coverage_file, 'r') as f:
            metrics["coverage"] = json.load(f)
    
    return metrics


def run_scoring(retrieval_file: str, consistency_file: str, coverage_file: str, 
                config_file: str, output_file: str):
    """Run scoring and apply gates"""
    print("Consolidating metrics...")
    metrics = consolidate_metrics(retrieval_file, consistency_file, coverage_file)
    
    print("Loading scoring configuration...")
    config = load_scoring_config(config_file)
    
    print("Applying gates...")
    gate_results = apply_gates(metrics, config)
    
    # Combine metrics and gate results
    final_results = {
        **metrics,
        **gate_results
    }
    
    print(f"Saving final results to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"Scoring complete! Status: {gate_results['status']}")
    
    # Print gate results
    for gate_name, result in gate_results["gate_results"].items():
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {gate_name}: {result['status']} "
              f"(expected: {result['expected']}, actual: {result['actual']:.3f})")
    
    return final_results


def create_default_scoring_config(output_file: str):
    """Create a default scoring configuration file"""
    default_config = {
        "gates": {
            "retrieval": {
                "precision_at_5": {"min": 0.65},
                "recall_at_10": {"min": 0.75},
                "mrr": {"min": 0.70}
            },
            "consistency": {
                "max_time_overlap_conflicts": 0,
                "max_world_future_leaks": 0,
                "max_crosstalk_leaks": 0
            },
            "coverage": {
                "min_overall": 0.75,
                "min_per_chapter": 0.60
            }
        }
    }
    
    with open(output_file, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    print(f"Default scoring configuration created: {output_file}")
