from __future__ import annotations
from typing import List, Optional, Dict, Any

from .pitch import Pitch
from .raga import Raga


class NoteViewPhrase:
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        opts = options or {}
        
        # Parameter validation
        self._validate_parameters(opts)
        self.pitches: List[Pitch] = opts.get('pitches', [])
        self.dur_tot: Optional[float] = opts.get('dur_tot')
        self.raga: Optional[Raga] = opts.get('raga')
        self.start_time: Optional[float] = opts.get('start_time')

    def _validate_parameters(self, opts: dict) -> None:
        """Validate constructor parameters and provide helpful error messages."""
        if not opts:
            return
            
        # Define allowed parameter names
        allowed_keys = {'pitches', 'dur_tot', 'raga', 'start_time'}
        provided_keys = set(opts.keys())
        invalid_keys = provided_keys - allowed_keys
        
        # Check for invalid parameter names
        if invalid_keys:
            error_messages = []
            
            for key in invalid_keys:
                if key == 'duration' or key == 'duration_total':
                    error_messages.append(f"Parameter '{key}' not supported. Did you mean 'dur_tot'?")
                elif key == 'pitch_list':
                    error_messages.append(f"Parameter '{key}' not supported. Did you mean 'pitches'?")
                elif key == 'start':
                    error_messages.append(f"Parameter '{key}' not supported. Did you mean 'start_time'?")
                else:
                    error_messages.append(f"Invalid parameter: '{key}'")
            
            error_msg = "; ".join(error_messages)
            error_msg += f". Allowed parameters: {sorted(allowed_keys)}"
            raise ValueError(error_msg)
        
        # Validate parameter types and values
        if 'pitches' in opts:
            if not isinstance(opts['pitches'], list):
                raise TypeError(f"Parameter 'pitches' must be a list, got {type(opts['pitches']).__name__}")
        
        if 'dur_tot' in opts and opts['dur_tot'] is not None:
            if not isinstance(opts['dur_tot'], (int, float)):
                raise TypeError(f"Parameter 'dur_tot' must be a number, got {type(opts['dur_tot']).__name__}")
            if opts['dur_tot'] <= 0:
                raise ValueError(f"Parameter 'dur_tot' must be positive, got {opts['dur_tot']}")
        
        if 'raga' in opts and opts['raga'] is not None:
            if not isinstance(opts['raga'], (Raga, dict)):
                raise TypeError(f"Parameter 'raga' must be a Raga object or dict, got {type(opts['raga']).__name__}")
        
        if 'start_time' in opts and opts['start_time'] is not None:
            if not isinstance(opts['start_time'], (int, float)):
                raise TypeError(f"Parameter 'start_time' must be a number, got {type(opts['start_time']).__name__}")
            if opts['start_time'] < 0:
                raise ValueError(f"Parameter 'start_time' must be non-negative, got {opts['start_time']}")
