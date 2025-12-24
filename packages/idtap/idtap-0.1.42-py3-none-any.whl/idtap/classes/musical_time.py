from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MusicalTime:
    """Represents a musical time position within a meter."""
    cycle_number: int
    hierarchical_position: List[int] 
    fractional_beat: float
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.cycle_number < 0:
            raise ValueError("cycle_number must be non-negative")
        if not all(pos >= 0 for pos in self.hierarchical_position):
            raise ValueError("All hierarchical positions must be non-negative")
        if not (0.0 <= self.fractional_beat < 1.0):
            raise ValueError("fractional_beat must be in range [0.0, 1.0)")
    
    def __str__(self) -> str:
        """Compact string representation: C{cycle}:{hierarchy}+{fraction}"""
        hierarchy_str = ".".join(map(str, self.hierarchical_position))
        return f"C{self.cycle_number}:{hierarchy_str}+{self.fractional_beat:.3f}"
    
    def to_readable_string(self) -> str:
        """Human-readable format with level names."""
        if not self.hierarchical_position:
            return f"Cycle {self.cycle_number + 1}"
        
        level_names = ["Beat", "Subdivision", "Sub-subdivision", "Sub-sub-subdivision"]
        
        parts = []
        for i, pos in enumerate(self.hierarchical_position):
            if i < len(level_names):
                name = level_names[i]
            else:
                name = f"Sub^{i-1}-subdivision"
            parts.append(f"{name} {pos + 1}")  # 1-indexed for display
        
        base = f"Cycle {self.cycle_number + 1}: {', '.join(parts)}"
        if self.fractional_beat > 0:
            base += f" + {self.fractional_beat:.3f}"
        return base
    
    @property
    def beat(self) -> int:
        """Beat number (0-indexed)"""
        return self.hierarchical_position[0] if self.hierarchical_position else 0
    
    @property 
    def subdivision(self) -> Optional[int]:
        """Subdivision number (0-indexed), None if hierarchy has only 1 level"""
        return self.hierarchical_position[1] if len(self.hierarchical_position) > 1 else None
        
    @property
    def sub_subdivision(self) -> Optional[int]:
        """Sub-subdivision number (0-indexed), None if hierarchy has < 3 levels"""
        return self.hierarchical_position[2] if len(self.hierarchical_position) > 2 else None
    
    def get_level(self, level: int) -> Optional[int]:
        """Get position at arbitrary hierarchical level (0=beat, 1=subdivision, etc.)"""
        return self.hierarchical_position[level] if level < len(self.hierarchical_position) else None
    
    @property
    def hierarchy_depth(self) -> int:
        """Number of hierarchical levels in this musical time"""
        return len(self.hierarchical_position)