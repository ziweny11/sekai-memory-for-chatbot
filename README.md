# Sekai Memory System

## Prerequisites

- Python 3.8+
- Ollama (for local LLM inference)
- Mistral 7B model

## Installation

### 1. Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [https://ollama.ai/download](https://ollama.ai/download)

### 2. Install Mistral 7B

```bash
# Start Ollama service
ollama serve

# In another terminal, pull Mistral 7B
ollama pull mistral:7b
```

### 3. Install Python Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd sekai-memory

# Install Python packages
pip install -r requirements.txt
```

## Usage

### Memory Extraction (LLM)

```bash
# Extract memories from chapter data using Mistral 7B
python llm/memory_extractor.py --input "chapter_data.json" --output "extracted_memories.jsonl"
```

### Query Memories

```bash
# Single query
python query_memories.py --query "what's the relation of Byleth and Edelgard before chapter 10"

# Interactive mode
python query_memories.py --interactive

# Custom memory store
python query_memories.py --memory-store "mistral_chapter_memories.jsonl" --query "your query"
```

### Run Evaluation Pipeline

```bash
# Run all evaluations
python eval/sekai_eval.py all --memory-store "enhanced_chapter_memories.jsonl"

# Individual evaluations
python eval/sekai_eval.py retrieval
python eval/sekai_eval.py consistency
python eval/sekai_eval.py coverage

# Scoring and final report
python eval/sekai_eval.py score
```

### Memory Management

```python
from storage.simple_memory_store import SimpleMemoryStore
from models.memory_unit import MemoryUnit

# Initialize store
store = SimpleMemoryStore("your_memories.jsonl")

# Add new memory
memory = MemoryUnit(
    fact_text="Byleth meets Edelgard for the first time",
    subjects=["byleth", "edelgard"],
    mem_type="IC",  # Inter-Character
    chapter_start=1
)
store.add_new_memory(memory, chapter=1)
```

## File Structure

```
sekai-memory/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── query_memories.py                  # Human query interface
├── main.py                           # Main application entry
├── models/
│   └── memory_unit.py                # Memory data model
├── storage/
│   └── simple_memory_store.py        # Memory storage system
├── retrieval/
│   └── simple_memory_retriever.py    # Memory retrieval engine
├── llm/
│   └── memory_extractor.py           # LLM-based memory extraction
├── eval/                             # Evaluation pipeline
│   ├── sekai_eval.py                 # Main evaluation runner
│   ├── retrieval_eval.py             # Retrieval quality tests
│   ├── consistency_eval.py           # Internal consistency checks
│   ├── coverage_eval.py              # Coverage assessment
│   └── scoring.py                    # Final scoring and reporting
└── config/                           # System configuration
    ├── defaults.py                   # Default parameters
    └── entity_registry.py            # Entity definitions
```


## API Reference

### SimpleMemoryStore
- `add_new_memory(memory, chapter)` - Add new memory
- `get_memories_at_chapter(chapter)` - Get chapter memories
- `get_total_memories()` - Get total memory count

### SimpleMemoryRetriever
- `search_memories_at_chapter(query, chapter, k)` - Search memories
- `retrieve_by_character_at_chapter(character, chapter, k)` - Character-specific retrieval

### MemoryQueryInterface
- `query(query_text)` - Process natural language query
