# Sekai Memory Evaluation Suite

A comprehensive evaluation framework for testing memory extraction, retrieval, and consistency in your Sekai Memory system.

## Overview

This evaluation suite tests three key aspects of your memory system:

1. **Evaluation A: Retrieval Quality** - Tests precision@k, recall@k, and MRR
2. **Evaluation B: Internal Consistency** - Checks for time conflicts, future leaks, and scope violations  
3. **Evaluation C: Coverage/Salience** - Tests if important facts were captured during the write step

## Quick Start

### 1. Initialize the evaluation environment

```bash
python -m eval.sekai_eval build-gold
python -m eval.sekai_eval init-config
```

This creates:
- Example gold dataset files in `eval/gold/`
- Default scoring configuration in `eval/scoring.yaml`

### 2. Edit your gold dataset

Edit the files in `eval/gold/` with your actual ground truth data:

- `memories_gold.jsonl` - Ground truth memories
- `queries.jsonl` - Retrieval test cases  
- `keyfacts.jsonl` - Chapter key facts for coverage testing

### 3. Run evaluations

```bash
# Run retrieval evaluation
python -m eval.sekai_eval run-retrieval \
  --queries eval/gold/queries.jsonl \
  --store your_memories.jsonl \
  --model qwen3:8b

# Check consistency
python -m eval.sekai_eval check-consistency \
  --store your_memories.jsonl \
  --queries eval/gold/queries.jsonl

# Evaluate coverage
python -m eval.sekai_eval coverage \
  --keyfacts eval/gold/keyfacts.jsonl \
  --store your_memories.jsonl

# Run scoring and apply gates
python -m eval.sekai_eval score \
  --retrieval eval/runs/20240816_123456/retrieval.jsonl \
  --consistency eval/runs/20240816_123456/consistency.json \
  --coverage eval/runs/20240816_123456/coverage.json \
  --config eval/scoring.yaml
```

## Data Formats

### Gold Memories (`memories_gold.jsonl`)

```json
{
  "id": "g-26-1",
  "chapter_start": 26,
  "mem_type": "IC",
  "subjects": ["dedue", "dimitri"],
  "predicate": "evidence",
  "object": "dedue_found_earring",
  "fact_text": "Dedue found Byleth's earring at Dimitri's home.",
  "visibility": "shared",
  "confidence": 0.9
}
```

### Queries (`queries.jsonl`)

```json
{
  "qid": "q-31-sylvain",
  "chapter": 31,
  "speaker": "sylvain",
  "participants": ["sylvain", "byleth", "dimitri"],
  "mem_types": ["IC", "WM"],
  "k": 10,
  "gold_ids": ["g-26-1", "g-31-1"]
}
```

### Key Facts (`keyfacts.jsonl`)

```json
{
  "chapter": 26,
  "facts": [
    {
      "id": "kf-26-1",
      "subjects": ["dedue", "dimitri"],
      "predicate": "evidence",
      "object": "dedue_found_earring",
      "weight": 3,
      "text": "Dedue found earring proving Byleth–Dimitri affair."
    }
  ]
}
```

## Scoring Configuration

Edit `eval/scoring.yaml` to customize your pass/fail thresholds:

```yaml
gates:
  retrieval:
    precision_at_5: {min: 0.65}    # Must achieve 65% precision@5
    recall_at_10: {min: 0.75}      # Must achieve 75% recall@10
    mrr: {min: 0.70}               # Must achieve 70% MRR
  consistency:
    max_time_overlap_conflicts: 0   # No time conflicts allowed
    max_world_future_leaks: 0      # No future leaks allowed
    max_crosstalk_leaks: 0         # No scope violations allowed
  coverage:
    min_overall: 0.75              # Must cover 75% of key facts overall
    min_per_chapter: 0.60          # Must cover 60% per chapter
```

## Output Structure

Results are saved in timestamped directories under `eval/runs/`:

```
eval/runs/20240816_123456/
├── retrieval.jsonl          # Raw retrieval results
├── retrieval_metrics.json   # Retrieval metrics summary
├── consistency.json         # Consistency check results
├── coverage.json            # Coverage evaluation results
└── metrics.json             # Final consolidated results with gates
```

## Metrics Explained

### Retrieval Quality
- **Precision@K**: Percentage of retrieved memories that are relevant
- **Recall@K**: Percentage of relevant memories that were retrieved
- **MRR**: Mean Reciprocal Rank of first relevant result

### Consistency Checks
- **Time Overlap Conflicts**: Memories with overlapping time periods but different objects
- **World Future Leaks**: Memories from future chapters retrieved at earlier chapters
- **Crosstalk Leaks**: Scope violations (e.g., C2U memories without proper context)

### Coverage
- **Overall Coverage**: Weighted percentage of key facts captured
- **Per-Chapter Coverage**: Coverage within each individual chapter

## Integration with CI/CD

The evaluation suite exits with non-zero code if any gates fail, making it suitable for CI/CD pipelines:

```bash
python -m eval.sekai_eval score \
  --retrieval runs/latest/retrieval.jsonl \
  --consistency runs/latest/consistency.json \
  --coverage runs/latest/coverage.json \
  --config eval/scoring.yaml

# Exit code 0 = PASS, Exit code 1 = FAIL
if [ $? -eq 0 ]; then
  echo "✅ Evaluation passed"
else
  echo "❌ Evaluation failed"
  exit 1
fi
```

## Customization

### Adding New Metrics
Extend the evaluation modules in `eval/` to add new metrics and checks.

### Custom Gates
Modify `eval/scoring.py` to add new gate types and validation logic.

### LLM-as-Judge (Optional)
For borderline cases, you can implement LLM-based fact similarity using Ollama:

```python
# In coverage_eval.py
def _llm_judge_same_fact(self, fact, chapter_memories):
    # Use Qwen3 8B to judge if facts are the same
    # This provides more nuanced similarity assessment
    pass
```

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure you're running from the project root
2. **Missing dependencies**: Install PyYAML: `pip install PyYAML`
3. **File not found**: Check that all input files exist and paths are correct

### Debug Mode
Add `--verbose` flags to see detailed output during evaluation.

## Contributing

To extend the evaluation suite:
1. Add new evaluation modules in `eval/`
2. Update the CLI interface in `eval/sekai_eval.py`
3. Add corresponding gates in `eval/scoring.py`
4. Update this README with new functionality

## License

This evaluation suite is part of the Sekai Memory project.
