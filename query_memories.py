#!/usr/bin/env python3
"""
Human Query Interface for Sekai Memory System
Allows natural language queries about character relationships, world facts, and personal memories
"""

import argparse
import json
import re
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from storage.simple_memory_store import SimpleMemoryStore
from retrieval.simple_memory_retriever import SimpleMemoryRetriever
from models.memory_unit import MemoryUnit


class MemoryQueryInterface:
    """Interface for querying memories with natural language"""
    
    def __init__(self, memory_store_path: str):
        self.memory_store = SimpleMemoryStore(memory_store_path)
        self.retriever = SimpleMemoryRetriever(self.memory_store)
        
    def query(self, query_text: str) -> str:
        """Process a natural language query and return an answer"""
        query_text = query_text.strip().lower()
        
        # Parse the query to extract key information
        parsed = self._parse_query(query_text)
        
        if not parsed:
            return "I couldn't understand your query. Please try rephrasing it."
        
        # Execute the query based on type
        if parsed["type"] == "relationship":
            return self._query_relationship(parsed)
        elif parsed["type"] == "character_facts":
            return self._query_character_facts(parsed)
        elif parsed["type"] == "world_facts":
            return self._query_world_facts(parsed)
        elif parsed["type"] == "personal_facts":
            return self._query_personal_facts(parsed)
        elif parsed["type"] == "timeline":
            return self._query_timeline(parsed)
        else:
            return self._query_general(parsed)
    
    def _parse_query(self, query_text: str) -> dict:
        """Parse natural language query to extract structured information"""
        
        # Relationship queries
        relationship_patterns = [
            r"what'?s?\s+(?:the\s+)?(?:relationship|relation)\s+(?:of|between)\s+(\w+)\s+and\s+(\w+)(?:\s+before\s+chapter\s+(\d+))?",
            r"how\s+do\s+(\w+)\s+and\s+(\w+)\s+(?:get along|interact)(?:\s+before\s+chapter\s+(\d+))?",
            r"what\s+does\s+(\w+)\s+think\s+of\s+(\w+)(?:\s+in\s+chapter\s+(\d+))?",
            r"(\w+)\s+and\s+(\w+)\s+relationship(?:\s+before\s+chapter\s+(\d+))?"
        ]
        
        for pattern in relationship_patterns:
            match = re.search(pattern, query_text)
            if match:
                char1, char2 = match.group(1), match.group(2)
                chapter_limit = int(match.group(3)) if match.group(3) else None
                return {
                    "type": "relationship",
                    "characters": [char1, char2],
                    "chapter_limit": chapter_limit,
                    "original_query": query_text
                }
        
        # Character fact queries
        character_patterns = [
            r"what\s+(?:does|do)\s+(\w+)\s+(?:know|think|feel)(?:\s+in\s+chapter\s+(\d+))?",
            r"(\w+)\s+(?:personality|background|role)(?:\s+in\s+chapter\s+(\d+))?",
            r"what\s+happened\s+to\s+(\w+)(?:\s+in\s+chapter\s+(\d+))?"
        ]
        
        for pattern in character_patterns:
            match = re.search(pattern, query_text)
            if match:
                character = match.group(1)
                chapter = int(match.group(2)) if match.group(2) else None
                return {
                    "type": "character_facts",
                    "character": character,
                    "chapter": chapter,
                    "original_query": query_text
                }
        
        # World fact queries
        world_patterns = [
            r"what'?s?\s+(?:happening|going on)\s+in\s+(?:the\s+)?(?:world|company|office)(?:\s+in\s+chapter\s+(\d+))?",
            r"(?:company|office|world)\s+(?:policies|rules|culture)(?:\s+in\s+chapter\s+(\d+))?",
            r"what'?s?\s+new\s+in\s+(?:the\s+)?(?:company|office)(?:\s+in\s+chapter\s+(\d+))?"
        ]
        
        for pattern in world_patterns:
            match = re.search(pattern, query_text)
            if match:
                chapter = int(match.group(1)) if match.group(1) else None
                return {
                    "type": "world_facts",
                    "chapter": chapter,
                    "original_query": query_text
                }
        
        # Personal fact queries
        personal_patterns = [
            r"what\s+(?:do\s+I\s+know|am\s+I\s+aware\s+of)(?:\s+in\s+chapter\s+(\d+))?",
            r"my\s+(?:thoughts|feelings|experiences)(?:\s+in\s+chapter\s+(\d+))?",
            r"what\s+(?:have\s+I\s+learned|did\s+I\s+experience)(?:\s+in\s+chapter\s+(\d+))?"
        ]
        
        for pattern in personal_patterns:
            match = re.search(pattern, query_text)
            if match:
                chapter = int(match.group(1)) if match.group(1) else None
                return {
                    "type": "personal_facts",
                    "chapter": chapter,
                    "original_query": query_text
                }
        
        # Timeline queries
        timeline_patterns = [
            r"what\s+happened\s+(?:in\s+chapter\s+(\d+)|before\s+chapter\s+(\d+))",
            r"timeline\s+(?:of|for)\s+chapter\s+(\d+)",
            r"summary\s+(?:of|for)\s+chapter\s+(\d+)"
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, query_text)
            if match:
                chapter = int(match.group(1) or match.group(2)) if (match.group(1) or match.group(2)) else None
                return {
                    "type": "timeline",
                    "chapter": chapter,
                    "original_query": query_text
                }
        
        # General query
        return {
            "type": "general",
            "query_text": query_text,
            "original_query": query_text
        }
    
    def _query_relationship(self, parsed: dict) -> str:
        """Query about relationships between characters"""
        char1, char2 = parsed["characters"]
        chapter_limit = parsed["chapter_limit"]
        
        # Find relationship memories
        relationship_memories = []
        
        if chapter_limit:
            # Search up to the specified chapter
            for chapter in range(1, chapter_limit + 1):
                memories = self.memory_store.get_memories_at_chapter(chapter)
                for memory in memories:
                    if (memory.mem_type == "IC" and 
                        memory.is_active and
                        char1 in memory.subjects and 
                        char2 in memory.subjects):
                        relationship_memories.append(memory)
        else:
            # Search all chapters
            for memory in self.memory_store.all_memories.values():
                if (memory.mem_type == "IC" and 
                    memory.is_active and
                    char1 in memory.subjects and 
                    char2 in memory.subjects):
                    relationship_memories.append(memory)
        
        if not relationship_memories:
            return f"I don't have any information about the relationship between {char1} and {char2}"
        
        # Sort by chapter and confidence
        relationship_memories.sort(key=lambda x: (x.chapter_start, -x.confidence))
        
        # Build response
        response = f"Here's what I know about the relationship between {char1} and {char2}"
        if chapter_limit:
            response += f" before chapter {chapter_limit}:\n\n"
        else:
            response += ":\n\n"
        
        for memory in relationship_memories:
            chapter_info = f"[Chapter {memory.chapter_start}]" if chapter_limit else ""
            response += f"• {chapter_info} {memory.fact_text}\n"
        
        return response
    
    def _query_character_facts(self, parsed: dict) -> str:
        """Query about character facts"""
        character = parsed["character"]
        chapter = parsed["chapter"]
        
        # Find character memories
        character_memories = []
        
        if chapter:
            memories = self.memory_store.get_memories_at_chapter(chapter)
            for memory in memories:
                if memory.is_active and character in memory.subjects:
                    character_memories.append(memory)
        else:
            # Search all chapters
            for memory in self.memory_store.all_memories.values():
                if memory.is_active and character in memory.subjects:
                    character_memories.append(memory)
        
        if not character_memories:
            return f"I don't have any information about {character}"
        
        # Sort by chapter and confidence
        character_memories.sort(key=lambda x: (x.chapter_start, -x.confidence))
        
        # Build response
        response = f"Here's what I know about {character}"
        if chapter:
            response += f" in chapter {chapter}:\n\n"
        else:
            response += ":\n\n"
        
        for memory in character_memories:
            chapter_info = f"[Chapter {memory.chapter_start}]" if not chapter else ""
            response += f"• {chapter_info} {memory.fact_text}\n"
        
        return response
    
    def _query_world_facts(self, parsed: dict) -> str:
        """Query about world/company facts"""
        chapter = parsed["chapter"]
        
        # Find world memories
        world_memories = []
        
        if chapter:
            memories = self.memory_store.get_memories_at_chapter(chapter)
            for memory in memories:
                if memory.mem_type == "WM" and memory.is_active:
                    world_memories.append(memory)
        else:
            # Search all chapters
            for memory in self.memory_store.all_memories.values():
                if memory.mem_type == "WM" and memory.is_active:
                    world_memories.append(memory)
        
        if not world_memories:
            return "I don't have any information about the world or company"
        
        # Sort by chapter and confidence
        world_memories.sort(key=lambda x: (x.chapter_start, -x.confidence))
        
        # Build response
        response = "Here's what I know about the world/company"
        if chapter:
            response += f" in chapter {chapter}:\n\n"
        else:
            response += ":\n\n"
        
        for memory in world_memories:
            chapter_info = f"[Chapter {memory.chapter_start}]" if not chapter else ""
            response += f"• {chapter_info} {memory.fact_text}\n"
        
        return response
    
    def _query_personal_facts(self, parsed: dict) -> str:
        """Query about personal/user facts"""
        chapter = parsed["chapter"]
        
        # Find personal memories
        personal_memories = []
        
        if chapter:
            memories = self.memory_store.get_memories_at_chapter(chapter)
            for memory in memories:
                if memory.mem_type == "C2U" and memory.is_active:
                    personal_memories.append(memory)
        else:
            # Search all chapters
            for memory in self.memory_store.all_memories.values():
                if memory.mem_type == "C2U" and memory.is_active:
                    personal_memories.append(memory)
        
        if not personal_memories:
            return "I don't have any personal information about you"
        
        # Sort by chapter and confidence
        personal_memories.sort(key=lambda x: (x.chapter_start, -x.confidence))
        
        # Build response
        response = "Here's what I know about you"
        if chapter:
            response += f" in chapter {chapter}:\n\n"
        else:
            response += ":\n\n"
        
        for memory in personal_memories:
            chapter_info = f"[Chapter {memory.chapter_start}]" if not chapter else ""
            response += f"• {chapter_info} {memory.fact_text}\n"
        
        return response
    
    def _query_timeline(self, parsed: dict) -> str:
        """Query about timeline/summary of a chapter"""
        chapter = parsed["chapter"]
        
        if not chapter:
            return "Please specify which chapter you'd like a summary for."
        
        # Get chapter summary
        summary = self.retriever.get_chapter_summary(chapter)
        
        response = f"Chapter {chapter} Summary:\n\n"
        response += f"Total Memories: {summary['total_memories']}\n"
        response += f"Characters: {', '.join(summary['characters'])}\n\n"
        
        # Memory breakdown by type
        response += "Memories by Type:\n"
        for mem_type, count in summary['by_type'].items():
            response += f"• {mem_type}: {count}\n"
        
        response += "\nTop Memories:\n"
        for memory in summary['top_memories']:
            response += f"• [{memory['mem_type']}] {memory['fact_text']}\n"
        
        return response
    
    def _query_general(self, parsed: dict) -> str:
        """Handle general queries with semantic search"""
        query_text = parsed["query_text"]
        
        # Try to find relevant memories across all chapters
        relevant_memories = []
        
        for memory in self.memory_store.all_memories.values():
            if memory.is_active:
                # Simple keyword matching
                query_words = set(query_text.lower().split())
                memory_words = set(memory.fact_text.lower().split())
                
                # Calculate overlap
                overlap = len(query_words.intersection(memory_words))
                if overlap > 0:
                    relevant_memories.append((memory, overlap))
        
        if not relevant_memories:
            return f"I couldn't find any relevant information for: '{parsed['original_query']}'"
        
        # Sort by relevance and confidence
        relevant_memories.sort(key=lambda x: (-x[1], -x[0].confidence))
        
        # Build response
        response = f"Here's what I found for: '{parsed['original_query']}'\n\n"
        
        for memory, relevance in relevant_memories[:5]:  # Top 5 results
            response += f"• [Chapter {memory.chapter_start}, {memory.mem_type}] {memory.fact_text}\n"
        
        return response


def main():
    parser = argparse.ArgumentParser(description="Query Sekai Memory System with natural language")
    parser.add_argument("--memory-store", default="enhanced_chapter_memories.jsonl",
                       help="Path to memory store file")
    parser.add_argument("--query", "-q", help="Query to run")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Initialize query interface
    try:
        interface = MemoryQueryInterface(args.memory_store)
        print(f"✅ Loaded memory store: {args.memory_store}")
        print(f"📚 Total memories: {interface.memory_store.get_total_memories()}")
        print(f"📖 Chapters: {interface.memory_store.get_chapters_with_memories()}")
        print()
    except Exception as e:
        print(f"❌ Error loading memory store: {e}")
        return
    
    if args.query:
        # Run single query
        print(f"🔍 Query: {args.query}")
        print("=" * 50)
        answer = interface.query(args.query)
        print(answer)
    
    elif args.interactive:
        # Interactive mode
        print("🎯 Interactive Query Mode")
        print("Type 'quit' or 'exit' to end")
        print("=" * 50)
        
        while True:
            try:
                query = input("\n❓ Your query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                print("\n💭 Processing...")
                answer = interface.query(query)
                print("\n📝 Answer:")
                print(answer)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    else:
        # Show examples
        print("🔍 Sekai Memory Query Interface")
        print("=" * 50)
        print("Examples:")
        print("• what's the relation of A and B before chapter 10")
        print("• how do Byleth and Edelgard get along")
        print("• what does Byleth know in chapter 5")
        print("• what's happening in the company in chapter 3")
        print("• what do I know about the office")
        print("• summary of chapter 7")
        print()
        print("Usage:")
        print("• python query_memories.py --query 'your query here'")
        print("• python query_memories.py --interactive")
        print()
        print("For more help: python query_memories.py --help")


if __name__ == "__main__":
    main()
