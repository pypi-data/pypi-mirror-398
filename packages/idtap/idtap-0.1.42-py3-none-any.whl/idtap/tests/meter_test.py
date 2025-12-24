import os
import sys
import math
import pytest

sys.path.insert(0, os.path.abspath('.'))

from idtap.classes.meter import Meter, Pulse, PulseStructure, find_closest_idxs
from idtap.enums import TalaName

# Tests mirror src/ts/tests/meter.test.js (simplified implementation)

def test_meter_reset_tempo_and_grow_cycle():
    m = Meter()
    assert isinstance(m, Meter)
    assert m.real_times == [
        0, 0.25, 0.5, 0.75,
        1, 1.25, 1.5, 1.75,
        2, 2.25, 2.5, 2.75,
        3, 3.25, 3.5, 3.75
    ]

    a = Meter(hierarchy=[4])
    assert a.real_times == [0, 1, 2, 3]
    last_pulse = a.all_pulses[-1]
    a.offset_pulse(last_pulse, -0.5)
    assert a.real_times == [0, 1, 2, 2.5]
    a.reset_tempo()
    assert a.real_times == [0, 1, 2, 2.5]
    a.grow_cycle()
    times = [0, 1, 2, 2.5, 10/3, 25/6, 30/6, 35/6]
    for rt, exp in zip(a.real_times, times):
        assert pytest.approx(rt, rel=1e-8) == exp

    b = Meter(hierarchy=[[2, 2]])
    assert b.real_times == [0, 1, 2, 3]
    b_last = b.all_pulses[-1]
    b.offset_pulse(b_last, -0.5)
    assert b.real_times == [0, 1, 2, 2.5]
    b.reset_tempo()
    assert b.real_times == [0, 1, 2, 2.5]
    b.grow_cycle()
    for rt, exp in zip(b.real_times, times):
        assert pytest.approx(rt, rel=1e-8) == exp

    c = Meter(hierarchy=[2, 2], tempo=30)
    assert c.real_times == [0, 1, 2, 3]
    c_last = c.all_pulses[-1]
    c.offset_pulse(c_last, -0.5)
    assert c.real_times == [0, 1, 2, 2.5]
    c.reset_tempo()
    assert c.real_times == [0, 1, 2, 2.5]
    c.grow_cycle()
    for rt, exp in zip(c.real_times, times):
        assert pytest.approx(rt, rel=1e-8) == exp

    d = Meter(hierarchy=[2, 2, 2], tempo=30)
    assert d.real_times == [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]
    d_last = d.all_pulses[-1]
    d.offset_pulse(d_last, -0.25)
    assert d.real_times == [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.25]
    d.reset_tempo()
    assert d.real_times == [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.25]
    d.grow_cycle()
    end1 = 3.25 * 8 / 7
    bit = end1 / 8
    next_times = [end1 + bit * i for i in range(8)]
    all_times = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.25] + next_times
    for rt, exp in zip(d.real_times, all_times):
        assert pytest.approx(rt, rel=1e-8) == exp

    e = Meter(hierarchy=[2, 2, 2, 2], tempo=15)
    assert e.real_times == [
        0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5,
        4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5
    ]
    e_last = e.all_pulses[-1]
    e.offset_pulse(e_last, -0.25)
    target_times = [
        0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5,
        4, 4.5, 5, 5.5, 6, 6.5, 7, 7.25
    ]
    assert e.real_times == target_times
    e.reset_tempo()
    for rt, exp in zip(e.real_times, target_times):
        assert pytest.approx(rt, rel=1e-8) == exp
    e.grow_cycle()
    end2 = 7.25 * 16 / 15
    bit2 = end2 / 16
    next_times2 = [end2 + bit2 * i for i in range(16)]
    all_times2 = target_times + next_times2
    for rt, exp in zip(e.real_times, all_times2):
        assert pytest.approx(rt, rel=1e-8) == exp


def test_more_complicated_single_layer():
    a = Meter(hierarchy=[7])
    b = Meter(hierarchy=[[2, 2, 3]])
    assert a.real_times == b.real_times
    a_last = a.all_pulses[-1]
    b_last = b.all_pulses[-1]
    a_third = a.all_pulses[2]
    b_third = b.all_pulses[2]
    a.offset_pulse(a_third, 0.1)
    b.offset_pulse(b_third, 0.1)
    a.offset_pulse(a_last, -0.5)
    b.offset_pulse(b_last, -0.5)
    assert a.real_times == b.real_times
    a.reset_tempo()
    b.reset_tempo()
    for rt, exp in zip(a.real_times, b.real_times):
        assert pytest.approx(rt, rel=1e-8) == exp
    a.grow_cycle()
    b.grow_cycle()
    for rt, exp in zip(a.real_times, b.real_times):
        assert pytest.approx(rt, rel=1e-8) == exp


def test_regeneration():
    pulse = Pulse()
    frozen = pulse.to_json()
    new_pulse = Pulse.from_json(frozen)
    assert new_pulse == pulse

    ps = PulseStructure()
    frozen2 = ps.to_json()
    new_ps = PulseStructure.from_json(frozen2)
    assert new_ps == ps
    assert isinstance(new_ps.pulses[0], Pulse)

    m = Meter()
    frozen3 = m.to_json()
    new_m = Meter.from_json(frozen3)
    assert new_m == m


def test_find_closest_idxs():
    trials = [1.1, 1.9, 4.4]
    items = [0, 1, 2, 3, 4, 5, 6, 7]
    expected = [1, 2, 4]
    assert find_closest_idxs(trials, items) == expected


def includes_with_tolerance(array, target, tolerance):
    return any(abs(item - target) <= tolerance for item in array)


def test_add_time_points():
    m = Meter()
    assert isinstance(m, Meter)
    assert m.real_times == [
        0, 0.25, 0.5, 0.75,
        1, 1.25, 1.5, 1.75,
        2, 2.25, 2.5, 2.75,
        3, 3.25, 3.5, 3.75
    ]
    new_times = [4.6, 5.1, 5.7]
    m.add_time_points(new_times, 1)
    for nt in new_times:
        assert includes_with_tolerance(m.real_times, nt, 1e-8)


def test_get_tempo_at_layer():
    """Test get_tempo_at_layer helper."""
    m = Meter(hierarchy=[[4, 4, 4, 4], 4], tempo=60)
    # Layer 0 tempo = internal tempo = 60
    assert m.get_tempo_at_layer(0) == 60
    # Layer 1 tempo = 60 * 4 = 240
    assert m.get_tempo_at_layer(1) == 240


def test_get_tempo_at_layer_out_of_bounds():
    """Test get_tempo_at_layer with invalid layer."""
    m = Meter(hierarchy=[4, 4], tempo=60)
    with pytest.raises(ValueError):
        m.get_tempo_at_layer(2)
    with pytest.raises(ValueError):
        m.get_tempo_at_layer(-1)


def test_get_hierarchy_mult():
    """Test _get_hierarchy_mult helper."""
    m = Meter(hierarchy=[[4, 4, 4, 4], 4])
    # Layer 0: [4,4,4,4] -> sum = 16
    assert m._get_hierarchy_mult(0) == 16
    # Layer 1: 4
    assert m._get_hierarchy_mult(1) == 4
    # Out of bounds returns 1
    assert m._get_hierarchy_mult(5) == 1


# Tala preset tests

def test_from_tala_tintal():
    """Test creating a Tintal meter from preset."""
    m = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    assert m.tala_name == TalaName.Tintal
    assert m.hierarchy == [[4, 4, 4, 4], 4]
    assert m.vibhaga == ['X', 2, 'O', 3]
    assert m.tempo == 60
    assert m.repetitions == 1


def test_from_tala_jhoomra():
    """Test creating a Jhoomra meter from preset."""
    m = Meter.from_tala(TalaName.Jhoomra, 0, 60, 2)
    assert m.tala_name == TalaName.Jhoomra
    assert m.hierarchy == [[3, 4, 3, 4], 4]
    assert m.vibhaga == ['X', 2, 'O', 3]
    assert m.repetitions == 2


def test_tala_serialization():
    """Test tala_name and vibhaga are preserved through serialization."""
    m = Meter.from_tala(TalaName.Ektal, 0, 60, 1)
    frozen = m.to_json()
    assert frozen['talaName'] == 'Ektal'
    assert frozen['vibhaga'] == ['X', 'O', 2, 'O', 3, 4]

    restored = Meter.from_json(frozen)
    assert restored.tala_name == TalaName.Ektal
    assert restored.vibhaga == ['X', 'O', 2, 'O', 3, 4]


# Segment boundary detection tests

def test_segment_boundary_indices_tintal():
    """Test getSegmentBoundaryIndices returns correct indices for Tintal."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    # Tintal [[4,4,4,4], 4] should have vibhag boundaries at 0, 4, 8, 12
    boundaries = meter.get_segment_boundary_indices()
    assert boundaries == [0, 4, 8, 12]


def test_segment_boundary_indices_jhoomra():
    """Test getSegmentBoundaryIndices returns correct indices for Jhoomra (asymmetric)."""
    meter = Meter.from_tala(TalaName.Jhoomra, 0, 60, 1)
    # Jhoomra [[3,4,3,4], 4] should have vibhag boundaries at 0, 3, 7, 10
    boundaries = meter.get_segment_boundary_indices()
    assert boundaries == [0, 3, 7, 10]


def test_segment_boundary_indices_multiple_cycles():
    """Test getSegmentBoundaryIndices handles multiple cycles."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 2)
    # 2 cycles of Tintal: boundaries at 0,4,8,12 and 16,20,24,28
    boundaries = meter.get_segment_boundary_indices()
    assert boundaries == [0, 4, 8, 12, 16, 20, 24, 28]


def test_segment_boundary_indices_simple_hierarchy():
    """Test getSegmentBoundaryIndices returns empty for simple hierarchy."""
    meter = Meter(hierarchy=[4, 4], tempo=60, start_time=0, repetitions=1)
    # Simple hierarchy [4, 4] has no compound layer, so no segment boundaries
    boundaries = meter.get_segment_boundary_indices()
    assert boundaries == []


def test_get_matra_pulses():
    """Test getMatraPulses returns correct number of pulses."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    # Tintal has 16 matras per cycle
    matra_pulses = meter.get_matra_pulses()
    assert len(matra_pulses) == 16


def test_is_segment_boundary():
    """Test isSegmentBoundary correctly identifies boundary pulses."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    matra_pulses = meter.get_matra_pulses()

    # Pulses at indices 0, 4, 8, 12 should be boundaries
    assert meter.is_segment_boundary(matra_pulses[0]) is True
    assert meter.is_segment_boundary(matra_pulses[4]) is True
    assert meter.is_segment_boundary(matra_pulses[8]) is True
    assert meter.is_segment_boundary(matra_pulses[12]) is True

    # Other pulses should not be boundaries
    assert meter.is_segment_boundary(matra_pulses[1]) is False
    assert meter.is_segment_boundary(matra_pulses[5]) is False
    assert meter.is_segment_boundary(matra_pulses[15]) is False


def test_get_segment_for_matra_index_tintal():
    """Test getSegmentForMatraIndex returns correct segment ranges for Tintal."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)

    # Index 0-3 should be in first segment
    assert meter.get_segment_for_matra_index(0) == {'start': 0, 'end': 4}
    assert meter.get_segment_for_matra_index(3) == {'start': 0, 'end': 4}

    # Index 4-7 should be in second segment
    assert meter.get_segment_for_matra_index(4) == {'start': 4, 'end': 8}
    assert meter.get_segment_for_matra_index(7) == {'start': 4, 'end': 8}

    # Index 12-15 should be in fourth segment
    assert meter.get_segment_for_matra_index(12) == {'start': 12, 'end': 16}
    assert meter.get_segment_for_matra_index(15) == {'start': 12, 'end': 16}


def test_get_segment_for_matra_index_jhoomra():
    """Test getSegmentForMatraIndex returns correct ranges for asymmetric Jhoomra."""
    meter = Meter.from_tala(TalaName.Jhoomra, 0, 60, 1)

    # First segment: 0-2 (3 matras)
    assert meter.get_segment_for_matra_index(0) == {'start': 0, 'end': 3}
    assert meter.get_segment_for_matra_index(2) == {'start': 0, 'end': 3}

    # Second segment: 3-6 (4 matras)
    assert meter.get_segment_for_matra_index(3) == {'start': 3, 'end': 7}
    assert meter.get_segment_for_matra_index(6) == {'start': 3, 'end': 7}

    # Third segment: 7-9 (3 matras)
    assert meter.get_segment_for_matra_index(7) == {'start': 7, 'end': 10}

    # Fourth segment: 10-13 (4 matras)
    assert meter.get_segment_for_matra_index(10) == {'start': 10, 'end': 14}


# Segment-aware pulse offset tests

def test_offset_segment_boundary_both_segments():
    """Test offsetSegmentBoundary resets and evenly spaces BOTH segments."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    matra_pulses = meter.get_matra_pulses()

    # Store the next boundary time (matra 8) - this should NOT move
    next_boundary_time = matra_pulses[8].real_time

    # Offset the second vibhag boundary (matra 4) by +0.5 seconds
    result = meter.offset_segment_boundary(matra_pulses[4], 0.5)
    assert result is True

    new_times_prev = [p.real_time for p in matra_pulses[:4]]
    new_times_next = [p.real_time for p in matra_pulses[5:8]]
    new_boundary_time = matra_pulses[4].real_time

    # The boundary pulse should have moved by +0.5s (from 4 to 4.5)
    assert pytest.approx(new_boundary_time, abs=0.001) == 4.5

    # The NEXT vibhag boundary (matra 8) should NOT have moved
    assert pytest.approx(matra_pulses[8].real_time, abs=0.001) == next_boundary_time

    # Matra 0 (the previous boundary) should NOT have moved
    assert pytest.approx(new_times_prev[0], abs=0.001) == 0

    # PREVIOUS segment: 4s -> 4.5s (expands)
    # Matras 1, 2, 3 should be EVENLY SPACED in the new 4.5s segment
    # 4 pulses in segment, so spacing is 4.5/4 = 1.125s
    assert pytest.approx(new_times_prev[1], abs=0.001) == 1.125
    assert pytest.approx(new_times_prev[2], abs=0.001) == 2.25
    assert pytest.approx(new_times_prev[3], abs=0.001) == 3.375

    # NEXT segment: 4s -> 3.5s (compresses)
    # Matras 5, 6, 7 should be EVENLY SPACED in the new 3.5s segment
    # 4 pulses in segment (including boundary at start), so spacing is 3.5/4 = 0.875s
    assert pytest.approx(new_times_next[0], abs=0.001) == 4.5 + 0.875       # matra 5 at 5.375
    assert pytest.approx(new_times_next[1], abs=0.001) == 4.5 + 0.875 * 2  # matra 6 at 6.25
    assert pytest.approx(new_times_next[2], abs=0.001) == 4.5 + 0.875 * 3  # matra 7 at 7.125


def test_offset_segment_boundary_resets_manual_adjustments():
    """Test offsetSegmentBoundary resets any previous manual adjustments."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    matra_pulses = meter.get_matra_pulses()

    # First, manually offset matra 5 (an internal pulse)
    meter._offset_pulse_direct(matra_pulses[5], 0.3)
    assert pytest.approx(matra_pulses[5].real_time, abs=0.001) == 5.3

    # Now nudge the vibhag boundary at matra 4
    meter.offset_segment_boundary(matra_pulses[4], 0.5)

    # Matra 5 should be reset to evenly-spaced position, NOT 5.3 + some offset
    # New segment is 3.5s (from 4.5 to 8), with 4 pulses, spacing = 0.875s
    assert pytest.approx(matra_pulses[5].real_time, abs=0.001) == 4.5 + 0.875  # 5.375


def test_offset_segment_boundary_returns_false_for_first_boundary():
    """Test offsetSegmentBoundary returns false for first boundary (matra 0)."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    matra_pulses = meter.get_matra_pulses()

    # Matra 0 is the first boundary - there's no previous segment to adjust
    result = meter.offset_segment_boundary(matra_pulses[0], 0.5)
    assert result is False


def test_offset_segment_boundary_returns_false_for_non_boundary():
    """Test offsetSegmentBoundary returns false for non-boundary pulse."""
    meter = Meter.from_tala(TalaName.Tintal, 0, 60, 1)
    matra_pulses = meter.get_matra_pulses()

    # Matra 5 is not a boundary
    result = meter.offset_segment_boundary(matra_pulses[5], 0.5)
    assert result is False


def test_offset_segment_boundary_returns_false_for_simple_hierarchy():
    """Test offsetSegmentBoundary returns false for simple hierarchy meter."""
    meter = Meter(hierarchy=[4, 4], tempo=60, start_time=0, repetitions=1)
    matra_pulses = meter.get_matra_pulses()

    # No segment boundaries in simple hierarchy
    result = meter.offset_segment_boundary(matra_pulses[0], 0.5)
    assert result is False


def test_offset_segment_boundary_jhoomra():
    """Test offsetSegmentBoundary works with asymmetric Jhoomra."""
    meter = Meter.from_tala(TalaName.Jhoomra, 0, 60, 1)
    matra_pulses = meter.get_matra_pulses()

    # Jhoomra: [[3,4,3,4], 4] - vibhag boundaries at 0, 3, 7, 10
    # Store the next boundary time (matra 7) - this should NOT move
    next_boundary_time = matra_pulses[7].real_time

    # Offset the second vibhag boundary (matra 3) by +0.25 seconds
    result = meter.offset_segment_boundary(matra_pulses[3], 0.25)
    assert result is True

    new_times_prev = [p.real_time for p in matra_pulses[:3]]
    new_times_next = [p.real_time for p in matra_pulses[4:7]]
    new_boundary_time = matra_pulses[3].real_time

    # Boundary should have moved by +0.25s (from 3 to 3.25)
    assert pytest.approx(new_boundary_time, abs=0.001) == 3.25

    # Next boundary (matra 7) should NOT have moved
    assert pytest.approx(matra_pulses[7].real_time, abs=0.001) == next_boundary_time

    # Matra 0 should NOT have moved
    assert pytest.approx(new_times_prev[0], abs=0.001) == 0

    # PREVIOUS segment: 3s -> 3.25s (expands)
    # 3 pulses in segment, so spacing is 3.25/3 ≈ 1.0833s
    prev_spacing = 3.25 / 3
    assert pytest.approx(new_times_prev[1], abs=0.001) == prev_spacing
    assert pytest.approx(new_times_prev[2], abs=0.001) == prev_spacing * 2

    # NEXT segment: 4s -> 3.75s (compresses)
    # 4 pulses in segment (including boundary), so spacing is 3.75/4 = 0.9375s
    next_spacing = 3.75 / 4
    assert pytest.approx(new_times_next[0], abs=0.001) == 3.25 + next_spacing      # matra 4
    assert pytest.approx(new_times_next[1], abs=0.001) == 3.25 + next_spacing * 2  # matra 5
    assert pytest.approx(new_times_next[2], abs=0.001) == 3.25 + next_spacing * 3  # matra 6


def test_pulse_lowest_layer():
    """Test Pulse.lowest_layer property."""
    # Pulse with no affiliations
    p1 = Pulse()
    assert p1.lowest_layer == 0

    # Pulse with single affiliation
    p2 = Pulse(affiliations=[{'layer': 1, 'psId': 'test'}])
    assert p2.lowest_layer == 1

    # Pulse with multiple affiliations
    p3 = Pulse(affiliations=[
        {'layer': 2, 'psId': 'a'},
        {'layer': 0, 'psId': 'b'},
        {'layer': 1, 'psId': 'c'}
    ])
    assert p3.lowest_layer == 0
