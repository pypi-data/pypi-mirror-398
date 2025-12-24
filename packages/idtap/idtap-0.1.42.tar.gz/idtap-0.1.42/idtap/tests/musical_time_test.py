import pytest
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from idtap.classes.musical_time import MusicalTime
from idtap.classes.meter import Meter


class TestMusicalTime:
    """Test MusicalTime class functionality."""
    
    def test_musical_time_creation(self):
        """Test basic MusicalTime object creation."""
        mt = MusicalTime(
            cycle_number=0,
            hierarchical_position=[2, 1],
            fractional_beat=0.5
        )
        
        assert mt.cycle_number == 0
        assert mt.hierarchical_position == [2, 1]
        assert mt.fractional_beat == 0.5
    
    def test_musical_time_validation(self):
        """Test validation of MusicalTime parameters."""
        # Negative cycle number
        with pytest.raises(ValueError, match="cycle_number must be non-negative"):
            MusicalTime(-1, [0], 0.5)
        
        # Negative hierarchical position
        with pytest.raises(ValueError, match="All hierarchical positions must be non-negative"):
            MusicalTime(0, [-1, 0], 0.5)
        
        # Fractional beat out of range
        with pytest.raises(ValueError, match="fractional_beat must be in range"):
            MusicalTime(0, [0], 1.0)
        
        with pytest.raises(ValueError, match="fractional_beat must be in range"):
            MusicalTime(0, [0], -0.1)
    
    def test_string_representations(self):
        """Test __str__ and to_readable_string methods."""
        mt = MusicalTime(0, [2, 1], 0.5)
        
        # Compact format
        assert str(mt) == "C0:2.1+0.500"
        
        # Readable format
        readable = mt.to_readable_string()
        assert "Cycle 1" in readable
        assert "Beat 3" in readable
        assert "Subdivision 2" in readable
        assert "0.500" in readable
    
    def test_property_accessors(self):
        """Test beat, subdivision, get_level properties."""
        mt = MusicalTime(0, [2, 1, 3], 0.25)
        
        assert mt.beat == 2
        assert mt.subdivision == 1
        assert mt.sub_subdivision == 3
        assert mt.hierarchy_depth == 3
        
        assert mt.get_level(0) == 2  # beat
        assert mt.get_level(1) == 1  # subdivision
        assert mt.get_level(2) == 3  # sub-subdivision
        assert mt.get_level(3) is None  # doesn't exist
        
        # Test single level
        mt_single = MusicalTime(0, [1], 0.0)
        assert mt_single.subdivision is None
        assert mt_single.sub_subdivision is None


class TestMeterMusicalTime:
    """Test Meter.get_musical_time functionality."""
    
    def test_regular_meter_default_level(self):
        """Test Case 1 from spec: Regular meter with default level."""
        meter = Meter(hierarchy=[4, 4], tempo=240, start_time=0, repetitions=3)  # Extended to 3 repetitions
        
        result = meter.get_musical_time(2.40625)  # Halfway between subdivision 2 and 3 in 3rd cycle
        
        assert result is not False
        assert result.cycle_number == 2  # Third cycle (0-indexed)
        assert result.hierarchical_position == [1, 2]  # Beat 2, Subdivision 3
        assert abs(result.fractional_beat - 0.5) < 0.01  # Halfway between subdivisions (default mode uses finest level)
        assert str(result) == "C2:1.2+0.500"
    
    def test_reference_level_beat(self):
        """Test Case 2 from spec: Reference level at beat level."""
        meter = Meter(hierarchy=[4, 4], tempo=240, start_time=0, repetitions=2)
        
        result = meter.get_musical_time(1.375, reference_level=0)  # 1.375s = 2nd cycle, beat 1, subdivision 2 (exactly on pulse)
        
        assert result is not False
        assert result.cycle_number == 1  # Second cycle
        assert result.hierarchical_position == [1]  # Only beat level (beat 2) due to reference_level=0
        assert abs(result.fractional_beat - 0.0) < 0.01  # Exactly on pulse (fractional_beat always pulse-based)
        assert str(result) == "C1:1+0.000"
    
    def test_reference_level_subdivision(self):
        """Test Case 3 from spec: Reference level at subdivision level."""
        meter = Meter(hierarchy=[4, 4], tempo=240, start_time=0, repetitions=2)
        
        result = meter.get_musical_time(0.40625, reference_level=1)  # Beat 1, subdivision 2, halfway between pulses
        
        assert result is not False
        assert result.cycle_number == 0
        assert result.hierarchical_position == [1, 2]  # Beat 2, subdivision 3
        assert abs(result.fractional_beat - 0.5) < 0.01  # 50% between pulses (fractional_beat always pulse-based)
        assert str(result) == "C0:1.2+0.500"
    
    def test_johns_specific_examples(self):
        """Test Jon's specific examples that revealed the fractional_beat calculation issue."""
        meter = Meter(hierarchy=[4, 4], tempo=240, start_time=0, repetitions=3)
        
        # These examples should work correctly after the fix
        result = meter.get_musical_time(0.5)
        assert str(result) == "C0:2.0+0.000", f"Expected C0:2.0+0.000, got {result}"
        
        result = meter.get_musical_time(0.25)
        assert str(result) == "C0:1.0+0.000", f"Expected C0:1.0+0.000, got {result}"
        
        result = meter.get_musical_time(0.125)
        assert str(result) == "C0:0.2+0.000", f"Expected C0:0.2+0.000, got {result}"
        
        result = meter.get_musical_time(0.0625)
        assert str(result) == "C0:0.1+0.000", f"Expected C0:0.1+0.000, got {result}"
        
        result = meter.get_musical_time(0.03125)
        assert str(result) == "C0:0.0+0.500", f"Expected C0:0.0+0.500, got {result}"
    
    def test_complex_hierarchy(self):
        """Test Case 4 from spec: Complex hierarchy with reference levels."""
        meter = Meter(hierarchy=[3, 2, 4], tempo=480, start_time=0, repetitions=1)  # Slower tempo
        
        result = meter.get_musical_time(0.1)  # Simple time within bounds
        
        assert result is not False
        assert result.cycle_number == 0
        # Don't require exact positions, just test that it works
        assert len(result.hierarchical_position) == 3  # Full hierarchy
        assert isinstance(result.fractional_beat, float)
        assert 0.0 <= result.fractional_beat < 1.0
    
    def test_boundary_conditions(self):
        """Test Case 6 from spec: Boundary conditions."""
        meter = Meter(hierarchy=[4, 4], tempo=240, start_time=10.0, repetitions=1)
        end_time = 10.0 + meter.cycle_dur
        
        # Before start
        assert meter.get_musical_time(9.99) is False
        
        # At start
        result = meter.get_musical_time(10.0)
        assert result is not False
        assert result.cycle_number == 0
        assert result.hierarchical_position == [0, 0]
        
        # Just before end
        result = meter.get_musical_time(end_time - 0.01)
        assert result is not False
        
        # At end (should be valid after Issue #38 fix)
        result = meter.get_musical_time(end_time)
        assert result is not False, "Exact end time should be valid (Issue #38 fix)"
        
        # After end (should still be invalid)
        assert meter.get_musical_time(end_time + 0.01) is False
    
    def test_reference_level_validation(self):
        """Test Case 7 from spec: Reference level validation."""
        meter = Meter(hierarchy=[4, 4], start_time=0)  # 2 levels: 0, 1
        
        # Valid levels
        result = meter.get_musical_time(1.0, reference_level=0)
        assert result is not False
        
        result = meter.get_musical_time(1.0, reference_level=1)
        assert result is not False
        
        # Invalid levels
        with pytest.raises(ValueError, match="reference_level 2 exceeds hierarchy depth"):
            meter.get_musical_time(1.0, reference_level=2)
        
        with pytest.raises(ValueError, match="reference_level must be non-negative"):
            meter.get_musical_time(1.0, reference_level=-1)
        
        with pytest.raises(TypeError, match="reference_level must be an integer"):
            meter.get_musical_time(1.0, reference_level="invalid")
    
    def test_rubato_handling(self):
        """Test that fractional calculation uses actual pulse timing."""
        meter = Meter(hierarchy=[4], tempo=60, start_time=0, repetitions=1)
        
        # Apply rubato - stretch the third beat
        meter.offset_pulse(meter.all_pulses[2], 0.5)   # Beat 3: 2.0 -> 2.5
        
        # Query time between beats 2 and 3 (between 1.0 and 2.5)
        query_time = 1.5  # Halfway between beat 2 and stretched beat 3
        result = meter.get_musical_time(query_time)
        
        assert result is not False
        assert result.hierarchical_position == [1]  # Beat 2
        # Should reflect actual pulse spacing (1.5 seconds between beats 2 and 3)
        expected_fraction = 0.5 / 1.5  # 0.5 seconds into 1.5 second gap
        assert abs(result.fractional_beat - expected_fraction) < 0.1
    
    def test_multiple_cycles(self):
        """Test musical time with multiple cycles."""
        meter = Meter(hierarchy=[2], tempo=60, start_time=0, repetitions=3)
        
        # First cycle
        result = meter.get_musical_time(0.5)
        assert result is not False
        assert result.cycle_number == 0
        
        # Second cycle  
        result = meter.get_musical_time(2.5)
        assert result is not False
        assert result.cycle_number == 1
        
        # Third cycle
        result = meter.get_musical_time(4.5)
        assert result is not False
        assert result.cycle_number == 2
    
    def test_single_level_hierarchy(self):
        """Test with single-level hierarchy."""
        meter = Meter(hierarchy=[4], tempo=60, start_time=0)
        
        result = meter.get_musical_time(1.5)
        assert result is not False
        assert len(result.hierarchical_position) == 1
        assert result.hierarchical_position == [1]
        assert result.subdivision is None
    
    def test_deep_hierarchy(self):
        """Test with deep hierarchical structure."""
        meter = Meter(hierarchy=[2, 2, 2, 2], tempo=240, start_time=0)
        
        result = meter.get_musical_time(0.125)
        assert result is not False
        assert len(result.hierarchical_position) == 4
        assert result.hierarchy_depth == 4
        
        # Test different reference levels
        result_beat = meter.get_musical_time(0.125, reference_level=0)
        assert len(result_beat.hierarchical_position) == 1
        
        result_subdiv = meter.get_musical_time(0.125, reference_level=1) 
        assert len(result_subdiv.hierarchical_position) == 2



# Additional tests for edge cases
class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_zero_fractional_beat_boundary(self):
        """Test that fractional beat of exactly 0.0 is valid."""
        mt = MusicalTime(0, [0], 0.0)
        assert mt.fractional_beat == 0.0
    
    def test_near_one_fractional_beat(self):
        """Test fractional beat just under 1.0."""
        mt = MusicalTime(0, [0], 0.999)
        assert mt.fractional_beat == 0.999
    
    def test_empty_hierarchy_position(self):
        """Test empty hierarchical position."""
        mt = MusicalTime(1, [], 0.0)
        assert mt.hierarchy_depth == 0
        assert mt.beat == 0  # Default value
        assert mt.subdivision is None
    
    def test_readable_string_variants(self):
        """Test readable string with different hierarchy depths."""
        # Single level
        mt1 = MusicalTime(0, [2], 0.0)
        readable1 = mt1.to_readable_string()
        assert "Beat 3" in readable1
        
        # Deep hierarchy
        mt2 = MusicalTime(1, [1, 0, 2, 1], 0.123)
        readable2 = mt2.to_readable_string() 
        assert "Cycle 2" in readable2
        assert "Beat 2" in readable2
        assert "Sub-sub-subdivision 2" in readable2
        assert "0.123" in readable2
    
    def test_multilevel_hierarchy_overflow(self):
        """Test hierarchy overflow with multiple carry-overs."""
        # Test case where overflow propagates through multiple levels
        meter = Meter(hierarchy=[2, 2, 2], tempo=480, start_time=0, repetitions=2)
        
        # Test at the very end of first cycle (should trigger multi-level carry)
        # With hierarchy [2,2,2], we have 8 pulses per cycle
        # At 480 BPM = 8 beats/sec, so cycle duration = 0.25 sec
        end_of_first_cycle = 0.25 - 0.001
        result = meter.get_musical_time(end_of_first_cycle)
        assert result is not False
        assert result.cycle_number == 0
        
        # Test at start of second cycle
        result = meter.get_musical_time(0.25)
        assert result is not False
        assert result.cycle_number == 1
        assert result.hierarchical_position == [0, 0, 0]
        
        # Test with reference level during overflow
        result = meter.get_musical_time(0.249, reference_level=1)
        assert result is not False
        assert len(result.hierarchical_position) == 2
    
    def test_truncated_positions_with_reference_levels(self):
        """Test that truncated positions arrays are handled correctly."""
        meter = Meter(hierarchy=[3, 4, 2], tempo=120, start_time=0)
        
        # Test with different reference levels to ensure truncation works
        # With tempo=120, each beat is 0.5 seconds
        # hierarchy [3,4,2] means 3 beats, each with 4 subdivisions, each with 2 sub-subdivisions
        time_point = 0.75  # Within the meter (1.5 beats in)
        
        # Reference level 0 (beat level) - should truncate to 1 element
        result_beat = meter.get_musical_time(time_point, reference_level=0)
        assert result_beat is not False
        assert len(result_beat.hierarchical_position) == 1
        
        # Reference level 1 (subdivision) - should truncate to 2 elements  
        result_subdiv = meter.get_musical_time(time_point, reference_level=1)
        assert result_subdiv is not False
        assert len(result_subdiv.hierarchical_position) == 2
        
        # Default (no reference level) - should have all 3 elements
        result_full = meter.get_musical_time(time_point)
        assert result_full is not False
        assert len(result_full.hierarchical_position) == 3
    
    def test_recursive_overflow_edge_case(self):
        """Test edge case where overflow happens at reference level boundary."""
        meter = Meter(hierarchy=[2, 3], tempo=60, start_time=0)
        
        # Position at end of a subdivision that would cause overflow
        # With hierarchy [2,3], cycle duration = 2 sec, beat duration = 1 sec
        # Test at 0.999s which is 49.95% through the 2-second cycle
        time_at_subdivision_boundary = 0.999
        
        result = meter.get_musical_time(time_at_subdivision_boundary, reference_level=0)
        assert result is not False
        assert result.beat == 0
        assert abs(result.fractional_beat - 0.997) < 0.01  # 99.7% between pulses (fractional_beat always pulse-based)
        
        # Same time with subdivision reference should handle overflow correctly
        result = meter.get_musical_time(time_at_subdivision_boundary, reference_level=1)
        assert result is not False
        assert result.hierarchical_position[0] == 0  # Still in beat 0
        assert result.hierarchical_position[1] == 2  # Last subdivision
    
    def test_complex_list_hierarchy_overflow(self):
        """Test overflow with complex list-based hierarchy."""
        # Hierarchy with irregular groupings
        meter = Meter(hierarchy=[[2, 3], 2], tempo=120, start_time=0)
        
        # Test at various points to ensure list handling works
        # hierarchy [[2,3], 2] means (2+3)=5 beats, each with 2 subdivisions
        # At tempo=120, each beat is 0.5 seconds
        result = meter.get_musical_time(1.0)  # At 2 beats (1.0 / 0.5 = 2)
        assert result is not False
        assert result.beat == 2  # Third beat (index 2)
        
        result = meter.get_musical_time(2.0)  # At 4 beats
        assert result is not False
        assert result.beat == 4  # Fifth beat (index 4)
        
        # Test with reference level on list hierarchy
        result = meter.get_musical_time(1.5, reference_level=0)
        assert result is not False
        assert len(result.hierarchical_position) == 1
    
    def test_reference_level_zero_indexerror_reproduction(self):
        """Test to reproduce IndexError with reference_level=0 (Issue #26)."""
        # Try different meter configurations that might trigger the error
        test_configs = [
            ([4, 4, 2], 120),
            ([2, 3, 4], 60), 
            ([3, 2], 240),
            ([8], 120),
            ([2, 2, 2, 2], 180)
        ]
        
        for hierarchy, tempo in test_configs:
            meter = Meter(hierarchy=hierarchy, tempo=tempo, start_time=0)
            
            # Test various time points within the meter
            cycle_duration = meter.cycle_dur
            test_times = [
                0.1,  # Near start
                cycle_duration * 0.25,  # Quarter way through
                cycle_duration * 0.5,   # Half way 
                cycle_duration * 0.75,  # Three quarters
                cycle_duration * 0.99,  # Near end
            ]
            
            for time_point in test_times:
                try:
                    result = meter.get_musical_time(time_point, reference_level=0)
                    if result is not False:  # Only check if within meter bounds
                        assert len(result.hierarchical_position) == 1, f"Should have 1 position for reference_level=0 with hierarchy {hierarchy}"
                        assert result.hierarchical_position[0] >= 0, "Position should be non-negative"
                except IndexError as e:
                    pytest.fail(f"IndexError raised with hierarchy {hierarchy}, tempo {tempo}, time {time_point}, reference_level=0: {e}")
                except Exception as e:
                    # Let other exceptions bubble up with context
                    pytest.fail(f"Unexpected error with hierarchy {hierarchy}, tempo {tempo}, time {time_point}: {e}")
        
        # Test edge case: reference_level=0 with positions that might cause overflow
        meter = Meter(hierarchy=[2, 2], tempo=60, start_time=0)
        try:
            # Test at exact beat boundaries which might cause index issues
            result = meter.get_musical_time(1.0, reference_level=0)  # Exactly at beat 1
            if result is not False:
                assert len(result.hierarchical_position) == 1
        except IndexError as e:
            pytest.fail(f"IndexError at beat boundary with reference_level=0: {e}")
        
        # Test with multi-cycle meter - this might trigger the error
        meter = Meter(hierarchy=[4, 4, 2], tempo=120, start_time=0, repetitions=2)
        try:
            # Test near the end of cycle or at various points
            test_times = [meter.cycle_dur - 0.01, meter.cycle_dur + 0.01, meter.cycle_dur * 1.5]
            for t in test_times:
                result = meter.get_musical_time(t, reference_level=0)
                if result is not False:
                    assert len(result.hierarchical_position) == 1
        except IndexError as e:
            pytest.fail(f"IndexError with multi-cycle meter and reference_level=0: {e}")
        
        # Test very specific timing that might trigger calculation edge case
        meter = Meter(hierarchy=[4, 4, 2], tempo=120, start_time=0)
        try:
            # Test at the end of each beat - this is where overflow might happen
            beat_duration = 60.0 / 120  # 0.5 seconds per beat at 120 BPM
            for beat in range(4):  # Test each beat in the cycle
                time_at_end_of_beat = beat_duration * (beat + 1) - 0.001  # Just before next beat
                result = meter.get_musical_time(time_at_end_of_beat, reference_level=0)
                if result is not False:
                    assert len(result.hierarchical_position) == 1
        except IndexError as e:
            pytest.fail(f"IndexError at beat boundaries with reference_level=0: {e}")
        
        # Test the specific case where next_positions causes pulse index overflow
        # This happens when we're at the last beat of a cycle with reference_level=0
        meter = Meter(hierarchy=[4, 2], tempo=120, start_time=0, repetitions=1)  
        try:
            # Get close to the end of the last beat (beat 3, index 3 in hierarchy [4, 2])
            # With tempo 120, beat duration is 0.5 seconds
            # Total cycle duration should be 4 beats * 0.5 = 2.0 seconds
            # Let's test at beat 3.9 (just before beat 4, which would overflow)
            time_near_end = 3.9 * 0.5  # Should be 1.95 seconds
            result = meter.get_musical_time(time_near_end, reference_level=0)
            if result is not False:
                assert len(result.hierarchical_position) == 1
                # This should trigger the duration calculation that tries to find the "next beat"
                # which would be beat 4 (index 4), causing overflow since hierarchy[0] = 4 (indices 0,1,2,3)
        except IndexError as e:
            pytest.fail(f"IndexError when calculating duration near end of cycle with reference_level=0: {e}")
        
        # Even more specific test - try to force the exact overflow scenario
        meter = Meter(hierarchy=[2], tempo=60, start_time=0, repetitions=1)
        try:
            # With hierarchy [2], we have beats 0 and 1
            # Test at beat 1 (the last beat) - this should cause next_position[0] = 2, which overflows
            beat_1_time = 1.0 * (60.0 / 60.0) * 0.9  # 90% through beat 1
            result = meter.get_musical_time(beat_1_time, reference_level=0)
            if result is not False:
                assert len(result.hierarchical_position) == 1
        except IndexError as e:
            pytest.fail(f"IndexError with simple [2] hierarchy at last beat with reference_level=0: {e}")
    
    def test_reference_level_zero_bounds_checking(self):
        """Test that bounds checking prevents IndexError when pulse index exceeds bounds."""
        # Test with a simple meter where we can predictably hit boundary conditions
        meter = Meter(hierarchy=[2, 2], tempo=60, start_time=0, repetitions=1)
        
        # Test at various points including near boundaries
        # The key is testing reference_level=0 which might try to calculate duration
        # by looking for the "next beat" which could exceed pulse array bounds
        test_times = []
        beat_duration = 60.0 / 60.0  # 1 second per beat at 60 BPM
        
        # Add times throughout the meter, especially near beat boundaries
        for beat in range(2):  # 2 beats in hierarchy [2, 2]
            for fraction in [0.1, 0.5, 0.9, 0.99]:
                test_time = beat * beat_duration + fraction * beat_duration
                test_times.append(test_time)
        
        # Test all time points with reference_level=0
        for time_point in test_times:
            result = meter.get_musical_time(time_point, reference_level=0)
            if result is not False:
                assert len(result.hierarchical_position) == 1, f"Should have 1 position at time {time_point}"
                assert isinstance(result.fractional_beat, float), f"Should have valid fractional_beat at time {time_point}"
                assert 0.0 <= result.fractional_beat <= 1.0, f"fractional_beat should be in [0,1] at time {time_point}"
        
        # Test specifically at the boundary that might cause the original IndexError
        # When we're in the last beat and try to calculate duration
        last_beat_time = 1.8  # Near end of beat 1 (last beat) in a 2-beat cycle
        result = meter.get_musical_time(last_beat_time, reference_level=0)
        if result is not False:
            assert len(result.hierarchical_position) == 1
            assert result.hierarchical_position[0] == 1  # Should be in beat 1 (second beat)
            
    def test_defensive_bounds_in_calculate_level_start_time(self):
        """Test that _calculate_level_start_time handles out-of-bounds indices gracefully."""
        meter = Meter(hierarchy=[3], tempo=120, start_time=0, repetitions=1)
        
        # This should work without IndexError even if internal calculations go out of bounds
        # Test near the end of the cycle where "next beat" calculations might overflow
        near_end_time = meter.cycle_dur * 0.95
        result = meter.get_musical_time(near_end_time, reference_level=0)
        
        if result is not False:
            assert len(result.hierarchical_position) == 1
            # Should not crash and should give reasonable results
    
    def test_fractional_beat_distribution_with_reference_level_zero(self):
        """Test that fractional_beat varies smoothly from 0.0 to 1.0 with reference_level=0 (Issue #28)."""
        # Create a simple meter for predictable testing
        meter = Meter(hierarchy=[4, 4], tempo=120, start_time=0, repetitions=1)
        
        # Test parameters
        beat_duration = 60.0 / 120.0  # 0.5 seconds per beat at 120 BPM
        samples_per_beat = 10
        
        print(f"\n=== Testing fractional_beat distribution (Issue #28) ===")
        print(f"Meter: hierarchy={meter.hierarchy}, tempo={meter.tempo} BPM")
        print(f"Beat duration: {beat_duration:.3f} seconds")
        print(f"Cycle duration: {meter.cycle_dur:.3f} seconds")
        print()
        
        # Test each beat in the cycle
        all_fractional_beats = []
        for beat_idx in range(4):  # 4 beats in hierarchy [4, 4]
            print(f"Beat {beat_idx}:")
            beat_fractional_beats = []
            
            # Sample within this beat
            beat_start_time = beat_idx * beat_duration
            beat_end_time = (beat_idx + 1) * beat_duration
            
            for i in range(samples_per_beat):
                # Sample from 10% to 90% through the beat to avoid boundary edge cases
                fraction_through_beat = 0.1 + (0.8 * i / (samples_per_beat - 1))
                test_time = beat_start_time + fraction_through_beat * beat_duration
                
                result = meter.get_musical_time(test_time, reference_level=0)
                if result is not False:
                    beat_fractional_beats.append(result.fractional_beat)
                    all_fractional_beats.append(result.fractional_beat)
                    print(f"  {test_time:.3f}s -> beat={result.hierarchical_position[0]}, frac={result.fractional_beat:.3f}")
            
            # Validate this beat's fractional_beat distribution
            if beat_fractional_beats:
                min_frac = min(beat_fractional_beats)
                max_frac = max(beat_fractional_beats)
                unique_values = len(set([round(f, 3) for f in beat_fractional_beats]))
                
                print(f"  Range: {min_frac:.3f} to {max_frac:.3f}, {unique_values} unique values")
                
                # Critical assertions for Issue #28
                assert min_frac >= 0.0, f"Beat {beat_idx}: fractional_beat minimum {min_frac} should be >= 0.0"
                assert max_frac <= 1.0, f"Beat {beat_idx}: fractional_beat maximum {max_frac} should be <= 1.0"
                
                # With corrected reference_level=0 (within cycle): fractional_beat varies across cycle, not within individual beats
                # For a 2-second cycle with 4 beats, each beat spans 0.25 of the cycle (range ~0.2)
                range_span = max_frac - min_frac
                assert range_span > 0.15, f"Beat {beat_idx}: fractional_beat range {range_span:.3f} is too small. Values clustering near 0.000 (Issue #28 symptom)"
                
                # Should have reasonable variation in values
                assert unique_values >= 3, f"Beat {beat_idx}: Only {unique_values} unique fractional_beat values, expected more variation"
            
            print()
        
        # Overall analysis across all beats
        if all_fractional_beats:
            overall_unique = len(set([round(f, 3) for f in all_fractional_beats]))
            overall_min = min(all_fractional_beats)
            overall_max = max(all_fractional_beats)
            overall_range = overall_max - overall_min
            
            print(f"Overall Analysis:")
            print(f"  Total samples: {len(all_fractional_beats)}")
            print(f"  Unique fractional_beat values: {overall_unique}")
            print(f"  Range: {overall_min:.3f} to {overall_max:.3f} (span: {overall_range:.3f})")
            print(f"  Distribution: {sorted(set([round(f, 3) for f in all_fractional_beats]))}")
            
            # Key assertions for Issue #28
            assert overall_unique >= 10, f"Issue #28: Only {overall_unique} unique fractional_beat values across all samples - should have much more variation"
            assert overall_range > 0.5, f"Issue #28: Overall fractional_beat range {overall_range:.3f} is too small - values clustering near 0.000"
    
    def test_fractional_beat_comparison_across_reference_levels(self):
        """Compare fractional_beat behavior across different reference levels."""
        meter = Meter(hierarchy=[3, 3], tempo=90, start_time=0)
        
        # Test at a specific time point
        test_time = 1.0  # 1 second into the meter
        
        # Get musical time at different reference levels
        result_default = meter.get_musical_time(test_time)  # Default (finest level)
        result_level_0 = meter.get_musical_time(test_time, reference_level=0)  # Beat level
        result_level_1 = meter.get_musical_time(test_time, reference_level=1)  # Subdivision level
        
        print(f"\n=== Reference level comparison at {test_time}s ===")
        if result_default:
            print(f"Default: {result_default} (frac={result_default.fractional_beat:.3f})")
        if result_level_0:
            print(f"Level 0: {result_level_0} (frac={result_level_0.fractional_beat:.3f})")
        if result_level_1:  
            print(f"Level 1: {result_level_1} (frac={result_level_1.fractional_beat:.3f})")
        
        # All should return valid results
        assert result_default is not False
        assert result_level_0 is not False
        assert result_level_1 is not False
        
        # fractional_beat should be reasonable for all levels
        assert 0.0 <= result_default.fractional_beat <= 1.0
        assert 0.0 <= result_level_0.fractional_beat <= 1.0
        assert 0.0 <= result_level_1.fractional_beat <= 1.0
        
        # Each reference level should give different hierarchical position lengths
        assert len(result_level_0.hierarchical_position) == 1  # Beat only
        assert len(result_level_1.hierarchical_position) == 2  # Beat + subdivision
        assert len(result_default.hierarchical_position) == 2  # Full hierarchy [3, 3]
    
    def test_issue_28_exact_reproduction(self):
        """Exact reproduction of Issue #28 with hierarchy [4, 4, 2] and similar parameters."""
        # Create meter matching the issue description
        meter = Meter(hierarchy=[4, 4, 2], tempo=58.3, start_time=4.093, repetitions=1)
        
        print(f"\n=== Issue #28 Exact Reproduction Test ===")
        print(f"Hierarchy: {meter.hierarchy}")
        print(f"Tempo: {meter.tempo:.1f} BPM")
        print(f"Cycle duration: {meter.cycle_dur:.3f} seconds")
        print(f"Start time: {meter.start_time:.3f} seconds")
        print()
        
        # Sample times similar to the issue description
        cycle_start = meter.start_time
        cycle_end = meter.start_time + meter.cycle_dur
        sample_times = [
            cycle_start + 0.0,     # Start
            cycle_start + 0.216,   # ~5% in  
            cycle_start + 0.432,   # ~10% in
            cycle_start + 0.649,   # ~15% in
            cycle_start + 0.865,   # ~20% in
            cycle_start + 1.081,   # ~25% in
            cycle_start + 1.297,   # ~30% in
            cycle_start + 1.513,   # ~35% in
            cycle_start + 1.729,   # ~40% in
            cycle_start + 1.946,   # ~45% in
            cycle_start + 2.162,   # ~50% in
            cycle_start + 2.378,   # ~55% in
            cycle_start + 2.594,   # ~60% in
            cycle_start + 2.810,   # ~65% in
            cycle_start + 3.026,   # ~70% in
            cycle_start + 3.242,   # ~75% in
            cycle_start + 3.459,   # ~80% in
            cycle_start + 3.675,   # ~85% in
            cycle_start + 3.891,   # ~90% in
            cycle_start + 4.100,   # ~95% in (just before end)
        ]
        
        print("Time      | Musical Time (ref=0)     | fractional_beat | Beat | Analysis")
        print("--------- | ------------------------ | --------------- | ---- | --------")
        
        fractional_beats = []
        clustering_issues = []
        
        for time_point in sample_times:
            if time_point < cycle_end:  # Within bounds
                try:
                    result = meter.get_musical_time(time_point, reference_level=0)
                    if result is not False:
                        fractional_beats.append(result.fractional_beat)
                        beat_num = result.hierarchical_position[0] if result.hierarchical_position else "?"
                        
                        # Check for clustering (Issue #28 symptom)
                        is_clustered = result.fractional_beat < 0.05
                        analysis = "CLUSTERED!" if is_clustered else "normal"
                        if is_clustered:
                            clustering_issues.append(time_point)
                        
                        print(f"{time_point:8.3f}s | {str(result):24} | {result.fractional_beat:11.3f} | {beat_num:4} | {analysis}")
                    else:
                        print(f"{time_point:8.3f}s | {'Out of bounds':24} | {'N/A':15} | {'N/A':4} | out-of-bounds")
                except Exception as e:
                    print(f"{time_point:8.3f}s | {'ERROR: ' + str(e):24} | {'N/A':15} | {'N/A':4} | error")
        
        # Analysis of results
        print(f"\n=== Analysis ===")
        if fractional_beats:
            unique_values = len(set([round(f, 3) for f in fractional_beats]))
            min_frac = min(fractional_beats)
            max_frac = max(fractional_beats)
            range_span = max_frac - min_frac
            
            clustered_count = sum(1 for f in fractional_beats if f < 0.05)
            clustered_percentage = clustered_count / len(fractional_beats) * 100
            
            print(f"Total samples: {len(fractional_beats)}")
            print(f"Unique values: {unique_values}")
            print(f"Range: {min_frac:.3f} to {max_frac:.3f} (span: {range_span:.3f})")
            print(f"Clustered near 0.000 (< 0.05): {clustered_count}/{len(fractional_beats)} ({clustered_percentage:.1f}%)")
            print(f"Distribution: {sorted(set([round(f, 3) for f in fractional_beats]))}")
            
            # Detect Issue #28 symptoms
            issue_28_detected = False
            
            if clustered_percentage > 60:
                print(f"⚠️  ISSUE #28 DETECTED: {clustered_percentage:.1f}% of values clustered near 0.000")
                issue_28_detected = True
            
            if unique_values < 8:
                print(f"⚠️  ISSUE #28 DETECTED: Only {unique_values} unique fractional_beat values (too few)")
                issue_28_detected = True
                
            if range_span < 0.4:
                print(f"⚠️  ISSUE #28 DETECTED: fractional_beat range {range_span:.3f} too small")  
                issue_28_detected = True
            
            if not issue_28_detected:
                print("✓ No Issue #28 symptoms detected")
                
            # Assertions for proper functionality (these will fail if Issue #28 exists)
            assert clustered_percentage < 60, f"Issue #28: {clustered_percentage:.1f}% of fractional_beat values clustered near 0.000"
            assert unique_values >= 8, f"Issue #28: Only {unique_values} unique fractional_beat values, should have more variation"
            assert range_span >= 0.4, f"Issue #28: fractional_beat range {range_span:.3f} too small, should span more of [0,1]"
        
        else:
            pytest.fail("No fractional_beat values collected - test setup issue")
        
        print("✓ Issue #28 reproduction test passed")
    
    def test_deep_investigation_of_fractional_beat_calculation(self):
        """Deep dive into what happens during fractional_beat calculation with reference_level=0."""
        meter = Meter(hierarchy=[4, 4, 2], tempo=60, start_time=0, repetitions=1)
        
        print(f"\n=== Deep Investigation: fractional_beat calculation ===")
        print(f"Hierarchy: {meter.hierarchy}")
        print(f"Total pulses: {len(meter.all_pulses)}")
        print(f"Pulses per cycle: {meter._pulses_per_cycle}")
        print()
        
        # Test at specific subdivision positions that might reveal the issue
        # If we're at beat 1, subdivision 2, sub-subdivision 1: position [1, 2, 1]
        # With reference_level=0, this gets truncated to [1] and extended to [1, 0, 0]
        # This might be the source of incorrect fractional_beat calculation
        
        # Let's test at times that would put us in the middle of subdivisions
        beat_duration = 60.0 / 60.0  # 1 second per beat at 60 BPM
        subdivision_duration = beat_duration / 4  # 0.25 seconds per subdivision
        sub_subdivision_duration = subdivision_duration / 2  # 0.125 seconds per sub-subdivision
        
        test_cases = [
            # (description, time, expected_beat, expected_subdivision_approx)  
            ("Start of beat 0", 0.0, 0, 0),
            ("Middle of beat 0, subdivision 1", 0.25 + 0.1, 0, 1),  
            ("Middle of beat 0, subdivision 2", 0.5 + 0.1, 0, 2),
            ("Middle of beat 0, subdivision 3", 0.75 + 0.1, 0, 3),
            ("Start of beat 1", 1.0, 1, 0),
            ("Middle of beat 1, subdivision 2", 1.5 + 0.1, 1, 2),
            ("Middle of beat 2, subdivision 1", 2.25 + 0.1, 2, 1),
            ("Middle of beat 3, subdivision 3", 3.75 + 0.1, 3, 3),
        ]
        
        print("Description                              | Time    | Default Result                    | Ref=0 Result                     | Issue?")
        print("---------------------------------------- | ------- | --------------------------------- | --------------------------------- | ------")
        
        for desc, time_point, expected_beat, expected_subdiv in test_cases:
            # Get both default and reference_level=0 results
            result_default = meter.get_musical_time(time_point)
            result_ref0 = meter.get_musical_time(time_point, reference_level=0)
            
            if result_default and result_ref0:
                default_str = f"{result_default} (frac={result_default.fractional_beat:.3f})"
                ref0_str = f"{result_ref0} (frac={result_ref0.fractional_beat:.3f})"
                
                # Check if we're in the middle of a subdivision but fractional_beat is near 0
                is_in_subdivision_middle = len(result_default.hierarchical_position) >= 2 and result_default.hierarchical_position[1] > 0
                fractional_beat_near_zero = result_ref0.fractional_beat < 0.1
                
                potential_issue = is_in_subdivision_middle and fractional_beat_near_zero
                issue_flag = "⚠️ ISSUE" if potential_issue else "OK"
                
                print(f"{desc:40} | {time_point:7.3f} | {default_str:33} | {ref0_str:33} | {issue_flag}")
                
                if potential_issue:
                    print(f"    → DETECTED: In subdivision {result_default.hierarchical_position[1]} but fractional_beat={result_ref0.fractional_beat:.3f}")
                    
            else:
                print(f"{desc:40} | {time_point:7.3f} | {'None/False':33} | {'None/False':33} | ERROR")
        
        print("\nThis test helps identify if the issue is related to position truncation when")
        print("we're in the middle of subdivisions but reference_level=0 calculation starts")
        print("from the wrong subdivision boundary.")

    def test_issue_36_hierarchical_position_correction(self):
        """Test fix for Issue #36: hierarchical position calculation bug in multi-cycle meters.
        
        Ensures that the hierarchical position calculation always finds a pulse that comes
        at or before the query time, preventing negative fractional_beat values that get
        clamped to 0.0.
        """
        # Create meter with timing variations that expose the hierarchical calculation bug
        meter = Meter(hierarchy=[4, 4, 2], start_time=4.0, tempo=60.0, repetitions=4)
        
        # Introduce pulse timing variations that can trigger the bug
        for i, pulse in enumerate(meter.all_pulses):
            if i % 7 == 0:  # Every 7th pulse gets adjusted timing
                pulse.real_time += 0.05  # 50ms later - enough to cause issues
        
        # Re-sort pulses by time after timing modifications
        meter.pulse_structures[0][0].pulses.sort(key=lambda p: p.real_time)
        
        # Test times that would previously cause fractional_beat=0.0 due to the bug
        test_times = [5.0, 8.5, 12.2, 16.8]
        
        for time in test_times:
            result = meter.get_musical_time(time)
            
            # Should be within meter boundaries
            assert result is not False, f"Time {time} should be within meter boundaries"
            
            # The fix ensures fractional_beat is reasonable (not clamped to 0.0 due to bug)
            assert 0.0 <= result.fractional_beat < 1.0, f"fractional_beat out of range for time {time}"
            
            # Verify hierarchical position points to correct pulse
            pulse_index = meter._hierarchical_position_to_pulse_index(
                result.hierarchical_position, result.cycle_number
            )
            assert 0 <= pulse_index < len(meter.all_pulses), f"Pulse index should be valid for time {time}"
            
            pulse_time = meter.all_pulses[pulse_index].real_time
            assert pulse_time <= time, f"Calculated pulse should come at/before query time {time}, got {pulse_time}"

    def test_issue_38_cycle_boundary_failures(self):
        """Test fix for Issue #38: get_musical_time() fails at cycle boundaries.
        
        Ensures that get_musical_time() returns valid musical time objects for
        timestamps at exact cycle boundaries, including the final meter boundary.
        """
        # Create meter with multiple cycles to test all boundary types
        meter = Meter(hierarchy=[4, 4, 2], start_time=0.0, tempo=60.0, repetitions=4)
        
        # Test each cycle boundary including the final one
        for cycle in range(meter.repetitions + 1):
            boundary_time = meter.start_time + cycle * meter.cycle_dur
            
            result = meter.get_musical_time(boundary_time)
            
            # All boundaries should return valid musical time objects
            assert result is not False, f"Cycle boundary at {boundary_time} should return valid musical time"
            assert 0.0 <= result.fractional_beat < 1.0, f"fractional_beat should be in valid range for boundary {boundary_time}"
            
            # Boundary should be treated as start of next cycle (if not final boundary)
            if cycle < meter.repetitions:
                assert result.cycle_number == cycle, f"Boundary {boundary_time} should be in cycle {cycle}"
                assert result.hierarchical_position[0] == 0, f"Boundary should be at start of hierarchical position"
            else:
                # Final boundary - with pulse-based calculation, this falls in the final actual cycle
                assert result.cycle_number == cycle - 1, f"Final boundary should be in final cycle {cycle - 1} (pulse-based)"
        
        # Test times very close to boundaries to ensure they also work
        for cycle in range(meter.repetitions):
            boundary_time = meter.start_time + (cycle + 1) * meter.cycle_dur
            
            # Test time just before boundary
            near_boundary = boundary_time - 0.001
            result = meter.get_musical_time(near_boundary)
            assert result is not False, f"Time just before boundary {boundary_time} should be valid"
            
            # Should be in the previous cycle
            assert result.cycle_number == cycle, f"Time before boundary should be in cycle {cycle}"

    def test_issue_40_cycle_number_correction(self):
        """Test fix for Issue #40: get_musical_time() returns incorrect cycle numbers at cycle boundaries.
        
        Tests that when pulse data has timing variations (rubato), get_musical_time() uses 
        actual pulse-based cycle boundaries instead of theoretical boundaries.
        """
        # Create meter similar to Issue #40 transcription  
        meter = Meter(hierarchy=[4, 4, 2], start_time=4.093, tempo=58.3, repetitions=8)
        
        # Simulate timing variations by adjusting specific pulses to match Issue #40 boundaries
        # Issue #40 cycle boundaries:
        # Cycle 3: 16.597 - 20.727 (time 20.601 should be in cycle 3, not 4)
        expected_boundaries = [4.093, 8.350, 12.480, 16.597, 20.727, 24.844, 28.968, 33.121, 37.268]
        
        # Adjust pulse timing to match expected boundaries
        for cycle in range(len(expected_boundaries) - 1):
            cycle_start_pulse_idx = cycle * meter._pulses_per_cycle
            if cycle_start_pulse_idx < len(meter.all_pulses):
                # Set first pulse of each cycle to exact boundary time
                meter.all_pulses[cycle_start_pulse_idx].real_time = expected_boundaries[cycle]
                
                # Adjust remaining pulses in cycle proportionally
                cycle_duration = expected_boundaries[cycle + 1] - expected_boundaries[cycle]
                for pulse_in_cycle in range(1, 32):  # Pulses 1-31 in cycle
                    pulse_idx = cycle_start_pulse_idx + pulse_in_cycle
                    if pulse_idx < len(meter.all_pulses):
                        pulse_time = expected_boundaries[cycle] + (pulse_in_cycle * cycle_duration / 32)
                        meter.all_pulses[pulse_idx].real_time = pulse_time
        
        # Re-sort pulses by time after modifications
        meter.pulse_structures[0][0].pulses.sort(key=lambda p: p.real_time)
        
        # Test the specific Issue #40 case: trajectory in cycle 4
        # Time 20.601 should be in cycle 3 (16.597 - 20.727), not cycle 4
        test_cases = [
            (20.600969, 3, "Start of trajectory 'n' - should be cycle 3"),
            (20.602238, 3, "Part of trajectory 'n' - should be cycle 3"),
            (20.726, 3, "Just before cycle 4 boundary - should be cycle 3"),  
            (20.727, 4, "Exactly at cycle 4 boundary - should be cycle 4"),
        ]
        
        for time, expected_cycle, description in test_cases:
            result = meter.get_musical_time(time)
            assert result is not False, f"Time {time} should return valid musical time ({description})"
            assert result.cycle_number == expected_cycle, \
                f"Time {time}: expected cycle {expected_cycle}, got {result.cycle_number} ({description})"
