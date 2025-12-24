"""Musical transcription query system.

This module provides a comprehensive query system for analyzing musical 
transcriptions, with exact compatibility to the TypeScript implementation.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Union, Any, Tuple
import json

from .classes.piece import Piece
from .classes.trajectory import Trajectory
from .classes.pitch import Pitch
from .enums import Instrument
from .query_types import (
    CategoryType, DesignatorType, SegmentationType, QueryType,
    QueryAnswerType, MultipleReturnType, MultipleOptionType
)
from .sequence_utils import find_sequence_indexes, loose_sequence_indexes, split_trajs_by_silences


class Query:
    """Query system for musical transcription analysis.
    
    This class provides sophisticated filtering and analysis capabilities
    for musical transcriptions, maintaining exact compatibility with the
    TypeScript implementation.
    """
    
    def __init__(self, piece: Piece, options: Optional[Dict[str, Any]] = None):
        """Initialize a new Query instance.
        
        Args:
            piece: The Piece object to query
            options: Query configuration options
        """
        opts = options or {}
        
        # Core properties
        self.piece = piece
        self.trajectories: List[List[Trajectory]] = []
        self.phrase_idxs: List[int] = []
        self.instrument_idx: int = opts.get("instrument_idx", 0)
        self.identifier: List[Union[int, str, Dict[str, int]]] = []
        self.stringified_identifier: List[str] = []
        self.sequence_length: Optional[int] = opts.get("sequence_length")
        self.repetition: bool = False
        self.start_times: List[float] = []
        
        # Query parameters
        self.designator = DesignatorType(opts.get("designator", "includes"))
        self.category = CategoryType(opts.get("category", "trajectoryID"))
        self.segmentation = SegmentationType(opts.get("segmentation", "phrase"))
        self.max_dur: float = opts.get("max_dur", 60.0)
        self.min_dur: float = opts.get("min_dur", 0.0)
        
        # Category-specific parameters
        self.consonant: Optional[str] = opts.get("consonant")
        self.vowel: Optional[str] = opts.get("vowel")
        self.trajectory_id: Optional[int] = opts.get("trajectory_id")
        self.pitch: Optional[Pitch] = opts.get("pitch")
        self.pitch_sequence: Optional[List[Pitch]] = opts.get("pitch_sequence")
        self.traj_id_sequence: Optional[List[int]] = opts.get("traj_id_sequence")
        
        # Section categorization parameters
        self.section_top_level: Optional[str] = opts.get("section_top_level")
        self.alap_section: Optional[str] = opts.get("alap_section")
        self.comp_type: Optional[str] = opts.get("comp_type")
        self.comp_sec_tempo: Optional[str] = opts.get("comp_sec_tempo")
        self.tala: Optional[str] = opts.get("tala")
        
        # Phrase categorization parameters
        self.phrase_type: Optional[str] = opts.get("phrase_type")
        self.elaboration_type: Optional[str] = opts.get("elaboration_type")
        self.vocal_art_type: Optional[str] = opts.get("vocal_art_type")
        self.inst_art_type: Optional[str] = opts.get("inst_art_type")
        self.incidental: Optional[str] = opts.get("incidental")
        
        # Validate parameters and execute query
        self._validate_parameters()
        self._execute_filters()
        self._filter_by_duration()
        self._generate_identifiers()
        self._calculate_start_times()
    
    def _validate_parameters(self) -> None:
        """Validate query parameters based on category and other constraints."""
        # Instrument index validation
        if self.instrument_idx < 0 or self.instrument_idx >= len(self.piece.instrumentation):
            raise ValueError(f"instrument_idx {self.instrument_idx} is out of range. Piece has {len(self.piece.instrumentation)} instruments (valid indices: 0-{len(self.piece.instrumentation)-1})")
        
        # Sequence length validation
        if self.segmentation == SegmentationType.SEQUENCE_OF_TRAJECTORIES:
            if self.sequence_length is None:
                raise ValueError("sequence_length is required when segmentation is sequenceOfTrajectories")
        
        # Category-specific validation
        consonant_categories = {
            CategoryType.STARTING_CONSONANT, 
            CategoryType.ENDING_CONSONANT, 
            CategoryType.ANY_CONSONANT
        }
        
        section_query = False
        
        if self.category == CategoryType.PITCH:
            if self.pitch is None:
                raise ValueError("pitch is required when category is pitch")
        elif self.category == CategoryType.TRAJECTORY_ID:
            if self.trajectory_id is None:
                raise ValueError("trajectory_id is required when category is trajectoryID")
        elif self.category == CategoryType.VOWEL:
            inst = self.piece.instrumentation[self.instrument_idx]
            if inst not in [Instrument.Vocal_F, Instrument.Vocal_M]:
                raise ValueError("category vowel is only for vocal instruments")
            if self.vowel is None:
                raise ValueError("vowel is required when category is vowel")
        elif self.category in consonant_categories:
            inst = self.piece.instrumentation[self.instrument_idx]
            if inst not in [Instrument.Vocal_F, Instrument.Vocal_M]:
                raise ValueError("category consonant is only for vocal instruments")
            if self.consonant is None:
                raise ValueError("consonant is required when category is consonant")
        elif self.category in [CategoryType.PITCH_SEQUENCE_STRICT, CategoryType.PITCH_SEQUENCE_LOOSE]:
            if self.pitch_sequence is None:
                raise ValueError("pitch_sequence is required")
        elif self.category in [CategoryType.TRAJ_SEQUENCE_STRICT, CategoryType.TRAJ_SEQUENCE_LOOSE]:
            if self.traj_id_sequence is None:
                raise ValueError("traj_id_sequence is required")
        elif self.category == CategoryType.SECTION_TOP_LEVEL:
            if self.section_top_level is None:
                raise ValueError("section_top_level is required")
            section_query = True
        elif self.category == CategoryType.ALAP_SECTION:
            if self.alap_section is None:
                raise ValueError("alap_section is required")
            section_query = True
        elif self.category == CategoryType.COMP_TYPE:
            if self.comp_type is None:
                raise ValueError("comp_type is required")
            section_query = True
        elif self.category == CategoryType.COMP_SEC_TEMPO:
            if self.comp_sec_tempo is None:
                raise ValueError("comp_sec_tempo is required")
            section_query = True
        elif self.category == CategoryType.TALA:
            if self.tala is None:
                raise ValueError("tala is required")
            section_query = True
        
        # Section query constraints
        if section_query:
            if self.designator in [DesignatorType.ENDS_WITH, DesignatorType.STARTS_WITH]:
                raise ValueError("Section queries cannot be used with startsWith or endsWith")
            if self.segmentation in [
                SegmentationType.SEQUENCE_OF_TRAJECTORIES,
                SegmentationType.CONNECTED_SEQUENCE_OF_TRAJECTORIES
            ]:
                raise ValueError("Section queries cannot be used with trajectory sequence segmentation")
    
    def _execute_filters(self) -> None:
        """Execute the appropriate filter based on segmentation type."""
        if self.segmentation == SegmentationType.PHRASE:
            self._phrase_filter()
        elif self.segmentation == SegmentationType.GROUP:
            self._group_filter()
        elif self.segmentation == SegmentationType.SEQUENCE_OF_TRAJECTORIES:
            self._sequence_of_trajectories_filter()
        elif self.segmentation == SegmentationType.CONNECTED_SEQUENCE_OF_TRAJECTORIES:
            self._connected_sequence_of_trajectories_filter()
    
    def _phrase_filter(self) -> None:
        """Filter phrases based on query criteria."""
        phrases = self.piece.phrase_grid[self.instrument_idx]
        filtered_phrases = []
        
        for phrase in phrases:
            if self._test_phrase_match(phrase):
                filtered_phrases.append(phrase)
        
        self.trajectories = [phrase.trajectories for phrase in filtered_phrases]
        self.identifier = [phrase.piece_idx for phrase in filtered_phrases if phrase.piece_idx is not None]
    
    def _group_filter(self) -> None:
        """Filter groups based on query criteria."""
        groups = self.piece.all_groups({"instrument_idx": self.instrument_idx})
        filtered_groups = []
        
        for group in groups:
            if self._test_group_match(group):
                filtered_groups.append(group)
        
        self.trajectories = [group.trajectories for group in filtered_groups]
        for group in filtered_groups:
            self.identifier.append(group.id)
    
    def _sequence_of_trajectories_filter(self) -> None:
        """Filter sequences of trajectories based on query criteria."""
        all_trajs = self.piece.all_trajectories(self.instrument_idx)
        
        for i in range(len(all_trajs) - self.sequence_length + 1):
            traj_seq = all_trajs[i:i + self.sequence_length]
            
            if self._test_trajectory_sequence_match(traj_seq):
                self.trajectories.append(traj_seq)
                id_obj = {
                    "phrase_idx": traj_seq[0].phrase_idx,
                    "traj_idx": traj_seq[0].num
                }
                self.identifier.append(id_obj)
    
    def _connected_sequence_of_trajectories_filter(self) -> None:
        """Filter connected sequences of trajectories (split by silences)."""
        all_trajs = self.piece.all_trajectories(self.instrument_idx)
        split_trajs = split_trajs_by_silences(all_trajs)
        
        for traj_seq in split_trajs:
            if self._test_trajectory_sequence_match(traj_seq):
                self.trajectories.append(traj_seq)
                id_obj = {
                    "phrase_idx": traj_seq[0].phrase_idx,
                    "traj_idx": traj_seq[0].num
                }
                self.identifier.append(id_obj)
    
    def _test_phrase_match(self, phrase) -> bool:
        """Test if a phrase matches the query criteria."""
        if self.category == CategoryType.PITCH:
            trial_arr = [pitch.numbered_pitch for pitch in phrase.all_pitches(self.repetition)]
            return self._pitch_diff(self.pitch, trial_arr)
        elif self.category == CategoryType.TRAJECTORY_ID:
            return self._traj_id_diff(self.trajectory_id, phrase.trajectories)
        elif self.category == CategoryType.VOWEL:
            trial_arr = [traj.vowel for traj in phrase.trajectories]
            return self._vowel_diff(self.vowel, trial_arr)
        elif self.category == CategoryType.STARTING_CONSONANT:
            trial_arr = [traj.start_consonant for traj in phrase.trajectories]
            return self._consonant_diff(self.consonant, trial_arr)
        elif self.category == CategoryType.ENDING_CONSONANT:
            trial_arr = [traj.end_consonant for traj in phrase.trajectories]
            return self._consonant_diff(self.consonant, trial_arr)
        elif self.category == CategoryType.ANY_CONSONANT:
            trial_arr = []
            for traj in phrase.trajectories:
                trial_arr.extend([traj.start_consonant, traj.end_consonant])
            return self._consonant_diff(self.consonant, trial_arr)
        elif self.category == CategoryType.PITCH_SEQUENCE_STRICT:
            trial_arr = [pitch.numbered_pitch for pitch in phrase.all_pitches(self.repetition)]
            return self._pitch_seq_strict_diff(self.pitch_sequence, trial_arr)
        elif self.category == CategoryType.PITCH_SEQUENCE_LOOSE:
            trial_arr = [pitch.numbered_pitch for pitch in phrase.all_pitches(self.repetition)]
            return self._pitch_seq_loose_diff(self.pitch_sequence, trial_arr)
        elif self.category == CategoryType.TRAJ_SEQUENCE_STRICT:
            trial_arr = [traj.id for traj in phrase.trajectories]
            return self._traj_seq_strict_diff(self.traj_id_sequence, trial_arr)
        elif self.category == CategoryType.TRAJ_SEQUENCE_LOOSE:
            trial_arr = [traj.id for traj in phrase.trajectories]
            return self._traj_seq_loose_diff(self.traj_id_sequence, trial_arr)
        elif self.category == CategoryType.SECTION_TOP_LEVEL:
            p_idx = phrase.piece_idx
            return self._sec_top_level_diff(p_idx)
        elif self.category == CategoryType.ALAP_SECTION:
            p_idx = phrase.piece_idx
            return self._alap_section_diff(p_idx)
        elif self.category == CategoryType.COMP_TYPE:
            p_idx = phrase.piece_idx
            return self._comp_type_diff(p_idx)
        elif self.category == CategoryType.COMP_SEC_TEMPO:
            p_idx = phrase.piece_idx
            return self._comp_sec_tempo_diff(p_idx)
        elif self.category == CategoryType.TALA:
            p_idx = phrase.piece_idx
            return self._tala_diff(p_idx)
        elif self.category in [
            CategoryType.PHRASE_TYPE,
            CategoryType.ELABORATION_TYPE,
            CategoryType.VOCAL_ART_TYPE,
            CategoryType.INST_ART_TYPE,
            CategoryType.INCIDENTAL
        ]:
            p_idx = phrase.piece_idx
            return self._phrase_label_diff(p_idx)
        
        return False
    
    def _test_group_match(self, group) -> bool:
        """Test if a group matches the query criteria."""
        # Similar logic to phrase match but for groups
        # This would need to be implemented based on the group structure
        # For now, return False as placeholder
        return False
    
    def _test_trajectory_sequence_match(self, traj_seq: List[Trajectory]) -> bool:
        """Test if a trajectory sequence matches the query criteria."""
        if self.category == CategoryType.PITCH:
            pitches = []
            for traj in traj_seq:
                pitches.extend(traj.pitches)
            n_pitches = [pitch.numbered_pitch for pitch in pitches]
            if not self.repetition:
                n_pitches = self._remove_consecutive_duplicates(n_pitches)
            return self._pitch_diff(self.pitch, n_pitches)
        elif self.category == CategoryType.TRAJECTORY_ID:
            return self._traj_id_diff(self.trajectory_id, traj_seq)
        elif self.category == CategoryType.VOWEL:
            vowels = [traj.vowel for traj in traj_seq]
            return self._vowel_diff(self.vowel, vowels)
        elif self.category == CategoryType.STARTING_CONSONANT:
            consonants = [traj.start_consonant for traj in traj_seq]
            return self._consonant_diff(self.consonant, consonants)
        elif self.category == CategoryType.ENDING_CONSONANT:
            consonants = [traj.end_consonant for traj in traj_seq]
            return self._consonant_diff(self.consonant, consonants)
        elif self.category == CategoryType.ANY_CONSONANT:
            consonants = []
            for traj in traj_seq:
                consonants.extend([traj.start_consonant, traj.end_consonant])
            return self._consonant_diff(self.consonant, consonants)
        elif self.category == CategoryType.PITCH_SEQUENCE_STRICT:
            pitches = []
            for traj in traj_seq:
                pitches.extend(traj.pitches)
            n_pitches = [pitch.numbered_pitch for pitch in pitches]
            if not self.repetition:
                n_pitches = self._remove_consecutive_duplicates(n_pitches)
            return self._pitch_seq_strict_diff(self.pitch_sequence, n_pitches)
        elif self.category == CategoryType.PITCH_SEQUENCE_LOOSE:
            pitches = []
            for traj in traj_seq:
                pitches.extend(traj.pitches)
            n_pitches = [pitch.numbered_pitch for pitch in pitches]
            if not self.repetition:
                n_pitches = self._remove_consecutive_duplicates(n_pitches)
            return self._pitch_seq_loose_diff(self.pitch_sequence, n_pitches)
        elif self.category == CategoryType.TRAJ_SEQUENCE_STRICT:
            traj_ids = [traj.id for traj in traj_seq]
            return self._traj_seq_strict_diff(self.traj_id_sequence, traj_ids)
        elif self.category == CategoryType.TRAJ_SEQUENCE_LOOSE:
            traj_ids = [traj.id for traj in traj_seq]
            return self._traj_seq_loose_diff(self.traj_id_sequence, traj_ids)
        elif self.category == CategoryType.SECTION_TOP_LEVEL:
            raise ValueError("section_top_level cannot be used with trajectory sequence segmentation")
        
        return False
    
    @staticmethod
    def _remove_consecutive_duplicates(sequence: List[int]) -> List[int]:
        """Remove consecutive duplicate values from a sequence."""
        if not sequence:
            return []
        
        result = [sequence[0]]
        for i in range(1, len(sequence)):
            if sequence[i] != sequence[i-1]:
                result.append(sequence[i])
        return result
    
    # ---- Diff methods for different query types ----
    
    def _pitch_diff(self, pitch: Pitch, n_pitches: List[int]) -> bool:
        """Test pitch criteria against a list of numbered pitches."""
        boolean = False
        
        if self.designator == DesignatorType.INCLUDES:
            boolean = pitch.numbered_pitch in n_pitches
        elif self.designator == DesignatorType.EXCLUDES:
            boolean = pitch.numbered_pitch not in n_pitches
        elif self.designator == DesignatorType.STARTS_WITH:
            boolean = len(n_pitches) > 0 and n_pitches[0] == pitch.numbered_pitch
        elif self.designator == DesignatorType.ENDS_WITH:
            boolean = len(n_pitches) > 0 and n_pitches[-1] == pitch.numbered_pitch
        
        return boolean
    
    def _pitch_seq_strict_diff(self, pitch_seq: List[Pitch], n_pitches: List[int]) -> bool:
        """Test strict pitch sequence criteria."""
        boolean = False
        num_pitch_seq = [pitch.numbered_pitch for pitch in pitch_seq]
        
        if self.designator == DesignatorType.INCLUDES:
            boolean = len(find_sequence_indexes(num_pitch_seq, n_pitches)) > 0
        elif self.designator == DesignatorType.EXCLUDES:
            boolean = len(find_sequence_indexes(num_pitch_seq, n_pitches)) == 0
        elif self.designator == DesignatorType.STARTS_WITH:
            if len(num_pitch_seq) <= len(n_pitches):
                boolean = all(num_pitch_seq[i] == n_pitches[i] for i in range(len(num_pitch_seq)))
        elif self.designator == DesignatorType.ENDS_WITH:
            if len(num_pitch_seq) <= len(n_pitches):
                start_idx = len(n_pitches) - len(num_pitch_seq)
                boolean = all(num_pitch_seq[i] == n_pitches[start_idx + i] for i in range(len(num_pitch_seq)))
        
        return boolean
    
    def _pitch_seq_loose_diff(self, pitch_seq: List[Pitch], n_pitches: List[int]) -> bool:
        """Test loose pitch sequence criteria."""
        boolean = False
        num_pitch_seq = [pitch.numbered_pitch for pitch in pitch_seq]
        
        if self.designator == DesignatorType.INCLUDES:
            loose_obj = loose_sequence_indexes(num_pitch_seq, n_pitches)
            boolean = loose_obj["truth"]
        elif self.designator == DesignatorType.EXCLUDES:
            loose_obj = loose_sequence_indexes(num_pitch_seq, n_pitches)
            boolean = not loose_obj["truth"]
        elif self.designator == DesignatorType.STARTS_WITH:
            loose_obj = loose_sequence_indexes(num_pitch_seq, n_pitches)
            boolean = loose_obj["truth"] and loose_obj["first_idx"] == 0
        elif self.designator == DesignatorType.ENDS_WITH:
            loose_obj = loose_sequence_indexes(num_pitch_seq, n_pitches)
            boolean = loose_obj["truth"] and loose_obj["last_idx"] == len(n_pitches) - 1
        
        return boolean
    
    def _traj_seq_strict_diff(self, traj_id_seq: List[int], full_traj_list: List[int]) -> bool:
        """Test strict trajectory sequence criteria."""
        boolean = False
        
        if self.designator == DesignatorType.INCLUDES:
            boolean = len(find_sequence_indexes(traj_id_seq, full_traj_list)) > 0
        elif self.designator == DesignatorType.EXCLUDES:
            boolean = len(find_sequence_indexes(traj_id_seq, full_traj_list)) == 0
        elif self.designator == DesignatorType.STARTS_WITH:
            indexes = find_sequence_indexes(traj_id_seq, full_traj_list)
            boolean = len(indexes) > 0 and indexes[0] == 0
        elif self.designator == DesignatorType.ENDS_WITH:
            start_idx = len(full_traj_list) - len(traj_id_seq)
            indexes = find_sequence_indexes(traj_id_seq, full_traj_list)
            boolean = len(indexes) > 0 and indexes[0] == start_idx
        
        return boolean
    
    def _traj_seq_loose_diff(self, traj_id_seq: List[int], full_traj_list: List[int]) -> bool:
        """Test loose trajectory sequence criteria."""
        boolean = False
        
        if self.designator == DesignatorType.INCLUDES:
            loose_obj = loose_sequence_indexes(traj_id_seq, full_traj_list)
            boolean = loose_obj["truth"]
        elif self.designator == DesignatorType.EXCLUDES:
            loose_obj = loose_sequence_indexes(traj_id_seq, full_traj_list)
            boolean = not loose_obj["truth"]
        elif self.designator == DesignatorType.STARTS_WITH:
            loose_obj = loose_sequence_indexes(traj_id_seq, full_traj_list)
            boolean = loose_obj["truth"] and loose_obj["first_idx"] == 0
        elif self.designator == DesignatorType.ENDS_WITH:
            loose_obj = loose_sequence_indexes(traj_id_seq, full_traj_list)
            boolean = loose_obj["truth"] and loose_obj["last_idx"] == len(full_traj_list) - 1
        
        return boolean
    
    def _traj_id_diff(self, traj_id: int, trajectories: List[Trajectory]) -> bool:
        """Test trajectory ID criteria against a list of trajectories."""
        boolean = False
        
        if self.designator == DesignatorType.INCLUDES:
            boolean = any(traj.id == traj_id for traj in trajectories)
        elif self.designator == DesignatorType.EXCLUDES:
            boolean = not any(traj.id == traj_id for traj in trajectories)
        elif self.designator == DesignatorType.STARTS_WITH:
            boolean = len(trajectories) > 0 and trajectories[0].id == traj_id
        elif self.designator == DesignatorType.ENDS_WITH:
            boolean = len(trajectories) > 0 and trajectories[-1].id == traj_id
        
        return boolean
    
    def _vowel_diff(self, vowel: str, vowels: List[Optional[str]]) -> bool:
        """Test vowel criteria against a list of vowels."""
        boolean = False
        
        if self.designator == DesignatorType.INCLUDES:
            boolean = vowel in vowels
        elif self.designator == DesignatorType.EXCLUDES:
            boolean = vowel not in vowels
        elif self.designator == DesignatorType.STARTS_WITH:
            boolean = len(vowels) > 0 and vowels[0] == vowel
        elif self.designator == DesignatorType.ENDS_WITH:
            boolean = len(vowels) > 0 and vowels[-1] == vowel
        
        return boolean
    
    def _consonant_diff(self, consonant: str, consonants: List[Optional[str]]) -> bool:
        """Test consonant criteria against a list of consonants."""
        boolean = False
        
        if self.designator == DesignatorType.INCLUDES:
            boolean = consonant in consonants
        elif self.designator == DesignatorType.EXCLUDES:
            boolean = consonant not in consonants
        elif self.designator == DesignatorType.STARTS_WITH:
            boolean = len(consonants) > 0 and consonants[0] == consonant
        # Note: endsWith is not implemented for consonants in TypeScript version
        
        return boolean
    
    def _sec_top_level_diff(self, p_idx: int) -> bool:
        """Test section top level criteria."""
        boolean = False
        s_idx = self.piece.s_idx_from_p_idx(p_idx, self.instrument_idx)
        if s_idx is not None and self.piece.sections:
            section = self.piece.sections[s_idx]
            if self.designator == DesignatorType.INCLUDES:
                boolean = section.categorization.get("Top Level") == self.section_top_level
            elif self.designator == DesignatorType.EXCLUDES:
                boolean = section.categorization.get("Top Level") != self.section_top_level
        
        return boolean
    
    def _alap_section_diff(self, p_idx: int) -> bool:
        """Test alap section criteria."""
        boolean = False
        s_idx = self.piece.s_idx_from_p_idx(p_idx)
        if s_idx is not None and self.piece.sections:
            section = self.piece.sections[s_idx]
            alap_cat = section.categorization.get("Alap", {})
            if self.designator == DesignatorType.INCLUDES:
                boolean = alap_cat.get(self.alap_section, False)
            elif self.designator == DesignatorType.EXCLUDES:
                boolean = not alap_cat.get(self.alap_section, False)
        
        return boolean
    
    def _comp_type_diff(self, p_idx: int) -> bool:
        """Test composition type criteria."""
        boolean = False
        s_idx = self.piece.s_idx_from_p_idx(p_idx)
        if s_idx is not None and self.piece.sections:
            section = self.piece.sections[s_idx]
            comp_cat = section.categorization.get("Composition Type", {})
            if self.designator == DesignatorType.INCLUDES:
                boolean = comp_cat.get(self.comp_type, False)
            elif self.designator == DesignatorType.EXCLUDES:
                boolean = not comp_cat.get(self.comp_type, False)
        
        return boolean
    
    def _comp_sec_tempo_diff(self, p_idx: int) -> bool:
        """Test composition section/tempo criteria."""
        boolean = False
        s_idx = self.piece.s_idx_from_p_idx(p_idx)
        if s_idx is not None and self.piece.sections:
            section = self.piece.sections[s_idx]
            comp_sec_tempo_cat = section.categorization.get("Comp.-section/Tempo", {})
            if self.designator == DesignatorType.INCLUDES:
                boolean = comp_sec_tempo_cat.get(self.comp_sec_tempo, False)
            elif self.designator == DesignatorType.EXCLUDES:
                boolean = not comp_sec_tempo_cat.get(self.comp_sec_tempo, False)
        
        return boolean
    
    def _tala_diff(self, p_idx: int) -> bool:
        """Test tala criteria."""
        boolean = False
        s_idx = self.piece.s_idx_from_p_idx(p_idx)
        if s_idx is not None and self.piece.sections:
            section = self.piece.sections[s_idx]
            tala_cat = section.categorization.get("Tala", {})
            if self.designator == DesignatorType.INCLUDES:
                boolean = tala_cat.get(self.tala, False)
            elif self.designator == DesignatorType.EXCLUDES:
                boolean = not tala_cat.get(self.tala, False)
        
        return boolean
    
    def _phrase_label_diff(self, p_idx: int) -> bool:
        """Test phrase label criteria."""
        boolean = False
        
        if p_idx < len(self.piece.phrases):
            phrase = self.piece.phrases[p_idx]
            if hasattr(phrase, 'categorization_grid') and phrase.categorization_grid:
                cat = phrase.categorization_grid[0]
                
                if self.category == CategoryType.PHRASE_TYPE:
                    boolean = cat.get("Phrase", {}).get(self.phrase_type, False)
                elif self.category == CategoryType.ELABORATION_TYPE:
                    boolean = cat.get("Elaboration", {}).get(self.elaboration_type, False)
                elif self.category == CategoryType.VOCAL_ART_TYPE:
                    boolean = cat.get("Vocal Articulation", {}).get(self.vocal_art_type, False)
                elif self.category == CategoryType.INST_ART_TYPE:
                    boolean = cat.get("Instrumental Articulation", {}).get(self.inst_art_type, False)
                elif self.category == CategoryType.INCIDENTAL:
                    boolean = cat.get("Incidental", {}).get(self.incidental, False)
                
                if self.designator == DesignatorType.EXCLUDES:
                    boolean = not boolean
        
        return boolean
    
    # ---- Helper methods ----
    
    def _filter_by_duration(self) -> None:
        """Filter results by duration constraints."""
        remove_idxs = []
        
        for t_idx, traj_seq in enumerate(self.trajectories):
            if not traj_seq:
                continue
                
            first_phrase_idx = traj_seq[0].phrase_idx
            if first_phrase_idx is None or first_phrase_idx >= len(self.piece.phrases):
                continue
                
            first_phrase = self.piece.phrases[first_phrase_idx]
            start = traj_seq[0].start_time + (first_phrase.start_time or 0)
            
            last_phrase_idx = traj_seq[-1].phrase_idx
            if last_phrase_idx is None or last_phrase_idx >= len(self.piece.phrases):
                continue
                
            last_phrase = self.piece.phrases[last_phrase_idx]
            end = traj_seq[-1].end_time + (last_phrase.start_time or 0)
            
            duration = end - start
            
            if duration > self.max_dur or duration < self.min_dur:
                remove_idxs.append(t_idx)
        
        # Remove filtered items
        self.trajectories = [
            traj_seq for t_idx, traj_seq in enumerate(self.trajectories) 
            if t_idx not in remove_idxs
        ]
        self.identifier = [
            identifier for t_idx, identifier in enumerate(self.identifier) 
            if t_idx not in remove_idxs
        ]
    
    def _generate_identifiers(self) -> None:
        """Generate stringified identifiers for results."""
        self.stringified_identifier = [json.dumps(identifier) for identifier in self.identifier]
    
    def _calculate_start_times(self) -> None:
        """Calculate start times for all trajectory sequences."""
        self.start_times = []
        
        for traj_seq in self.trajectories:
            if not traj_seq:
                self.start_times.append(0.0)
                continue
                
            phrase_idx = traj_seq[0].phrase_idx
            if phrase_idx is None or phrase_idx >= len(self.piece.phrase_grid[self.instrument_idx]):
                self.start_times.append(0.0)
                continue
                
            phrase = self.piece.phrase_grid[self.instrument_idx][phrase_idx]
            start_time = (traj_seq[0].start_time or 0) + (phrase.start_time or 0)
            self.start_times.append(start_time)
    
    @property
    def query_answers(self) -> List[QueryAnswerType]:
        """Get structured query results."""
        answers = []
        
        for t_idx, trajs in enumerate(self.trajectories):
            if not trajs:
                continue
                
            # Calculate timing
            start_phrase_idx = trajs[0].phrase_idx
            if start_phrase_idx is None or start_phrase_idx >= len(self.piece.phrase_grid[self.instrument_idx]):
                continue
                
            start_phrase = self.piece.phrase_grid[self.instrument_idx][start_phrase_idx]
            start_time = (trajs[0].start_time or 0) + (start_phrase.start_time or 0)
            
            end_phrase_idx = trajs[-1].phrase_idx
            if end_phrase_idx is None or end_phrase_idx >= len(self.piece.phrase_grid[self.instrument_idx]):
                continue
                
            end_phrase = self.piece.phrase_grid[self.instrument_idx][end_phrase_idx]
            end_time = (trajs[-1].end_time or 0) + (end_phrase.start_time or 0)
            
            duration = end_time - start_time
            
            # Generate title
            title = self._generate_title(trajs, start_phrase_idx, end_phrase_idx)
            
            answer = QueryAnswerType(
                trajectories=trajs,
                identifier=self.identifier[t_idx],
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                segmentation=self.segmentation
            )
            answers.append(answer)
        
        return answers
    
    def _generate_title(self, trajs: List[Trajectory], start_phrase_idx: int, end_phrase_idx: int) -> str:
        """Generate a descriptive title for the query result."""
        if self.segmentation == SegmentationType.PHRASE:
            phrase_idx_str = str(start_phrase_idx + 1)
            return f"Phrase {phrase_idx_str}"
        elif self.segmentation == SegmentationType.GROUP:
            # This would need group information from trajectories
            phrase_idx_str = str(start_phrase_idx + 1)
            group_id = getattr(trajs[0], 'group_id', None)
            return f"Phrase {phrase_idx_str} Group {group_id if group_id else 'Unknown'}"
        elif self.segmentation == SegmentationType.SEQUENCE_OF_TRAJECTORIES:
            return self._generate_trajectory_sequence_title(trajs, start_phrase_idx, end_phrase_idx)
        elif self.segmentation == SegmentationType.CONNECTED_SEQUENCE_OF_TRAJECTORIES:
            return self._generate_trajectory_sequence_title(trajs, start_phrase_idx, end_phrase_idx)
        
        return "Unknown"
    
    def _generate_trajectory_sequence_title(self, trajs: List[Trajectory], start_phrase_idx: int, end_phrase_idx: int) -> str:
        """Generate title for trajectory sequence results."""
        phrase_idxs = list(set(traj.phrase_idx for traj in trajs if traj.phrase_idx is not None))
        phrase_idxs.sort()
        
        first_traj_idx = (trajs[0].num or 0) + 1
        last_traj_idx = (trajs[-1].num or 0) + 1
        
        if len(phrase_idxs) == 1:
            phrase_idx_str = str(phrase_idxs[0] + 1)
            return f"Phrase {phrase_idx_str} Traj {first_traj_idx}-{last_traj_idx}"
        else:
            start_phrase_str = str(phrase_idxs[0] + 1)
            end_phrase_str = str(phrase_idxs[-1] + 1)
            return f"Phrase {start_phrase_str} Traj {first_traj_idx} - Phrase {end_phrase_str} Traj {last_traj_idx}"
    
    # ---- Static factory methods ----
    
    @staticmethod
    async def single(
        transcription_id: str = "63445d13dc8b9023a09747a6",
        segmentation: SegmentationType = SegmentationType.PHRASE,
        designator: DesignatorType = DesignatorType.INCLUDES,
        category: CategoryType = CategoryType.TRAJECTORY_ID,
        pitch: Optional[Pitch] = None,
        sequence_length: Optional[int] = None,
        trajectory_id: Optional[int] = None,
        vowel: Optional[str] = None,
        consonant: Optional[str] = None,
        instrument_idx: int = 0,
    ) -> Query:
        """Create a single query instance.
        
        This is an async method that would need to fetch the piece data.
        For now, it's a placeholder that would need integration with the API client.
        """
        # This would need to be implemented with actual piece fetching logic
        # For now, return a basic implementation
        raise NotImplementedError("Single query requires integration with SwaraClient")
    
    @staticmethod
    async def multiple(
        queries: List[QueryType],
        transcription_id: str = "63445d13dc8b9023a09747a6",
        piece: Optional[Piece] = None,
        segmentation: SegmentationType = SegmentationType.PHRASE,
        sequence_length: Optional[int] = None,
        min_dur: float = 0.0,
        max_dur: float = 60.0,
        every: bool = True,
        instrument_idx: int = 0,
    ) -> MultipleReturnType:
        """Execute multiple queries and combine results.
        
        Args:
            queries: List of query specifications
            transcription_id: ID of transcription to query
            piece: Pre-loaded Piece object (optional)
            segmentation: Segmentation type for all queries
            sequence_length: Sequence length for trajectory sequences
            min_dur: Minimum duration filter
            max_dur: Maximum duration filter
            every: If True, require all queries to match; if False, any query can match
            instrument_idx: Index of instrument track to query
            
        Returns:
            Tuple of (trajectories, identifiers, query_answers)
        """
        if not queries:
            raise ValueError("No queries provided")
        
        if piece is None:
            # This would need integration with SwaraClient to fetch the piece
            raise NotImplementedError("Multiple queries require piece data or SwaraClient integration")
        
        output_trajectories: List[List[Trajectory]] = []
        output_identifiers: List[str] = []
        query_answers: List[QueryAnswerType] = []
        non_stringified_output_identifiers: List[Union[int, str, Dict[str, int]]] = []
        
        # Create query objects
        query_objs = []
        for query in queries:
            query_options = {
                "segmentation": segmentation,
                "designator": query.get("designator"),
                "category": query.get("category"),
                "pitch": query.get("pitch"),
                "sequence_length": sequence_length,
                "trajectory_id": query.get("trajectory_id"),
                "vowel": query.get("vowel"),
                "consonant": query.get("consonant"),
                "pitch_sequence": query.get("pitch_sequence"),
                "traj_id_sequence": query.get("traj_id_sequence"),
                "section_top_level": query.get("section_top_level"),
                "alap_section": query.get("alap_section"),
                "comp_type": query.get("comp_type"),
                "comp_sec_tempo": query.get("comp_sec_tempo"),
                "tala": query.get("tala"),
                "phrase_type": query.get("phrase_type"),
                "elaboration_type": query.get("elaboration_type"),
                "vocal_art_type": query.get("vocal_art_type"),
                "inst_art_type": query.get("inst_art_type"),
                "incidental": query.get("incidental"),
                "min_dur": min_dur,
                "max_dur": max_dur,
                "instrument_idx": instrument_idx,
            }
            query_objs.append(Query(piece, query_options))
        
        if every:
            # Only select trajectories that are in all answers
            if query_objs:
                output_identifiers = query_objs[0].stringified_identifier[:]
                for answer in query_objs[1:]:
                    output_identifiers = [
                        id_str for id_str in output_identifiers 
                        if id_str in answer.stringified_identifier
                    ]
                
                # Get corresponding trajectories and answers
                idxs = [
                    query_objs[0].stringified_identifier.index(id_str) 
                    for id_str in output_identifiers
                ]
                output_trajectories = [query_objs[0].trajectories[idx] for idx in idxs]
                non_stringified_output_identifiers = [query_objs[0].identifier[idx] for idx in idxs]
                query_answers = [query_objs[0].query_answers[idx] for idx in idxs]
        else:
            # Select trajectories that are in any answer
            start_times = []
            seen_ids = set()
            
            for answer in query_objs:
                for s_idx, s_id in enumerate(answer.stringified_identifier):
                    if s_id not in seen_ids:
                        seen_ids.add(s_id)
                        output_identifiers.append(s_id)
                        output_trajectories.append(answer.trajectories[s_idx])
                        non_stringified_output_identifiers.append(answer.identifier[s_idx])
                        query_answers.append(answer.query_answers[s_idx])
                        start_times.append(answer.start_times[s_idx])
            
            # Sort by start times
            sort_idxs = sorted(range(len(start_times)), key=lambda i: start_times[i])
            output_trajectories = [output_trajectories[idx] for idx in sort_idxs]
            non_stringified_output_identifiers = [non_stringified_output_identifiers[idx] for idx in sort_idxs]
            query_answers = [query_answers[idx] for idx in sort_idxs]
        
        return output_trajectories, non_stringified_output_identifiers, query_answers