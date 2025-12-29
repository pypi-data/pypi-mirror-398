"""Implementation of digit storage on disk."""

import json
from pathlib import Path
from .types import DigitChunk, DigitTape

class FileDigitTape(DigitTape):
    """
    Storage for digit chunks using packed nibbles (2 digits per byte).
    
    Structure:
    directory/
      header.json
      chunk_000000.dgt
      ...
    """
    
    def __init__(self, directory: str | Path, create_if_missing: bool = True):
        self.directory = Path(directory)
        if create_if_missing:
            self.directory.mkdir(parents=True, exist_ok=True)
        
        self.header_path = self.directory / "header.json"
        self.metadata = {}
        
        if self.header_path.exists():
            with open(self.header_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            if create_if_missing:
                self._save_header()

    def _save_header(self):
        with open(self.header_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

    def _get_chunk_path(self, index: int) -> Path:
        return self.directory / f"chunk_{index:06d}.dgt"

    def write_chunk(self, chunk: DigitChunk) -> None:
        """Writes a chunk of digits to disk, packing 2 digits per byte."""
        if len(chunk.digits) % 2 != 0:
            raise ValueError("Chunk size must be even for packed storage")
            
        # Pre-allocate bytearray for performance
        packed = bytearray(len(chunk.digits) // 2)
        
        # Vectorized packing would be faster but sticking to pure python list/loop for now
        # as per explicit admonition "Do NOT optimize prematurely with C"
        # However, manual loop is slow for 1M items. 
        # But this is I/O bound likely anyway.
        
        digits = chunk.digits
        for i in range(len(packed)):
            high = digits[2*i]
            low = digits[2*i+1]
            if not (0 <= high <= 9 and 0 <= low <= 9):
                 raise ValueError(f"Invalid digits at index {2*i}: {high}, {low}")
            packed[i] = (high << 4) | low
            
        with open(self._get_chunk_path(chunk.index), 'wb') as f:
            f.write(packed)

    def read_chunk(self, index: int) -> DigitChunk:
        """Reads a chunk from disk and unpacks it."""
        path = self._get_chunk_path(index)
        if not path.exists():
             raise FileNotFoundError(f"Chunk {index} not found at {path}")
             
        with open(path, 'rb') as f:
            packed = f.read()
            
        digits = bytearray(len(packed) * 2)
        for i in range(len(packed)):
            byte = packed[i]
            digits[2*i] = (byte >> 4) & 0x0F
            digits[2*i+1] = byte & 0x0F
            
        return DigitChunk(index=index, digits=bytes(digits))
        
    def exists(self, index: int) -> bool:
        return self._get_chunk_path(index).exists()
