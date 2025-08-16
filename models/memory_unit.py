from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Provenance(BaseModel):
    chapter: int
    source: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MemoryUnit(BaseModel):
    id: str
    mem_type: str
    subjects: List[str]
    predicate: str
    object: str
    fact_text: str
    chapter_start: int
    chapter_end: Optional[int] = None  # When this memory becomes outdated
    visibility: str = "shared"
    confidence: float = 0.9
    is_active: bool = True
    provenance: Provenance
    version: int = 1
    supersedes: Optional[str] = None  # ID of memory this supersedes
    superseded_by: Optional[str] = None  # ID of memory that supersedes this
    update_reason: Optional[str] = None  # Why this memory was updated
    update_confidence: Optional[float] = None  # Confidence in the update
    embedding: Optional[List[float]] = None
    attrs: Dict[str, Any] = Field(default_factory=dict)
    
    def get_key(self) -> str:
        """Generate canonical key for matching memories"""
        subjects_sorted = sorted(self.subjects)
        return f"{'::'.join(subjects_sorted)}::{self.predicate}::{self.object}"
    
    def is_world_memory(self) -> bool:
        """Check if this is a world memory"""
        return self.mem_type == "WM" and self.subjects == ["world"]
    
    def is_character_memory(self) -> bool:
        """Check if this is a character interaction memory"""
        return self.mem_type == "IC" and len(self.subjects) == 2
    
    def is_user_memory(self) -> bool:
        """Check if this is a character-to-user memory"""
        return self.mem_type == "C2U" and "user_123" in self.subjects
    
    def can_update(self, new_memory: 'MemoryUnit') -> bool:
        """Check if this memory can be updated by the new memory"""
        # Must have same canonical key
        if self.get_key() != new_memory.get_key():
            return False
        
        # Must be active
        if not self.is_active:
            return False
        
        # New memory must be from a later chapter
        if new_memory.chapter_start <= self.chapter_start:
            return False
        
        return True
    
    def get_update_score(self, new_memory: 'MemoryUnit') -> float:
        """Calculate how good an update this would be (0.0 to 1.0)"""
        if not self.can_update(new_memory):
            return 0.0
        
        score = 0.0
        
        # Higher confidence in new memory = better update
        score += new_memory.confidence * 0.3
        
        # More recent chapter = better update
        recency_bonus = min(0.2, (new_memory.chapter_start - self.chapter_start) * 0.05)
        score += recency_bonus
        
        # If new memory has higher confidence, bonus
        if new_memory.confidence > self.confidence:
            score += 0.2
        
        # If this memory is old, more likely to need update
        if self.chapter_start < new_memory.chapter_start - 5:
            score += 0.1
        
        return min(1.0, score)
