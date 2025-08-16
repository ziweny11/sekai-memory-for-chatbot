import json
from typing import List, Dict, Any, Optional
from models.memory_unit import MemoryUnit
from storage.simple_memory_store import SimpleMemoryStore
import ollama
import numpy as np


class SimpleMemoryRetriever:
    """Memory retriever that works with SimpleMemoryStore for chapter-based retrieval"""
    
    def __init__(self, memory_store: SimpleMemoryStore, model_name: str = "mistral:7b"):
        self.memory_store = memory_store
        self.model_name = model_name
        
        # Initialize Ollama client for embeddings
        try:
            self.client = ollama.Client()
        except Exception as e:
            print(f"Warning: Could not initialize Ollama client: {e}")
            self.client = None
    
    def retrieve_by_chapter(self, chapter: int, query: str = "", k: int = 10) -> List[MemoryUnit]:
        """Retrieve memories available at a specific chapter"""
        memories = self.memory_store.get_memories_at_chapter(chapter)
        
        if not query:
            # No query, return all memories sorted by confidence
            return sorted(memories, key=lambda x: x.confidence, reverse=True)[:k]
        
        # With query, score and rank memories
        scored_memories = []
        for memory in memories:
            score = self._calculate_relevance_score(memory, query, chapter)
            scored_memories.append((memory, score))
        
        # Sort by score and return top k
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, score in scored_memories[:k]]
    
    def retrieve_by_character_at_chapter(self, character: str, chapter: int, k: int = 10) -> List[MemoryUnit]:
        """Retrieve memories involving a specific character at a chapter"""
        memories = self.memory_store.get_memories_at_chapter(chapter)
        character_memories = []
        
        for memory in memories:
            if character in memory.subjects:
                character_memories.append(memory)
        
        # Sort by confidence and return top k
        character_memories.sort(key=lambda x: x.confidence, reverse=True)
        return character_memories[:k]
    
    def retrieve_by_type_at_chapter(self, mem_type: str, chapter: int, k: int = 10) -> List[MemoryUnit]:
        """Retrieve memories of a specific type at a chapter"""
        memories = self.memory_store.get_memories_at_chapter(chapter)
        type_memories = []
        
        for memory in memories:
            if memory.mem_type == mem_type:
                type_memories.append(memory)
        
        # Sort by confidence and return top k
        type_memories.sort(key=lambda x: x.confidence, reverse=True)
        return type_memories[:k]
    
    def search_memories_at_chapter(self, query: str, chapter: int, k: int = 10) -> List[MemoryUnit]:
        """Search memories at a specific chapter using semantic similarity"""
        memories = self.memory_store.get_memories_at_chapter(chapter)
        
        if not query or not memories:
            return memories[:k]
        
        # Score memories by relevance to query
        scored_memories = []
        for memory in memories:
            score = self._calculate_relevance_score(memory, query, chapter)
            scored_memories.append((memory, score))
        
        # Sort by score and return top k
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, score in scored_memories[:k]]
    
    def get_memory_timeline(self, canonical_key: str) -> List[MemoryUnit]:
        """Get the complete timeline of a memory across chapters"""
        return self.memory_store.get_memory_timeline(canonical_key)
    
    def get_memory_evolution(self, memory_id: str) -> List[MemoryUnit]:
        """Get the complete evolution chain of a memory"""
        return self.memory_store.get_memory_evolution(memory_id)
    
    def _calculate_relevance_score(self, memory: MemoryUnit, query: str, target_chapter: int) -> float:
        """Calculate relevance score for a memory given a query and target chapter"""
        score = 0.0
        
        # 1. Base confidence (30% weight)
        score += memory.confidence * 0.3
        
        # 2. Chapter relevance (25% weight)
        chapter_score = self._calculate_chapter_relevance(memory, target_chapter)
        score += chapter_score * 0.25
        
        # 3. Semantic similarity (25% weight)
        semantic_score = self._calculate_semantic_similarity(memory, query)
        score += semantic_score * 0.25
        
        # 4. Memory type relevance (20% weight)
        type_score = self._calculate_type_relevance(memory, query)
        score += type_score * 0.2
        
        return score
    
    def _calculate_chapter_relevance(self, memory: MemoryUnit, target_chapter: int) -> float:
        """Calculate how relevant a memory is to the target chapter"""
        if memory.chapter_start == target_chapter:
            return 1.0  # Exact chapter match
        elif memory.chapter_start < target_chapter:
            # Memory from earlier chapter, still relevant
            recency = target_chapter - memory.chapter_start
            if recency <= 3:
                return 0.8  # Very recent
            elif recency <= 10:
                return 0.6  # Moderately recent
            else:
                return 0.4  # Old but still relevant
        else:
            return 0.0  # Memory from future chapter
    
    def _calculate_semantic_similarity(self, memory: MemoryUnit, query: str) -> float:
        """Calculate semantic similarity between memory and query"""
        if not query or not self.client:
            return 0.5  # Neutral score if no query or no client
        
        try:
            # Simple text similarity for now
            query_lower = query.lower()
            memory_text = memory.fact_text.lower()
            
            # Check for keyword matches
            query_words = set(query_lower.split())
            memory_words = set(memory_text.split())
            
            if not query_words:
                return 0.5
            
            # Jaccard similarity
            intersection = len(query_words.intersection(memory_words))
            union = len(query_words.union(memory_words))
            
            if union == 0:
                return 0.5
            
            return intersection / union
            
        except Exception as e:
            print(f"Error calculating semantic similarity: {e}")
            return 0.5
    
    def _calculate_type_relevance(self, memory: MemoryUnit, query: str) -> float:
        """Calculate relevance based on memory type"""
        query_lower = query.lower()
        
        if memory.mem_type == "WM" and any(word in query_lower for word in ["world", "company", "office", "policy"]):
            return 1.0
        elif memory.mem_type == "IC" and any(word in query_lower for word in ["relationship", "interaction", "meeting", "conversation"]):
            return 1.0
        elif memory.mem_type == "C2U" and any(word in query_lower for word in ["user", "me", "my", "personal"]):
            return 1.0
        
        return 0.5  # Neutral score
    
    def get_chapter_summary(self, chapter: int) -> Dict[str, Any]:
        """Get summary of memories at a specific chapter"""
        memories = self.memory_store.get_memories_at_chapter(chapter)
        
        summary = {
            "chapter": chapter,
            "total_memories": len(memories),
            "by_type": {},
            "by_confidence": {"high": 0, "medium": 0, "low": 0},
            "characters": set(),
            "top_memories": []
        }
        
        for memory in memories:
            # Count by type
            mem_type = memory.mem_type
            summary["by_type"][mem_type] = summary["by_type"].get(mem_type, 0) + 1
            
            # Count by confidence
            if memory.confidence >= 0.8:
                summary["by_confidence"]["high"] += 1
            elif memory.confidence >= 0.6:
                summary["by_confidence"]["medium"] += 1
            else:
                summary["by_confidence"]["low"] += 1
            
            # Collect characters
            summary["characters"].update(memory.subjects)
        
        # Convert set to list for JSON serialization
        summary["characters"] = list(summary["characters"])
        
        # Get top memories by confidence
        top_memories = sorted(memories, key=lambda x: x.confidence, reverse=True)[:5]
        summary["top_memories"] = [
            {
                "id": m.id,
                "fact_text": m.fact_text[:100] + "..." if len(m.fact_text) > 100 else m.fact_text,
                "confidence": m.confidence,
                "mem_type": m.mem_type
            }
            for m in top_memories
        ]
        
        return summary
