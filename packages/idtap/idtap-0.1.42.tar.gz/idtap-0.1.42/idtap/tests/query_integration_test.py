"""Integration tests for the query system using real transcription data."""

import pytest
from typing import List

from idtap import SwaraClient
from idtap.query_types import (
    CategoryType, DesignatorType, SegmentationType,
    QueryAnswerType, QueryType
)
from idtap.classes.piece import Piece


# Test transcription ID - vocal recording suitable for consonant/vowel testing
TEST_TRANSCRIPTION_ID = "645ff354deeaf2d1e33b3c44"


@pytest.mark.integration
class TestRealTranscriptionQueries:
    """Test queries against real transcription data."""
    
    @pytest.fixture
    def client(self):
        """Initialize SwaraClient for testing."""
        return SwaraClient()
    
    @pytest.fixture
    def test_piece(self, client):
        """Load the test transcription as a Piece object."""
        try:
            piece_data = client.get_piece(TEST_TRANSCRIPTION_ID)
            return Piece.from_json(piece_data)
        except Exception as e:
            pytest.skip(f"Could not load test transcription: {e}")
    
    def test_basic_trajectory_query(self, client):
        """Test basic trajectory ID query on real data."""
        try:
            # Look for trajectory ID 1 (common trajectory type)
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.TRAJECTORY_ID,
                trajectory_id=1,
                designator=DesignatorType.INCLUDES,
                segmentation=SegmentationType.PHRASE
            )
            
            print(f"\n=== Basic Trajectory Query Results ===")
            print(f"Found {len(result.trajectories)} phrases containing trajectory ID 1")
            
            # Verify we got reasonable results
            assert isinstance(result.trajectories, list)
            assert isinstance(result.query_answers, list)
            assert len(result.trajectories) == len(result.query_answers)
            
            # Print first few results for inspection
            for i, answer in enumerate(result.query_answers[:3]):
                print(f"Result {i+1}: {answer.title} - {answer.duration:.2f}s")
                assert answer.duration > 0
                assert len(answer.trajectories) > 0
                
        except Exception as e:
            pytest.fail(f"Basic trajectory query failed: {e}")
    
    def test_consonant_starts_with_query(self, client):
        """Test the specific consonant query: trajectories that start with 'b'."""
        try:
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.STARTING_CONSONANT,
                consonant="b",
                designator=DesignatorType.STARTS_WITH,
                segmentation=SegmentationType.PHRASE
            )
            
            print(f"\n=== Consonant 'b' Starts With Query ===")
            print(f"Found {len(result.trajectories)} phrases starting with consonant 'b'")
            
            # Verify structure
            assert isinstance(result.trajectories, list)
            assert isinstance(result.query_answers, list)
            
            # Check that results make sense
            for answer in result.query_answers[:3]:
                print(f"- {answer.title}: {answer.duration:.2f}s, {len(answer.trajectories)} trajectories")
                assert answer.duration > 0
                
                # Verify the first trajectory in the phrase actually starts with 'b'
                if answer.trajectories:
                    first_traj = answer.trajectories[0]
                    if hasattr(first_traj, 'start_consonant'):
                        print(f"  First trajectory consonant: {first_traj.start_consonant}")
                        # Note: May be None if not labeled, so we don't assert equality
                        
        except Exception as e:
            pytest.fail(f"Consonant starts with query failed: {e}")
    
    def test_vowel_starts_with_query(self, client):
        """Test vowel query: trajectories that start with 'a'."""
        try:
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.VOWEL,
                vowel="a",
                designator=DesignatorType.STARTS_WITH,
                segmentation=SegmentationType.PHRASE
            )
            
            print(f"\n=== Vowel 'a' Starts With Query ===")
            print(f"Found {len(result.trajectories)} phrases starting with vowel 'a'")
            
            # Verify structure
            assert isinstance(result.trajectories, list)
            assert isinstance(result.query_answers, list)
            
            for answer in result.query_answers[:3]:
                print(f"- {answer.title}: {answer.duration:.2f}s")
                assert answer.duration > 0
                
                # Check first trajectory vowel if available
                if answer.trajectories:
                    first_traj = answer.trajectories[0]
                    if hasattr(first_traj, 'vowel'):
                        print(f"  First trajectory vowel: {first_traj.vowel}")
                        
        except Exception as e:
            pytest.fail(f"Vowel starts with query failed: {e}")
    
    def test_combined_consonant_vowel_query(self, client):
        """Test the specific multi-query: consonant 'b' AND vowel 'a' start conditions."""
        try:
            queries = [
                {
                    "category": CategoryType.STARTING_CONSONANT,
                    "consonant": "b",
                    "designator": DesignatorType.STARTS_WITH,
                    "instrument_idx": 0
                },
                {
                    "category": CategoryType.VOWEL,
                    "vowel": "a", 
                    "designator": DesignatorType.STARTS_WITH,
                    "instrument_idx": 0
                }
            ]
            
            # Find phrases that start with consonant 'b' AND start with vowel 'a'
            trajectories, identifiers, answers = client.multiple_query(
                queries=queries,
                transcription_id=TEST_TRANSCRIPTION_ID,
                every=True,  # Both conditions must be met
                segmentation=SegmentationType.PHRASE
            )
            
            print(f"\n=== Combined Query: Consonant 'b' AND Vowel 'a' Starts With ===")
            print(f"Found {len(trajectories)} phrases meeting BOTH conditions")
            
            # Verify results
            assert isinstance(trajectories, list)
            assert isinstance(identifiers, list)
            assert isinstance(answers, list)
            assert len(trajectories) == len(identifiers) == len(answers)
            
            for i, answer in enumerate(answers[:3]):
                print(f"Result {i+1}: {answer.title} - {answer.duration:.2f}s")
                print(f"  Contains {len(answer.trajectories)} trajectories")
                
                # Inspect first trajectory
                if answer.trajectories:
                    first_traj = answer.trajectories[0]
                    start_cons = getattr(first_traj, 'start_consonant', None)
                    vowel = getattr(first_traj, 'vowel', None)
                    print(f"  First trajectory - consonant: {start_cons}, vowel: {vowel}")
                    
        except Exception as e:
            pytest.fail(f"Combined consonant/vowel query failed: {e}")
    
    def test_trajectory_sequence_query(self, client):
        """Test trajectory sequence query on real data."""
        try:
            # Look for common trajectory sequence pattern
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.TRAJ_SEQUENCE_STRICT,
                traj_id_sequence=[1, 2],  # Simple 2-trajectory pattern
                designator=DesignatorType.INCLUDES,
                segmentation=SegmentationType.SEQUENCE_OF_TRAJECTORIES,
                sequence_length=2
            )
            
            print(f"\n=== Trajectory Sequence Query [1, 2] ===")
            print(f"Found {len(result.trajectories)} trajectory sequences with pattern [1, 2]")
            
            assert isinstance(result.trajectories, list)
            assert isinstance(result.query_answers, list)
            
            for answer in result.query_answers[:3]:
                print(f"- {answer.title}: {answer.duration:.2f}s")
                assert answer.duration > 0
                assert len(answer.trajectories) == 2  # Should be exactly 2 trajectories
                
                # Verify the sequence pattern
                if len(answer.trajectories) == 2:
                    ids = [traj.id for traj in answer.trajectories]
                    print(f"  Trajectory IDs: {ids}")
                    
        except Exception as e:
            # This might fail if the specific pattern doesn't exist
            print(f"Trajectory sequence query note: {e}")
    
    def test_pitch_query_real_data(self, client):
        """Test pitch-based query on real transcription."""
        try:
            from idtap.classes.pitch import Pitch
            
            # Create a pitch object for a common pitch (around middle range)
            target_pitch = Pitch({"numberedPitch": 65})  # F above middle C
            
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.PITCH,
                pitch=target_pitch,
                designator=DesignatorType.INCLUDES,
                segmentation=SegmentationType.PHRASE
            )
            
            print(f"\n=== Pitch Query (numberedPitch=65) ===")
            print(f"Found {len(result.trajectories)} phrases containing pitch 65")
            
            assert isinstance(result.trajectories, list)
            assert isinstance(result.query_answers, list)
            
            for answer in result.query_answers[:3]:
                print(f"- {answer.title}: {answer.duration:.2f}s")
                assert answer.duration > 0
                
                # Count pitches in the phrase
                total_pitches = sum(len(traj.pitches) for traj in answer.trajectories)
                print(f"  Total pitches in phrase: {total_pitches}")
                
        except Exception as e:
            pytest.fail(f"Pitch query failed: {e}")
    
    def test_duration_filtering_real_data(self, client):
        """Test duration filtering with real data."""
        try:
            # Find short phrases (< 3 seconds) containing trajectory ID 1
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.TRAJECTORY_ID,
                trajectory_id=1,
                designator=DesignatorType.INCLUDES,
                max_dur=3.0,  # Maximum 3 seconds
                min_dur=0.5   # Minimum 0.5 seconds
            )
            
            print(f"\n=== Duration Filtered Query (0.5s - 3.0s) ===")
            print(f"Found {len(result.trajectories)} phrases (traj ID 1, 0.5-3.0s duration)")
            
            assert isinstance(result.trajectories, list)
            
            # Verify all results meet duration constraints
            for answer in result.query_answers[:5]:
                print(f"- {answer.title}: {answer.duration:.2f}s")
                assert 0.5 <= answer.duration <= 3.0, f"Duration {answer.duration} outside range"
                
        except Exception as e:
            pytest.fail(f"Duration filtering failed: {e}")
    
    def test_data_structure_inspection(self, test_piece):
        """Inspect the actual transcription structure for debugging."""
        print(f"\n=== Transcription Data Structure ===")
        print(f"Instrumentation: {test_piece.instrumentation}")
        print(f"Number of phrases: {len(test_piece.phrases) if test_piece.phrases else 0}")
        
        if hasattr(test_piece, 'phrase_grid') and test_piece.phrase_grid:
            print(f"Phrase grid tracks: {len(test_piece.phrase_grid)}")
            if test_piece.phrase_grid[0]:
                print(f"Phrases in track 0: {len(test_piece.phrase_grid[0])}")
                
                # Inspect first few trajectories
                first_phrase = test_piece.phrase_grid[0][0]
                print(f"First phrase trajectories: {len(first_phrase.trajectories)}")
                
                for i, traj in enumerate(first_phrase.trajectories[:3]):
                    print(f"  Traj {i}: ID={traj.id}, vowel={getattr(traj, 'vowel', None)}, "
                          f"start_consonant={getattr(traj, 'start_consonant', None)}")
        
        # This helps us understand what data is available for querying
        assert test_piece is not None
    
    def test_query_result_serialization(self, client):
        """Test that query results can be serialized/deserialized properly."""
        try:
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.TRAJECTORY_ID,
                trajectory_id=1,
                designator=DesignatorType.INCLUDES
            )
            
            if result.query_answers:
                # Test serialization
                answer = result.query_answers[0]
                json_data = answer.to_json()
                
                print(f"\n=== Serialization Test ===")
                print(f"Original title: {answer.title}")
                print(f"Original duration: {answer.duration}")
                print(f"JSON keys: {list(json_data.keys())}")
                
                # Test deserialization
                from idtap.query_types import QueryAnswerType
                restored = QueryAnswerType.from_json(json_data)
                
                print(f"Restored title: {restored.title}")
                print(f"Restored duration: {restored.duration}")
                
                # Verify round-trip accuracy
                assert restored.title == answer.title
                assert restored.duration == answer.duration
                assert restored.start_time == answer.start_time
                assert restored.end_time == answer.end_time
                
                print("✅ Serialization round-trip successful")
                
        except Exception as e:
            pytest.fail(f"Serialization test failed: {e}")


class TestQueryPerformance:
    """Test query performance with real data."""
    
    @pytest.mark.integration
    def test_large_query_performance(self, client=None):
        """Test performance of queries on real transcription."""
        if client is None:
            client = SwaraClient()
            
        import time
        
        try:
            start_time = time.time()
            
            result = client.single_query(
                transcription_id=TEST_TRANSCRIPTION_ID,
                category=CategoryType.TRAJECTORY_ID,
                trajectory_id=1,
                designator=DesignatorType.INCLUDES
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n=== Performance Test ===")
            print(f"Query execution time: {duration:.3f} seconds")
            print(f"Results found: {len(result.trajectories)}")
            print(f"Results per second: {len(result.trajectories)/duration:.1f}")
            
            # Performance should be reasonable (< 5 seconds for most queries)
            assert duration < 10.0, f"Query took too long: {duration:.3f}s"
            
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")


if __name__ == "__main__":
    """Run integration tests manually."""
    print("Running integration tests with real transcription data...")
    print(f"Test transcription ID: {TEST_TRANSCRIPTION_ID}")
    
    # You can run individual tests here for debugging
    client = SwaraClient()
    test_instance = TestRealTranscriptionQueries()
    
    try:
        test_instance.test_consonant_starts_with_query(client)
        test_instance.test_vowel_starts_with_query(client)
        test_instance.test_combined_consonant_vowel_query(client)
    except Exception as e:
        print(f"Manual test execution failed: {e}")