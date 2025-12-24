"""Sequence matching utilities for query analysis.

This module provides exact Python ports of the TypeScript sequence matching
functions used in the query system.
"""

from typing import List, Dict, Optional, Tuple


def find_sequence_indexes(sequence: List[int], longer_sequence: List[int]) -> List[int]:
    """Find all starting indexes where sequence appears in longer_sequence.
    
    This is an exact port of the TypeScript findSequenceIndexes function.
    
    Args:
        sequence: The sequence to search for
        longer_sequence: The sequence to search in
        
    Returns:
        List of starting indexes where the sequence is found
    """
    indexes: List[int] = []
    
    if not sequence or not longer_sequence:
        return indexes
        
    start_index = -1
    try:
        start_index = longer_sequence.index(sequence[0])
    except ValueError:
        return indexes
    
    if start_index != -1:
        # Check first potential match
        match = True
        for i in range(1, len(sequence)):
            if start_index + i >= len(longer_sequence) or longer_sequence[start_index + i] != sequence[i]:
                match = False
                break
        
        if match:
            indexes.append(start_index)
        
        # Check remaining potential matches
        for i in range(start_index + 1, len(longer_sequence)):
            if longer_sequence[i] == sequence[0]:
                match = True
                for j in range(1, len(sequence)):
                    if i + j >= len(longer_sequence) or longer_sequence[i + j] != sequence[j]:
                        match = False
                        break
                
                if match:
                    indexes.append(i)
    
    return indexes


def loose_sequence_indexes(
    sequence: List[int], 
    longer_sequence: List[int]
) -> Dict[str, Optional[int] | bool]:
    """Test if sequence appears loosely (in order but not necessarily consecutively) in longer_sequence.
    
    This is an exact port of the TypeScript testLooseSequenceIndexes function.
    
    Args:
        sequence: The sequence to search for
        longer_sequence: The sequence to search in
        
    Returns:
        Dictionary with keys:
        - 'truth': Whether the sequence was found
        - 'first_idx': Index of first element match (None if not found)
        - 'last_idx': Index of last element match (None if not found)
    """
    ct = 0
    out = False
    first_idx: Optional[int] = None
    last_idx: Optional[int] = None
    
    if not sequence or not longer_sequence:
        return {"truth": out, "first_idx": first_idx, "last_idx": last_idx}
    
    for i in range(len(longer_sequence)):
        el = longer_sequence[i]
        
        if ct < len(sequence) and el == sequence[ct]:
            if ct == 0:
                first_idx = i
            ct += 1
        
        if ct > len(sequence) - 1:
            out = True
            last_idx = i
            break
    
    return {"truth": out, "first_idx": first_idx, "last_idx": last_idx}


def split_trajs_by_silences(trajectories: List) -> List[List]:
    """Split trajectory list by silences (trajectory ID 12).
    
    This is a port of the TypeScript splitTrajsBySilences method.
    
    Args:
        trajectories: List of trajectory objects
        
    Returns:
        List of trajectory sublists split by silence markers
    """
    result = [[]]
    
    for traj in trajectories:
        # Check if trajectory has ID 12 (silence marker)
        traj_id = getattr(traj, 'id', None)
        if traj_id == 12:
            result.append([])
        else:
            if len(result) == 0:
                result.append([])
            result[-1].append(traj)
    
    # Filter out empty sublists
    return [traj_seq for traj_seq in result if len(traj_seq) > 0]