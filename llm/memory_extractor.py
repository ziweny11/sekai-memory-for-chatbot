import json
import re
from typing import List, Optional, Dict, Any
from models.memory_unit import MemoryUnit, Provenance
import ollama
from config.entity_registry import load_entity_registry
from config.predicate_vocabulary import load_predicate_vocabulary
from config.defaults import load_defaults
import uuid


class MemoryExtractor:
    """LLM-based memory extraction from narrative text"""
    
    def __init__(self, model_name: str = "mistral:7b"):
        self.model_name = model_name
        self.entity_registry = load_entity_registry()
        self.predicate_vocab = load_predicate_vocabulary()
        self.defaults = load_defaults()
        
        # Initialize Ollama client
        try:
            self.client = ollama.Client()
        except Exception as e:
            print(f"Warning: Could not initialize Ollama client: {e}")
            self.client = None
    
    def extract_memories_from_sentence(self, sentence: str, chapter_number: int) -> Optional[MemoryUnit]:
        """Extract a single memory from a sentence using LLM"""
        if not self.client:
            print("LLM client not available, skipping extraction")
            return None
        
        # Create the system prompt
        system_prompt = self._create_system_prompt()
        
        # Create the user prompt
        user_prompt = self._create_user_prompt(sentence, chapter_number)
        
        try:
            # Call the LLM
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={"temperature": 0.05}  # Very low temperature for consistent extraction
            )
            
            # Parse the response
            content = response['message']['content']
            memory_data = self._parse_llm_response(content)
            
            if memory_data and memory_data.get("emit", True):
                return self._create_memory_unit(memory_data, chapter_number)
            
        except Exception as e:
            print(f"Error extracting memory from sentence: {e}")
            print(f"Sentence: {sentence}")
        
        return None
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for memory extraction"""
        return """You are a memory extractor. Extract facts from sentences and return JSON.

Memory types:
- WM: World events, policies, office dynamics
- IC: Character interactions and relationships  
- C2U: Character knowledge about user

Rules:
- Return ONLY valid JSON
- Use provided vocabulary for predicate/object
- Set confidence 0.7-1.0
- Keep fact_text under 140 characters
- If no fact found, return {"emit": false}
- CRITICAL: Only use characters that exist in the provided character list
- DO NOT invent or assume characters that aren't mentioned in the data
- BE AGGRESSIVE: Extract multiple memories if a sentence contains multiple facts
- Look for implicit relationships, character states, and world details
- Even minor interactions or observations should be captured"""
    
    def _create_user_prompt(self, sentence: str, chapter_number: int) -> str:
        """Create the user prompt for a specific sentence"""
        # Build character mapping
        char_mapping = []
        for name, char_id in self.entity_registry["character_aliases"].items():
            char_mapping.append(f'{name}->"{char_id}"')
        
        # Build predicate vocabulary
        predicate_json = json.dumps(self.predicate_vocab, indent=2)
        
        return f"""Entities (IDs):
- world: "{self.entity_registry['world_id']}"
- user: "{self.entity_registry['user_id']}"
- characters:
  {', '.join(char_mapping)}

Predicate vocabulary:
{predicate_json}

Visibility defaults: WM=global, IC=shared, C2U=private

Sentence: "{sentence}"
Chapter: {chapter_number}

IMPORTANT: This sentence may contain multiple facts. Extract ALL relevant memories.
Look for:
- Character relationships and interactions
- World events and settings
- Character knowledge and observations
- Implicit facts and implications

Output JSON schema:
{{
  "emit": boolean,
  "mem_type": "WM" | "IC" | "C2U",
  "subjects": [string],
  "fact_text": string,
  "predicate": string,
  "object": string,
  "visibility": "global" | "shared" | "private",
  "confidence": number
}}

If multiple memories exist, return the most important one first."""
    
    def _parse_llm_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse and validate LLM response with repair logic"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
                
                # Validate required fields and set defaults
                if parsed_data.get("emit", True):
                    # Ensure all required fields exist
                    required_fields = ["mem_type", "subjects", "fact_text", "predicate", "object", "confidence"]
                    for field in required_fields:
                        if field not in parsed_data or parsed_data[field] is None:
                            print(f"Missing or null field '{field}' in LLM response")
                            return None
                    
                    # Validate object field specifically
                    if not parsed_data["object"] or parsed_data["object"] == "":
                        print(f"Invalid object value: {parsed_data['object']}")
                        return None
                    
                    return parsed_data
                else:
                    return None
                    
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Try to repair common JSON issues
            repaired_data = self._repair_json_response(content)
            if repaired_data:
                return repaired_data
            print(f"Content: {content}")
        
        return None
    
    def _repair_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Attempt to repair common JSON formatting issues"""
        try:
            # Remove common LLM artifacts
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            # Try to fix common issues
            cleaned = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*):', r'"\1":', cleaned)  # Quote keys
            cleaned = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)', r': "\1"', cleaned)  # Quote string values
            
            # Try to parse repaired JSON
            parsed = json.loads(cleaned)
            if self._validate_repaired_data(parsed):
                print(f"Successfully repaired malformed JSON response")
                return parsed
                
        except Exception as e:
            print(f"JSON repair failed: {e}")
        
        return None
    
    def _validate_repaired_data(self, data: Dict[str, Any]) -> bool:
        """Validate that repaired data has required fields"""
        required = ["mem_type", "subjects", "fact_text", "predicate", "object", "confidence"]
        return all(field in data and data[field] is not None for field in required)
    
    def _create_memory_unit(self, memory_data: Dict[str, Any], chapter_number: int) -> MemoryUnit:
        """Create a MemoryUnit from parsed LLM data"""
        # Validate required fields
        required_fields = ["mem_type", "subjects", "fact_text", "predicate", "object", "confidence"]
        for field in required_fields:
            if field not in memory_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults
        visibility = memory_data.get("visibility")
        if not visibility:
            visibility = self.defaults["visibility_defaults"].get(memory_data["mem_type"], "shared")
        
        # Create provenance
        provenance = Provenance(
            chapter=chapter_number,
            source="synopsis"
        )
        
        # Create memory unit
        memory = MemoryUnit(
            id=str(uuid.uuid4()),  # Generate unique ID
            mem_type=memory_data["mem_type"],
            subjects=memory_data["subjects"],
            fact_text=memory_data["fact_text"][:140],  # Ensure max length
            predicate=memory_data["predicate"],
            object=memory_data["object"],
            chapter_start=chapter_number,
            chapter_end=None,
            visibility=visibility,
            confidence=memory_data["confidence"],
            is_active=True,
            provenance=provenance,
            version=1,
            supersedes=None,
            embedding=None,
            attrs={"language": self.defaults["language"]}
        )
        
        return memory
    
    def validate_memory(self, memory: MemoryUnit) -> bool:
        """Validate memory against configuration"""
        # Check confidence threshold
        if memory.confidence < self.defaults["min_confidence"]:
            return False
        
        # Check memory type validity
        if memory.mem_type not in ["WM", "IC", "C2U"]:
            return False
        
        # Check subjects validity
        if memory.mem_type == "WM" and memory.subjects != ["world"]:
            return False
        elif memory.mem_type == "IC" and len(memory.subjects) != 2:
            return False
        elif memory.mem_type == "C2U" and len(memory.subjects) != 2 and "user_123" not in memory.subjects:
            return False
        
        # CRITICAL: Validate that all subjects exist in character registry
        valid_characters = set(self.entity_registry["character_aliases"].values())
        valid_characters.add(self.entity_registry["world_id"])
        valid_characters.add(self.entity_registry["user_id"])
        
        for subject in memory.subjects:
            if subject not in valid_characters:
                print(f"WARNING: Invalid subject '{subject}' in memory - not in character registry")
                return False
        
        # Check predicate exists in vocabulary
        if memory.predicate not in self.predicate_vocab:
            return False
        
        # Check object is valid for predicate
        predicate_config = self.predicate_vocab[memory.predicate]
        if memory.object not in predicate_config["object_enum"]:
            return False
        
        return True


class MockMemoryExtractor(MemoryExtractor):
    """Mock extractor for testing without LLM"""
    
    def __init__(self):
        super().__init__()
        self.client = None
    
    def extract_memories_from_sentence(self, sentence: str, chapter_number: int) -> Optional[MemoryUnit]:
        """Mock extraction for testing"""
        # Simple rule-based extraction for testing
        sentence_lower = sentence.lower()
        
        # Example rules for testing - handle the actual sentence patterns
        if "earring" in sentence_lower and "byleth" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["dedue", "byleth"],
                fact_text="Dedue found evidence of Byleth's affair at Dimitri's home (earring).",
                predicate="evidence",
                object="dedue_found_earring",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.9,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "virus" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="WM",
                subjects=["world"],
                fact_text="A company-wide memo warns about a novel virus.",
                predicate="alert",
                object="health_alert_circulated",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="global",
                confidence=0.8,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "affair" in sentence_lower and "dimitri" in sentence_lower and "byleth" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["dimitri", "byleth"],
                fact_text="Byleth and Dimitri started an affair.",
                predicate="relationship_status",
                object="started_affair",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.9,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "sylvain" in sentence_lower and "annette" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["sylvain", "annette"],
                fact_text="Sylvain and Annette have an established relationship.",
                predicate="relationship_status",
                object="reconciled",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.8,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        # Add more rules for Chapter 1 and other content
        elif "garreg mach" in sentence_lower and "first-day" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="WM",
                subjects=["world"],
                fact_text="Byleth steps into Garreg Mach Corp, the air buzzing with first-day energy",
                predicate="setting",
                object="garreg_mach_corp",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="global",
                confidence=0.95,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "byleth" in sentence_lower and "dimitri" in sentence_lower and "asset" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["byleth", "dimitri"],
                fact_text="Byleth notes Dimitri as a potential asset or obstacle in the games to come",
                predicate="first_meeting",
                object="noted_potential_asset",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.9,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "byleth" in sentence_lower and "sylvain" in sentence_lower and "asset" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["byleth", "sylvain"],
                fact_text="Byleth notes Sylvain as a potential asset or obstacle in the games to come",
                predicate="first_meeting",
                object="noted_potential_asset",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.9,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "intimacy" in sentence_lower and "sylvain" in sentence_lower and "annette" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["sylvain", "annette"],
                fact_text="Sylvain and Annette share an easy intimacy, their established relationship is clear",
                predicate="relationship_status",
                object="proprietary_display",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.9,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        elif "desk" in sentence_lower and "after hours" in sentence_lower:
            return MemoryUnit(
                id=str(uuid.uuid4()),
                mem_type="IC",
                subjects=["byleth", "dimitri"],
                fact_text="Byleth approaches Dimitri's desk after hours and weaves a plausible story about needing help with a task",
                predicate="manipulation",
                object="engineered_alibi_and_tryst",
                chapter_start=chapter_number,
                chapter_end=None,
                visibility="shared",
                confidence=0.95,
                is_active=True,
                provenance=Provenance(chapter=chapter_number, source="synopsis"),
                version=1,
                supersedes=None,
                embedding=None,
                attrs={"language": "en"}
            )
        
        return None
