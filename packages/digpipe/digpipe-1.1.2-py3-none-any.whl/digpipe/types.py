"""Core types and protocols for DigPipe."""

from dataclasses import dataclass
from typing import Protocol, Iterator, List, Tuple, Iterable

@dataclass
class DigitChunk:
    """A chunk of decimal digits."""
    index: int
    digits: bytes  # Bytes with values 0-9

@dataclass
class Action:
    """An abstract input action."""
    device: str
    control: str
    value: int
    frame: int

class DigitSource(Protocol):
    """Protocol for digit generators."""
    def chunks(self, chunk_size: int) -> Iterator[DigitChunk]:
        """Yields sequential chunks of digits."""
        ...

class DigitTape(Protocol):
    """Protocol for digit storage."""
    def write_chunk(self, chunk: DigitChunk) -> None:
        """Writes a chunk to storage."""
        ...

    def read_chunk(self, index: int) -> DigitChunk:
        """Reads a chunk from storage."""
        ...
        
    def exists(self, index: int) -> bool:
        """Checks if a chunk exists."""
        ...

class DigitMapper(Protocol):
    """Protocol for mapping digits to actions."""
    def map_chunk(
        self,
        chunk: DigitChunk,
        start_frame: int
    ) -> Tuple[List[Action], int]:
        """Maps a chunk of digits to a list of actions and returns the next start frame."""
        ...

class InputSink(Protocol):
    """Protocol for action consumers."""
    def write_actions(self, actions: Iterable[Action]) -> None:
        """Writes actions to the sink."""
        ...
        
    def close(self) -> None:
        """Closes the sink."""
        ...
