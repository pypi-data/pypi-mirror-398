"""Reference frame log sink."""

from typing import Iterable, TextIO
import sys
from ..types import InputSink, Action

class FrameLogSink(InputSink):
    """
    Writes actions to a log file or stdout.
    Format: FRAME: DEVICE.CONTROL=VALUE
    """
    
    def __init__(self, output_file: str = "-"):
        self.file_path = output_file
        self.file: TextIO | None = None
        
        if output_file == "-":
            self.file = sys.stdout
        else:
            self.file = open(output_file, "w", encoding="utf-8")
            
    def write_actions(self, actions: Iterable[Action]) -> None:
        if self.file is None:
            raise RuntimeError("Sink is closed or not initialized")
            
        for action in actions:
            line = f"{action.frame}: {action.device}.{action.control}={action.value}\n"
            self.file.write(line)
            
    def close(self) -> None:
        if self.file and self.file_path != "-":
            self.file.close()
        self.file = None
