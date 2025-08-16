import json
from typing import List, Dict, Any, Optional, Tuple
from models.memory_unit import MemoryUnit, Provenance
from storage.memory_store import MemoryStore
from datetime import datetime


class MemoryUpdater:
    """Handles updating existing memories with time-based priority logic"""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.update_log = []
    
    def update_memory(self, new_memory: MemoryUnit) -> Tuple[MemoryUnit, str]:
        """
        Update existing memory or create new one
        Returns: (updated_memory, action_taken)
        """
        # Find similar existing memory
        existing = self._find_similar_memory(new_memory)
        
        if existing:
            # Compare facts and decide action
            if self._same_fact(existing, new_memory):
                if self._same_time_period(existing, new_memory):
                    # Same fact, same time - merge
                    result = self._merge_memories(existing, new_memory)
                    return result, "merged"
                else:
                    # Same fact, different time - replace with newer
                    result = self._replace_memory(existing, new_memory)
                    return result, "replaced_same_fact"
            else:
                # Different fact - time-based decision
                if new_memory.chapter_start > existing.chapter_start:
                    # Newer chapter - replace old fact
                    result = self._replace_memory(existing, new_memory)
                    return result, "replaced_different_fact"
                else:
                    # Older chapter - keep existing (newer) fact
                    return existing, "kept_existing"
        else:
            # No existing memory - create new
            result = self._create_new_memory(new_memory)
            return result, "created_new"
    
    def _find_similar_memory(self, new_memory: MemoryUnit) -> Optional[MemoryUnit]:
        """Find memory with similar logical key"""
        all_memories = self.memory_store.get_all_active()
        
        for memory in all_memories:
            if self._is_similar_memory(memory, new_memory):
                return memory
        
        return None
    
    def _is_similar_memory(self, existing: MemoryUnit, new: MemoryUnit) -> bool:
        """Check if memories are similar enough to consider updating"""
        # Same memory type
        if existing.mem_type != new.mem_type:
            return False
        
        # Same subjects (characters involved)
        if set(existing.subjects) != set(new.subjects):
            return False
        
        # Same predicate (type of relationship/action)
        if existing.predicate != new.predicate:
            return False
        
        # Same visibility
        if existing.visibility != new.visibility:
            return False
        
        return True
    
    def _same_fact(self, existing: MemoryUnit, new: MemoryUnit) -> bool:
        """Check if memories represent the same fact"""
        return existing.object == new.object
    
    def _same_time_period(self, existing: MemoryUnit, new: MemoryUnit) -> bool:
        """Check if memories are from similar time periods"""
        chapter_diff = abs(new.chapter_start - existing.chapter_start)
        return chapter_diff <= 5  # Within 5 chapters = same time period
    
    def _merge_memories(self, existing: MemoryUnit, new: MemoryUnit) -> MemoryUnit:
        """Merge two memories representing the same fact"""
        # Calculate merged confidence
        merged_confidence = self._calculate_merged_confidence(existing, new)
        
        # Merge provenance
        merged_provenance = self._merge_provenance(existing.provenance, new.provenance)
        
        # Update chapter range
        chapter_start = min(existing.chapter_start, new.chapter_start)
        chapter_end = max(existing.chapter_end or existing.chapter_start, 
                         new.chapter_end or new.chapter_start)
        
        # Create merged memory
        merged_memory = MemoryUnit(
            id=existing.id,  # Keep existing ID
            mem_type=existing.mem_type,
            subjects=existing.subjects,
            fact_text=existing.fact_text,  # Keep existing text
            predicate=existing.predicate,
            object=existing.object,
            chapter_start=chapter_start,
            chapter_end=chapter_end,
            visibility=existing.visibility,
            confidence=merged_confidence,
            provenance=merged_provenance,
            version=existing.version + 1,
            supersedes=existing.supersedes,
            is_active=True,
            embedding=existing.embedding,  # Keep existing embedding
            attrs=existing.attrs
        )
        
        # Update in store
        self.memory_store.upsert(merged_memory)
        
        # Log the merge
        self._log_update("merge", existing, new, merged_memory)
        
        return merged_memory
    
    def _replace_memory(self, existing: MemoryUnit, new_memory: MemoryUnit) -> MemoryUnit:
        """Replace existing memory with new one"""
        # Deactivate existing memory
        existing.is_active = False
        existing.chapter_end = new_memory.chapter_start - 1
        existing.supersedes = None
        
        # Update existing memory in store
        self.memory_store.upsert(existing)
        
        # Create new memory with reference to old
        new_memory.supersedes = existing.id
        new_memory.version = existing.version + 1
        
        # Add to store
        self.memory_store.upsert(new_memory)
        
        # Log the replacement
        self._log_update("replace", existing, new_memory, new_memory)
        
        return new_memory
    
    def _create_new_memory(self, memory: MemoryUnit) -> MemoryUnit:
        """Create new memory in store"""
        self.memory_store.upsert(memory)
        
        # Log the creation
        self._log_update("create", None, memory, memory)
        
        return memory
    
    def _calculate_merged_confidence(self, existing: MemoryUnit, new: MemoryUnit) -> float:
        """Calculate confidence when merging memories"""
        # Weight by evidence strength (chapter recency)
        existing_weight = 1.0
        new_weight = 1.0
        
        # Bonus for multiple sources
        source_bonus = 0.1
        
        # Weighted average
        merged_confidence = (
            (existing.confidence * existing_weight + new.confidence * new_weight) 
            / (existing_weight + new_weight)
        ) + source_bonus
        
        return min(merged_confidence, 1.0)
    
    def _merge_provenance(self, existing_prov: Provenance, new_prov: Provenance) -> Provenance:
        """Merge provenance information"""
        # Keep the earlier chapter as source
        source_chapter = min(existing_prov.chapter, new_prov.chapter)
        
        # Combine sources
        sources = [existing_prov.source, new_prov.source]
        if "synopsis" in sources:
            source = "synopsis"  # Prefer synopsis over other sources
        else:
            source = " + ".join(set(sources))
        
        return Provenance(
            chapter=source_chapter,
            source=source,
            timestamp=datetime.now().isoformat()
        )
    
    def _log_update(self, action: str, old_memory: Optional[MemoryUnit], 
                   new_memory: MemoryUnit, result_memory: MemoryUnit):
        """Log memory update actions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "old_memory_id": old_memory.id if old_memory else None,
            "new_memory_id": new_memory.id,
            "result_memory_id": result_memory.id,
            "chapter_start": new_memory.chapter_start,
            "fact_text": new_memory.fact_text[:50] + "..."
        }
        
        self.update_log.append(log_entry)
    
    def get_update_log(self) -> List[Dict[str, Any]]:
        """Get the update log"""
        return self.update_log
    
    def clear_update_log(self):
        """Clear the update log"""
        self.update_log = []
    
    def batch_update(self, new_memories: List[MemoryUnit]) -> List[Tuple[MemoryUnit, str]]:
        """Update multiple memories at once"""
        results = []
        
        for memory in new_memories:
            result, action = self.update_memory(memory)
            results.append((result, action))
        
        return results


class MockMemoryUpdater(MemoryUpdater):
    """Mock updater for testing without real memory store"""
    
    def __init__(self):
        # Create a simple in-memory store for testing
        from storage.memory_store import JSONLMemoryStore
        import tempfile
        
        # Create temporary file for testing
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
        temp_file.close()
        
        memory_store = JSONLMemoryStore(temp_file.name)
        super().__init__(memory_store)
    
    def cleanup(self):
        """Clean up temporary files"""
        import os
        if hasattr(self.memory_store, 'file_path'):
            try:
                os.unlink(self.memory_store.file_path)
            except:
                pass
