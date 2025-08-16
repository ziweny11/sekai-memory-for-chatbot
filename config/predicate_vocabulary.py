import json
import os
from typing import Dict, Any


def load_predicate_vocabulary() -> Dict[str, Any]:
    """Load predicate vocabulary configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "predicate_vocabulary.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading predicate vocabulary: {e}")
        # Return default vocabulary
        return {
            "relationship_status": {
                "type": "IC",
                "object_enum": [
                    "started_affair", "affair_acknowledged", "jealous", "suspicious",
                    "reconciled", "proprietary_display", "mentor_mask", "confrontation",
                    "deception", "manipulation", "betrayal_discovered"
                ]
            },
            "secrecy_pact": { 
                "type": "IC", 
                "object_enum": ["true", "false"] 
            },
            "contact": { 
                "type": "IC", 
                "object_enum": ["exchanged_numbers", "private_meeting", "hotel_rendezvous"] 
            },
            "evidence": { 
                "type": "IC", 
                "object_enum": ["dedue_found_earring", "public_display", "witnessed_betrayal"] 
            },
            "manipulation": { 
                "type": "IC", 
                "object_enum": ["engineered_alibi_and_tryst", "sabotaged_plans", "created_conflict"] 
            },
            "alert": { 
                "type": "WM", 
                "object_enum": ["health_alert_circulated", "virus_warning", "company_memo"] 
            },
            "world_discussion": { 
                "type": "WM", 
                "object_enum": ["office_dismissive_attitude", "virus_fearmongering", "distant_threat"] 
            },
            "office_dynamics": {
                "type": "WM",
                "object_enum": ["first_day_energy", "professional_boundaries", "workplace_entanglements"]
            }
        }
