"""Query types for musical transcription analysis.

This module defines Python equivalents of TypeScript query types to ensure
exact data structure compatibility between the web app and Python API.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Union, Literal, TypedDict
from enum import Enum
from dataclasses import dataclass

from .classes.trajectory import Trajectory
from .classes.pitch import Pitch


class CategoryType(str, Enum):
    """Query category types for different musical elements."""
    TRAJECTORY_ID = "trajectoryID"
    PITCH = "pitch"
    VOWEL = "vowel"
    STARTING_CONSONANT = "startingConsonant"
    ENDING_CONSONANT = "endingConsonant"
    ANY_CONSONANT = "anyConsonant"
    PITCH_SEQUENCE_STRICT = "pitchSequenceStrict"
    PITCH_SEQUENCE_LOOSE = "pitchSequenceLoose"
    TRAJ_SEQUENCE_STRICT = "trajSequenceStrict"
    TRAJ_SEQUENCE_LOOSE = "trajSequenceLoose"
    SECTION_TOP_LEVEL = "sectionTopLevel"
    ALAP_SECTION = "alapSection"
    COMP_TYPE = "compType"
    COMP_SEC_TEMPO = "compSecTempo"
    TALA = "tala"
    PHRASE_TYPE = "phraseType"
    ELABORATION_TYPE = "elaborationType"
    VOCAL_ART_TYPE = "vocalArtType"
    INST_ART_TYPE = "instArtType"
    INCIDENTAL = "incidental"


class DesignatorType(str, Enum):
    """Query designator types for matching behavior."""
    INCLUDES = "includes"
    EXCLUDES = "excludes"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"


class SegmentationType(str, Enum):
    """Query segmentation types for different analysis units."""
    PHRASE = "phrase"
    GROUP = "group"
    SEQUENCE_OF_TRAJECTORIES = "sequenceOfTrajectories"
    CONNECTED_SEQUENCE_OF_TRAJECTORIES = "connectedSequenceOfTrajectories"


# Section categorization types (matching TypeScript SecCatType)
class SecCatType(TypedDict, total=False):
    """Section categorization structure."""
    # Pre-Chiz Alap section
    pre_chiz_alap: Dict[str, bool]
    
    # Alap section types
    alap: Dict[str, bool]
    
    # Composition types
    composition_type: Dict[str, bool]
    
    # Tempo/section types
    comp_section_tempo: Dict[str, bool]
    
    # Tala types
    tala: Dict[str, bool]
    
    # Other categories
    improvisation: Dict[str, bool]
    other: Dict[str, bool]
    
    # Top level category
    top_level: Literal[
        "Pre-Chiz Alap", 
        "Alap", 
        "Composition", 
        "Improvisation", 
        "Other", 
        "None"
    ]


# Phrase categorization types (matching TypeScript PhraseCatType)
class PhraseCatType(TypedDict, total=False):
    """Phrase categorization structure."""
    phrase: Dict[str, bool]
    elaboration: Dict[str, bool]
    vocal_articulation: Dict[str, bool]
    instrumental_articulation: Dict[str, bool]
    incidental: Dict[str, bool]


class QueryType(TypedDict, total=False):
    """Single query specification."""
    category: CategoryType
    designator: DesignatorType
    pitch: Optional[Pitch]
    trajectory_id: Optional[int]
    vowel: Optional[str]
    consonant: Optional[str]
    pitch_sequence: Optional[List[Pitch]]
    traj_id_sequence: Optional[List[int]]
    section_top_level: Optional[str]
    alap_section: Optional[str]
    comp_type: Optional[str]
    comp_sec_tempo: Optional[str]
    tala: Optional[str]
    phrase_type: Optional[str]
    elaboration_type: Optional[str]
    vocal_art_type: Optional[str]
    inst_art_type: Optional[str]
    incidental: Optional[str]
    instrument_idx: int


@dataclass
class QueryAnswerType:
    """Result of a query execution."""
    trajectories: List[Trajectory]
    identifier: Union[int, str, Dict[str, int]]  # Can be phraseIdx or {phraseIdx, trajIdx}
    title: str
    start_time: float
    end_time: float
    duration: float
    segmentation: SegmentationType
    
    def to_json(self) -> Dict:
        """Convert to JSON-serializable dictionary with camelCase keys."""
        from .utils import to_camel_case
        return to_camel_case({
            "trajectories": [traj.to_json() for traj in self.trajectories],
            "identifier": self.identifier,
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "segmentation": self.segmentation.value if isinstance(self.segmentation, SegmentationType) else self.segmentation
        })
    
    @staticmethod
    def from_json(data: Dict) -> QueryAnswerType:
        """Create from JSON dictionary with camelCase keys."""
        from .utils import to_snake_case
        snake_data = to_snake_case(data)
        
        # Import here to avoid circular imports
        from .classes.trajectory import Trajectory
        
        trajectories = [Trajectory.from_json(t) for t in snake_data["trajectories"]]
        
        return QueryAnswerType(
            trajectories=trajectories,
            identifier=snake_data["identifier"],
            title=snake_data["title"],
            start_time=snake_data["start_time"],
            end_time=snake_data["end_time"],
            duration=snake_data["duration"],
            segmentation=SegmentationType(snake_data["segmentation"])
        )


# Type aliases for multi-query returns
MultipleReturnType = tuple[
    List[List[Trajectory]],  # trajectories
    List[Union[int, str, Dict[str, int]]],  # identifiers
    List[QueryAnswerType]  # query answers
]


class MultipleOptionType(TypedDict, total=False):
    """Options for multiple query execution."""
    transcription_id: Optional[str]
    piece: Optional[object]  # Will be Piece type, but avoiding circular import
    segmentation: SegmentationType
    sequence_length: Optional[int]
    min_dur: float
    max_dur: float
    every: bool  # True = all queries must match, False = any query can match
    instrument_idx: int


# Default categorization structures
def init_sec_categorization() -> SecCatType:
    """Initialize default section categorization structure."""
    return {
        "pre_chiz_alap": {"Pre-Chiz Alap": False},
        "alap": {
            "Alap": False,
            "Jor": False,
            "Alap-Jhala": False
        },
        "composition_type": {
            "Dhrupad": False,
            "Bandish": False,
            "Thumri": False,
            "Ghazal": False,
            "Qawwali": False,
            "Dhun": False,
            "Tappa": False,
            "Bhajan": False,
            "Kirtan": False,
            "Kriti": False,
            "Masitkhani Gat": False,
            "Razakhani Gat": False,
            "Ferozkhani Gat": False,
        },
        "comp_section_tempo": {
            "Ati Vilambit": False,
            "Vilambit": False,
            "Madhya": False,
            "Drut": False,
            "Ati Drut": False,
            "Jhala": False,
        },
        "tala": {
            "Ektal": False,
            "Tintal": False,
            "Rupak": False
        },
        "improvisation": {"Improvisation": False},
        "other": {"Other": False},
        "top_level": "None"
    }


def init_phrase_categorization() -> PhraseCatType:
    """Initialize default phrase categorization structure."""
    return {
        "phrase": {
            "Mohra": False,
            "Mukra": False,
            "Asthai": False,
            "Antara": False,
            "Manjha": False,
            "Abhog": False,
            "Sanchari": False,
            "Jhala": False
        },
        "elaboration": {
            "Vistar": False,
            "Barhat": False,
            "Prastar": False,
            "Bol Banao": False,
            "Bol Alap": False,
            "Bol Bandt": False,
            "Behlava": False,
            "Gat-kari": False,
            "Tan (Sapat)": False,
            "Tan (Gamak)": False,
            "Laykari": False,
            "Tihai": False,
            "Chakradar": False,
        },
        "vocal_articulation": {
            "Bol": False,
            "Non-Tom": False,
            "Tarana": False,
            "Aakar": False,
            "Sargam": False
        },
        "instrumental_articulation": {
            "Bol": False,
            "Non-Bol": False
        },
        "incidental": {
            "Talk/Conversation": False,
            "Praise ('Vah')": False,
            "Tuning": False,
            "Pause": False,
        }
    }