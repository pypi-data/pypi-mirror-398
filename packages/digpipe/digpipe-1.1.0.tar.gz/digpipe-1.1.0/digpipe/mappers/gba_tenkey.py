"""GBA Ten-Key Mapper."""

from typing import List, Tuple
from ..types import DigitMapper, DigitChunk, Action

class GbaTenKeyMapper(DigitMapper):
    """
    Maps digits 0-9 to GBA controls.
    0-9 -> A, B, L, R, UP, DOWN, LEFT, RIGHT, START, SELECT
    """
    
    MAPPING = [
        "A", "B", "L", "R", "UP", "DOWN", "LEFT", "RIGHT", "START", "SELECT"
    ]
    
    def __init__(self, hold_frames: int = 5, release_frames: int = 5):
        self.hold_frames = hold_frames
        self.release_frames = release_frames
        
    def map_chunk(
        self,
        chunk: DigitChunk,
        start_frame: int
    ) -> Tuple[List[Action], int]:
        actions = []
        current_frame = start_frame
        
        for digit_byte in chunk.digits:
            # digit_byte is 0-9
            if 0 <= digit_byte <= 9:
                control = self.MAPPING[digit_byte]
                
                # Press
                actions.append(Action(
                    device="gba",
                    control=control,
                    value=1,
                    frame=current_frame
                ))
                
                # Advance for hold
                current_frame += self.hold_frames
                
                # Release
                actions.append(Action(
                    device="gba",
                    control=control,
                    value=0,
                    frame=current_frame
                ))
                
                # Advance for release gap
                current_frame += self.release_frames
                
        return actions, current_frame
