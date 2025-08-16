import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from models.memory_unit import MemoryUnit
import uuid


class SimpleMemoryStore:
    """Simple memory store that maintains chapter-based memory sets"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.chapter_memories: Dict[int, List[MemoryUnit]] = {}  # chapter -> list of memories
        self.all_memories: Dict[str, MemoryUnit] = {}  # id -> memory for updates
        self.load_memories()
    
    def load_memories(self):
        """Load existing memories from file"""
        if self.file_path.exists():
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        memory_data = json.loads(line)
                        memory = MemoryUnit(**memory_data)
                        self._add_memory_to_chapter(memory, memory.chapter_start)
                        self.all_memories[memory.id] = memory
    
    def save_memories(self):
        """Save all memories to file"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            for memory in self.all_memories.values():
                f.write(memory.model_dump_json() + '\n')
    
    def _add_memory_to_chapter(self, memory: MemoryUnit, chapter: int):
        """Add memory to a specific chapter list"""
        if chapter not in self.chapter_memories:
            self.chapter_memories[chapter] = []
        self.chapter_memories[chapter].append(memory)
    
    def add_new_memory(self, memory: MemoryUnit, chapter: int):
        """Add a completely new memory to a chapter"""
        memory.id = str(uuid.uuid4())
        memory.chapter_start = chapter
        memory.provenance.chapter = chapter
        
        self._add_memory_to_chapter(memory, chapter)
        self.all_memories[memory.id] = memory
        
        return memory
    
    def find_existing_memory(self, memory: MemoryUnit) -> Optional[MemoryUnit]:
        """Find existing memory by canonical key"""
        memory_key = memory.get_key()
        
        for existing in self.all_memories.values():
            if existing.is_active and existing.get_key() == memory_key:
                return existing
        
        return None
    
    def find_all_candidate_memories(self, memory: MemoryUnit) -> List[MemoryUnit]:
        """Find all memories that could potentially be updated by this new memory"""
        memory_key = memory.get_key()
        candidates = []
        
        for existing in self.all_memories.values():
            if existing.get_key() == memory_key and existing.can_update(memory):
                candidates.append(existing)
        
        return candidates
    
    def find_best_update_candidate(self, memory: MemoryUnit, min_score: float = 0.5) -> Optional[tuple[MemoryUnit, float]]:
        """Find the best memory to update with scoring"""
        candidates = self.find_all_candidate_memories(memory)
        
        if not candidates:
            return None
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score = candidate.get_update_score(memory)
            if score >= min_score:
                scored_candidates.append((candidate, score))
        
        if not scored_candidates:
            return None
        
        # Return the candidate with highest score
        best_candidate = max(scored_candidates, key=lambda x: x[1])
        return best_candidate
    
    def update_existing_memory(self, existing_memory: MemoryUnit, new_info: MemoryUnit, chapter: int, update_reason: str = "new_information") -> MemoryUnit:
        """Advanced memory update with sophisticated tracking"""
        
        # Mark old version as superseded
        existing_memory.is_active = False
        existing_memory.chapter_end = chapter - 1
        existing_memory.superseded_by = str(uuid.uuid4())  # Will be set to new memory's ID
        
        # Create updated version with enhanced tracking
        updated_memory = MemoryUnit(
            id=str(uuid.uuid4()),
            mem_type=existing_memory.mem_type,
            subjects=existing_memory.subjects,
            predicate=existing_memory.predicate,
            object=existing_memory.object,
            fact_text=new_info.fact_text,
            chapter_start=chapter,
            chapter_end=None,
            visibility=existing_memory.visibility,
            confidence=new_info.confidence,
            is_active=True,
            provenance=new_info.provenance,
            version=existing_memory.version + 1,
            supersedes=existing_memory.id,
            superseded_by=None,
            update_reason=update_reason,
            update_confidence=new_info.confidence,
            embedding=None,
            attrs=existing_memory.attrs
        )
        
        # Link the old memory to the new one
        existing_memory.superseded_by = updated_memory.id
        
        # Add updated version to current chapter
        self._add_memory_to_chapter(updated_memory, chapter)
        self.all_memories[updated_memory.id] = updated_memory
        
        return updated_memory
    
    def smart_update_or_create(self, memory: MemoryUnit, chapter: int, update_threshold: float = 0.6) -> tuple[MemoryUnit, str]:
        """Intelligently decide whether to update existing memory or create new one"""
        
        # Find best update candidate
        update_candidate = self.find_best_update_candidate(memory, update_threshold)
        
        if update_candidate:
            existing_memory, score = update_candidate
            
            # Determine update reason based on score and context
            if score > 0.8:
                update_reason = "high_confidence_update"
            elif score > 0.6:
                update_reason = "moderate_update"
            else:
                update_reason = "low_confidence_update"
            
            # Perform the update
            updated = self.update_existing_memory(existing_memory, memory, chapter, update_reason)
            return updated, f"updated_existing_score_{score:.2f}"
        else:
            # Create new memory
            new_memory = self.add_new_memory(memory, chapter)
            return new_memory, "created_new"
    
    def get_memory_evolution(self, memory_id: str) -> List[MemoryUnit]:
        """Get the complete evolution chain of a memory"""
        evolution = []
        current_id = memory_id
        
        # Follow the chain backwards to find the original
        while current_id:
            if current_id in self.all_memories:
                memory = self.all_memories[current_id]
                evolution.insert(0, memory)  # Insert at beginning to maintain order
                current_id = memory.supersedes
            else:
                break
        
        return evolution
    
    def get_memory_timeline(self, canonical_key: str) -> List[MemoryUnit]:
        """Get all versions of a memory across time"""
        timeline = []
        
        for memory in self.all_memories.values():
            if memory.get_key() == canonical_key:
                timeline.append(memory)
        
        # Sort by chapter_start
        timeline.sort(key=lambda x: x.chapter_start)
        return timeline
    
    def get_memories_at_chapter(self, chapter: int) -> List[MemoryUnit]:
        """Get all memories available at a specific chapter"""
        memories = []
        
        # Get memories from this chapter and all previous chapters
        for ch in range(1, chapter + 1):
            if ch in self.chapter_memories:
                for memory in self.chapter_memories[ch]:
                    if memory.is_active and (memory.chapter_end is None or memory.chapter_end >= chapter):
                        memories.append(memory)
        
        return memories
    
    def get_chapter_summary(self) -> Dict[int, int]:
        """Get summary of memories per chapter"""
        return {chapter: len(memories) for chapter, memories in self.chapter_memories.items()}
    
    def get_total_memories(self) -> int:
        """Get total number of memories"""
        return len(self.all_memories)
    
    def get_chapters_with_memories(self) -> List[int]:
        """Get list of chapters that have memories"""
        return sorted(self.chapter_memories.keys())
