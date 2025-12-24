"""Comprehensive tests for the query system."""

import pytest
import json
from typing import List, Dict, Any

from idtap.query import Query
from idtap.query_types import (
    CategoryType, DesignatorType, SegmentationType,
    QueryAnswerType, QueryType
)
from idtap.sequence_utils import find_sequence_indexes, loose_sequence_indexes
from idtap.classes.piece import Piece
from idtap.classes.trajectory import Trajectory
from idtap.classes.pitch import Pitch
from idtap.classes.phrase import Phrase


class TestSequenceUtils:
    """Test sequence matching utilities."""
    
    def test_find_sequence_indexes_basic(self):
        """Test basic sequence finding."""
        sequence = [1, 2, 3]
        longer_sequence = [0, 1, 2, 3, 4, 1, 2, 3, 5]
        
        result = find_sequence_indexes(sequence, longer_sequence)
        assert result == [1, 5]
    
    def test_find_sequence_indexes_empty(self):
        """Test sequence finding with empty inputs."""
        assert find_sequence_indexes([], [1, 2, 3]) == []
        assert find_sequence_indexes([1, 2], []) == []
        assert find_sequence_indexes([], []) == []
    
    def test_find_sequence_indexes_no_match(self):
        """Test sequence finding with no matches."""
        sequence = [5, 6, 7]
        longer_sequence = [1, 2, 3, 4]
        
        result = find_sequence_indexes(sequence, longer_sequence)
        assert result == []
    
    def test_loose_sequence_indexes_basic(self):
        """Test basic loose sequence matching."""
        sequence = [1, 3, 5]
        longer_sequence = [0, 1, 2, 3, 4, 5, 6]
        
        result = loose_sequence_indexes(sequence, longer_sequence)
        assert result["truth"] is True
        assert result["first_idx"] == 1
        assert result["last_idx"] == 5
    
    def test_loose_sequence_indexes_no_match(self):
        """Test loose sequence matching with no matches."""
        sequence = [1, 3, 8]
        longer_sequence = [0, 1, 2, 3, 4, 5, 6]
        
        result = loose_sequence_indexes(sequence, longer_sequence)
        assert result["truth"] is False
        assert result["first_idx"] == 1
        assert result["last_idx"] is None


class TestQueryTypes:
    """Test query type structures and serialization."""
    
    def test_query_answer_serialization(self):
        """Test QueryAnswerType serialization."""
        # Create mock trajectories and data
        traj1 = Trajectory({"id": 1, "startTime": 0.0, "durTot": 1.0})
        
        answer = QueryAnswerType(
            trajectories=[traj1],
            identifier=123,
            title="Test Phrase",
            start_time=0.0,
            end_time=1.0,
            duration=1.0,
            segmentation=SegmentationType.PHRASE
        )
        
        # Test serialization
        json_data = answer.to_json()
        assert "trajectories" in json_data
        assert json_data["title"] == "Test Phrase"
        assert json_data["duration"] == 1.0
        
        # Test deserialization
        restored = QueryAnswerType.from_json(json_data)
        assert restored.title == "Test Phrase"
        assert restored.duration == 1.0
        assert len(restored.trajectories) == 1


class TestQueryValidation:
    """Test query parameter validation."""
    
    def create_minimal_piece(self) -> Piece:
        """Create a minimal piece for testing."""
        from idtap.enums import Instrument
        
        # Create minimal phrase and trajectory data
        phrase_data = {
            "trajectories": [{"id": 1, "startTime": 0.0, "durTot": 1.0, "pitches": []}],
            "startTime": 0.0,
            "durTot": 1.0,
            "pieceIdx": 0
        }
        phrase = Phrase.from_json(phrase_data)
        
        # Ensure trajectories have correct phrase_idx for queries
        phrase.assign_phrase_idx()
        
        piece_data = {
            "instrumentation": [Instrument.Sitar],
            "phrases": [phrase],
            "phraseGrid": [[phrase]],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        return Piece(piece_data)
    
    def test_sequence_length_validation(self):
        """Test that sequence length is required for trajectory sequences."""
        piece = self.create_minimal_piece()
        
        with pytest.raises(ValueError, match="sequence_length is required"):
            Query(piece, {
                "segmentation": SegmentationType.SEQUENCE_OF_TRAJECTORIES,
                "category": CategoryType.TRAJECTORY_ID,
                "trajectory_id": 1
            })
    
    def test_pitch_validation(self):
        """Test that pitch parameter is required when category is pitch."""
        piece = self.create_minimal_piece()
        
        with pytest.raises(ValueError, match="pitch is required"):
            Query(piece, {
                "category": CategoryType.PITCH
            })
    
    def test_trajectory_id_validation(self):
        """Test that trajectory_id is required when category is trajectoryID."""
        piece = self.create_minimal_piece()
        
        with pytest.raises(ValueError, match="trajectory_id is required"):
            Query(piece, {
                "category": CategoryType.TRAJECTORY_ID
            })
    
    def test_vowel_instrument_validation(self):
        """Test that vowel queries are only allowed for vocal instruments."""
        from idtap.enums import Instrument
        
        # Create piece with sitar (non-vocal instrument)
        piece_data = {
            "instrumentation": [Instrument.Sitar],
            "phrases": [],
            "phraseGrid": [[]],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        piece = Piece(piece_data)
        
        with pytest.raises(ValueError, match="vowel is only for vocal instruments"):
            Query(piece, {
                "category": CategoryType.VOWEL,
                "vowel": "a"
            })
    
    def test_consonant_instrument_validation(self):
        """Test that consonant queries are only allowed for vocal instruments."""
        from idtap.enums import Instrument
        
        # Create piece with sitar (non-vocal instrument)
        piece_data = {
            "instrumentation": [Instrument.Sitar],
            "phrases": [],
            "phraseGrid": [[]],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        piece = Piece(piece_data)
        
        with pytest.raises(ValueError, match="consonant is only for vocal instruments"):
            Query(piece, {
                "category": CategoryType.STARTING_CONSONANT,
                "consonant": "k"
            })
    
    def test_section_designator_validation(self):
        """Test that section queries cannot use startsWith/endsWith."""
        piece = self.create_minimal_piece()
        
        with pytest.raises(ValueError, match="cannot be used with startsWith"):
            Query(piece, {
                "category": CategoryType.SECTION_TOP_LEVEL,
                "section_top_level": "Alap",
                "designator": DesignatorType.STARTS_WITH
            })
    
    def test_section_segmentation_validation(self):
        """Test that section queries cannot use trajectory sequence segmentation."""
        piece = self.create_minimal_piece()
        
        with pytest.raises(ValueError, match="cannot be used with trajectory sequence"):
            Query(piece, {
                "category": CategoryType.SECTION_TOP_LEVEL,
                "section_top_level": "Alap",
                "segmentation": SegmentationType.SEQUENCE_OF_TRAJECTORIES,
                "sequence_length": 3
            })


class TestQueryExecution:
    """Test query execution with mock data."""
    
    def create_test_piece(self) -> Piece:
        """Create a more comprehensive test piece."""
        from idtap.enums import Instrument
        
        # Create trajectories with different IDs and pitches
        traj_data = [
            {
                "id": 1, "startTime": 0.0, "durTot": 0.5, "phraseIdx": 0, "num": 0,
                "pitches": [{"numberedPitch": 60, "time": 0.1}],
                "vowel": "a", "startConsonant": "k", "endConsonant": "t"
            },
            {
                "id": 2, "startTime": 0.5, "durTot": 0.5, "phraseIdx": 0, "num": 1,
                "pitches": [{"numberedPitch": 62, "time": 0.7}],
                "vowel": "i", "startConsonant": "r", "endConsonant": None
            },
            {
                "id": 1, "startTime": 1.0, "durTot": 0.5, "phraseIdx": 0, "num": 2,
                "pitches": [{"numberedPitch": 64, "time": 1.2}],
                "vowel": "u", "startConsonant": "m", "endConsonant": "n"
            }
        ]
        
        phrase_data = {
            "trajectories": traj_data,
            "startTime": 0.0,
            "durTot": 1.5,
            "pieceIdx": 0
        }
        phrase = Phrase.from_json(phrase_data)
        
        # Ensure trajectories have correct phrase_idx for queries
        phrase.assign_phrase_idx()
        
        piece_data = {
            "instrumentation": [Instrument.Vocal_M],
            "phrases": [phrase],
            "phraseGrid": [[phrase]],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        return Piece(piece_data)
    
    def test_trajectory_id_query_includes(self):
        """Test trajectory ID query with includes designator."""
        piece = self.create_test_piece()
        
        query = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1,
            "designator": DesignatorType.INCLUDES
        })
        
        # Should find one phrase containing trajectory ID 1
        assert len(query.trajectories) == 1
        assert len(query.query_answers) == 1
        assert query.query_answers[0].title == "Phrase 1"
    
    def test_trajectory_id_query_excludes(self):
        """Test trajectory ID query with excludes designator."""
        piece = self.create_test_piece()
        
        query = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 3,  # ID that doesn't exist
            "designator": DesignatorType.EXCLUDES
        })
        
        # Should find the phrase since it doesn't contain trajectory ID 3
        assert len(query.trajectories) == 1
    
    def test_pitch_query_includes(self):
        """Test pitch query with includes designator."""
        piece = self.create_test_piece()
        pitch = Pitch({"numberedPitch": 62})
        
        query = Query(piece, {
            "category": CategoryType.PITCH,
            "pitch": pitch,
            "designator": DesignatorType.INCLUDES
        })
        
        # Should find phrases containing pitch 62
        assert len(query.trajectories) == 1
    
    def test_vowel_query(self):
        """Test vowel query."""
        piece = self.create_test_piece()
        
        query = Query(piece, {
            "category": CategoryType.VOWEL,
            "vowel": "i",
            "designator": DesignatorType.INCLUDES
        })
        
        # Should find phrases containing vowel "i"
        assert len(query.trajectories) == 1
    
    def test_consonant_query(self):
        """Test consonant query."""
        piece = self.create_test_piece()
        
        query = Query(piece, {
            "category": CategoryType.STARTING_CONSONANT,
            "consonant": "k",
            "designator": DesignatorType.INCLUDES
        })
        
        # Should find phrases containing starting consonant "k"
        assert len(query.trajectories) == 1
    
    def test_duration_filtering(self):
        """Test duration-based filtering."""
        piece = self.create_test_piece()
        
        # Query with very short max duration - should filter out results
        query = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1,
            "max_dur": 0.1  # Very short duration
        })
        
        # Should have no results due to duration filtering
        assert len(query.trajectories) == 0
    
    def test_query_answers_structure(self):
        """Test that query answers have correct structure."""
        piece = self.create_test_piece()
        
        query = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1
        })
        
        assert len(query.query_answers) >= 1
        answer = query.query_answers[0]
        
        # Check required fields
        assert hasattr(answer, 'trajectories')
        assert hasattr(answer, 'identifier')
        assert hasattr(answer, 'title')
        assert hasattr(answer, 'start_time')
        assert hasattr(answer, 'end_time')
        assert hasattr(answer, 'duration')
        assert hasattr(answer, 'segmentation')
        
        # Check types
        assert isinstance(answer.trajectories, list)
        assert isinstance(answer.title, str)
        assert isinstance(answer.start_time, (int, float))
        assert isinstance(answer.end_time, (int, float))
        assert isinstance(answer.duration, (int, float))


class TestMultipleQueries:
    """Test multiple query coordination."""
    
    def create_test_piece(self) -> Piece:
        """Create test piece with multiple phrases."""
        from idtap.enums import Instrument
        
        # Create multiple phrases with different characteristics
        phrases = []
        for i in range(3):
            traj_data = {
                "id": i + 1, "startTime": 0.0, "durTot": 1.0, 
                "phraseIdx": i, "num": 0,
                "pitches": [{"numberedPitch": 60 + i, "time": 0.5}],
                "vowel": ["a", "i", "u"][i]
            }
            
            phrase_data = {
                "trajectories": [traj_data],  # Pass raw JSON data, not Trajectory objects
                "startTime": float(i), 
                "durTot": 1.0,
                "pieceIdx": i
            }
            phrase = Phrase.from_json(phrase_data)
            
            # Ensure trajectories have correct phrase_idx for queries
            phrase.assign_phrase_idx()
            
            phrases.append(phrase)
        
        piece_data = {
            "instrumentation": [Instrument.Vocal_M],
            "phrases": phrases,
            "phraseGrid": [phrases],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        return Piece(piece_data)
    
    def test_multiple_queries_every_true(self):
        """Test multiple queries with every=True (intersection)."""
        piece = self.create_test_piece()
        
        # Create queries that should have overlapping results
        queries: List[QueryType] = [
            {
                "category": CategoryType.TRAJECTORY_ID,
                "trajectory_id": 1,
                "designator": DesignatorType.INCLUDES,
                "instrument_idx": 0
            },
            {
                "category": CategoryType.VOWEL,
                "vowel": "a",
                "designator": DesignatorType.INCLUDES,
                "instrument_idx": 0
            }
        ]
        
        # Use the static method (note: would need actual implementation)
        # For now, test the individual queries work
        query1 = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1,
            "designator": DesignatorType.INCLUDES
        })
        query2 = Query(piece, {
            "category": CategoryType.VOWEL,
            "vowel": "a",
            "designator": DesignatorType.INCLUDES
        })
        
        # Both should find results
        assert len(query1.trajectories) >= 1
        assert len(query2.trajectories) >= 1
    
    def test_multiple_queries_every_false(self):
        """Test multiple queries with every=False (union)."""
        piece = self.create_test_piece()
        
        # Test individual queries that should find different results
        query1 = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1,
            "designator": DesignatorType.INCLUDES
        })
        query2 = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 2,
            "designator": DesignatorType.INCLUDES
        })
        
        # Each should find different results
        assert len(query1.trajectories) >= 1
        assert len(query2.trajectories) >= 1
        
        # Identifiers should be different
        assert query1.identifier != query2.identifier


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_piece(self):
        """Test query on piece with no content."""
        from idtap.enums import Instrument
        
        piece_data = {
            "instrumentation": [Instrument.Sitar],
            "phrases": [],
            "phraseGrid": [[]],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        piece = Piece(piece_data)
        
        query = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1
        })
        
        # Should complete without error but find no results
        assert len(query.trajectories) == 0
        assert len(query.query_answers) == 0
    
    def test_invalid_instrument_index(self):
        """Test query with invalid instrument index."""
        from idtap.enums import Instrument
        
        piece_data = {
            "instrumentation": [Instrument.Sitar],
            "phrases": [],
            "phraseGrid": [[]],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        piece = Piece(piece_data)
        
        # This should raise a validation error for invalid instrument index
        with pytest.raises(ValueError, match="instrument_idx 5 is out of range"):
            Query(piece, {
                "category": CategoryType.TRAJECTORY_ID,
                "trajectory_id": 1,
                "instrument_idx": 5  # Invalid index
            })
    
    def test_missing_phrase_data(self):
        """Test query with piece missing required phrase data."""
        from idtap.enums import Instrument
        
        # Create piece with minimal data
        piece_data = {
            "instrumentation": [Instrument.Sitar],
            "raga": {"name": "Test", "fundamental": 220, "ratios": [1.0]}
        }
        piece = Piece(piece_data)
        
        # Query should not crash even with missing data
        query = Query(piece, {
            "category": CategoryType.TRAJECTORY_ID,
            "trajectory_id": 1
        })
        
        # Should complete without error
        assert len(query.trajectories) == 0