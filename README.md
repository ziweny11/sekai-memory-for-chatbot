# Sekai Memory System

A sophisticated multi-character memory management system for narrative-based applications, featuring three distinct memory types: Character-to-User (C2U), Inter-Character (IC), and World Memory (WM).

## 🎯 **What Makes Sekai Unique**

Unlike traditional single-character chatbots, Sekai's system manages complex multi-character interactions:

- **Character-to-User Memory**: Each character maintains separate memories with the same user
- **Inter-Character Memory**: Characters remember interactions with each other, creating an interconnected web
- **World Memory**: Characters retain memories about the world's evolving state across chapters

This multilayered architecture creates significant complexity compared to traditional chatbots, requiring sophisticated memory management.

## 🏗️ **System Architecture**

```
Sekai Memory System
├── Storage Layer (SimpleMemoryStore)
│   ├── Chapter-based memory organization
│   ├── Memory type classification (C2U, IC, WM)
│   └── Active/inactive memory tracking
├── Retrieval Layer (SimpleMemoryRetriever)
│   ├── Semantic search capabilities
│   ├── Chapter-aware retrieval
│   └── Relevance scoring
├── Evaluation Pipeline
│   ├── Retrieval Quality (Precision/Recall/MRR)
│   ├── Internal Consistency (Time/Character/World)
│   └── Coverage/Salience Assessment
└── Query Interface
    ├── Natural language processing
    ├── Relationship queries
    └── Timeline analysis
```

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- Required packages (see requirements.txt)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd sekai-memory

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import storage.simple_memory_store; print('✅ Setup complete!')"
```

### Basic Usage

#### 1. **Query the Memory System**
```bash
# Single query
python query_memories.py --query "what's the relation of Byleth and Edelgard before chapter 10"

# Interactive mode
python query_memories.py --interactive

# Custom memory store
python query_memories.py --memory-store "mistral_chapter_memories.jsonl" --query "your query"
```

#### 2. **Run Evaluation Pipeline**
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

#### 3. **Memory Management**
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

## 📊 **Memory Types**

### **C2U (Character-to-User)**
- Personal interactions between characters and the user
- Example: "Byleth learned about office politics from the user"
- Stored with `mem_type="C2U"`

### **IC (Inter-Character)**
- Relationships and interactions between characters
- Example: "Byleth and Edelgard had a tense meeting"
- Stored with `mem_type="IC"`

### **WM (World Memory)**
- Environmental and situational knowledge
- Example: "The company announced new policies"
- Stored with `mem_type="WM"`

## 🔍 **Query Examples**

### **Relationship Queries**
```bash
# Character relationships
"what's the relation of A and B before chapter 10"
"how do Byleth and Edelgard get along"
"what does A think of B in chapter 5"
```

### **Character Fact Queries**
```bash
# Individual character knowledge
"what does Byleth know in chapter 5"
"Byleth personality"
"what happened to Edelgard"
```

### **World/Company Queries**
```bash
# Environmental information
"what's happening in the company in chapter 3"
"company policies"
"what's new in the office"
```

### **Timeline Queries**
```bash
# Chapter summaries
"summary of chapter 7"
"what happened in chapter 5"
"timeline for chapter 3"
```

## 📈 **Evaluation Metrics**

### **A. Retrieval Quality**
- **Precision@k**: How many retrieved memories are relevant
- **Recall@k**: How many relevant memories were retrieved
- **MRR**: Mean Reciprocal Rank of first relevant memory

### **B. Internal Consistency**
- **Time Overlap Conflicts**: Same fact in different chapters
- **World Future Leaks**: Future references in world memories
- **Crosstalk Violations**: Character knowledge boundary violations
- **Symmetry Violations**: Asymmetric relationship memories

### **C. Coverage/Salience**
- **Fact Coverage Rate**: Percentage of important facts captured
- **Chapter-level Coverage**: Breakdown by individual chapters
- **Overall Coverage**: Aggregate coverage across all chapters

## 🛠️ **Configuration**

### **Memory Store Files**
- `enhanced_chapter_memories.jsonl` - Default enhanced memories
- `mistral_chapter_memories.jsonl` - Mistral-generated memories
- `memory_data.json` - Base memory data

### **Evaluation Configuration**
- `eval/scoring.yaml` - Scoring weights and thresholds
- `eval/gold/` - Gold standard evaluation data
- `eval/runs/` - Evaluation results and metrics

## 📁 **File Structure**
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

## 🔧 **Advanced Usage**

### **Custom Memory Types**
```python
# Define custom memory type
class CustomMemory(MemoryUnit):
    def __init__(self, custom_field, **kwargs):
        super().__init__(**kwargs)
        self.custom_field = custom_field
```

### **Batch Memory Operations**
```python
# Add multiple memories at once
memories = [memory1, memory2, memory3]
for memory in memories:
    store.add_new_memory(memory, chapter=memory.chapter_start)
```

### **Memory Evolution Tracking**
```python
# Get memory timeline
timeline = store.get_memory_timeline("canonical_key")
evolution = store.get_memory_evolution("memory_id")
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   ```bash
   # Ensure you're in the project root
   cd sekai-memory
   python -c "import sys; sys.path.append('.'); import storage.simple_memory_store"
   ```

2. **Memory Store Not Found**
   ```bash
   # Check if memory files exist
   ls -la *.jsonl
   # Use --memory-store flag to specify path
   python query_memories.py --memory-store "path/to/memories.jsonl"
   ```

3. **Evaluation Failures**
   ```bash
   # Check gold standard files
   ls -la eval/gold/
   # Run individual evaluations to isolate issues
   python eval/sekai_eval.py retrieval
   ```

### **Performance Optimization**
- Use smaller memory stores for testing
- Limit query results with `k` parameter
- Enable caching for repeated queries

## 📚 **API Reference**

### **SimpleMemoryStore**
- `add_new_memory(memory, chapter)` - Add new memory
- `get_memories_at_chapter(chapter)` - Get chapter memories
- `get_total_memories()` - Get total memory count
- `get_chapters_with_memories()` - Get available chapters

### **SimpleMemoryRetriever**
- `search_memories_at_chapter(query, chapter, k)` - Search memories
- `retrieve_by_character_at_chapter(character, chapter, k)` - Character-specific retrieval
- `get_chapter_summary(chapter)` - Chapter overview

### **MemoryQueryInterface**
- `query(query_text)` - Process natural language query
- Supports relationship, character, world, and timeline queries

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 **License**

[Add your license information here]

## 🙏 **Acknowledgments**

- Built for multi-character narrative applications
- Inspired by the complexity of character relationship management
- Designed for real-time memory consistency evaluation

---

**For questions and support, please open an issue in the repository.**
