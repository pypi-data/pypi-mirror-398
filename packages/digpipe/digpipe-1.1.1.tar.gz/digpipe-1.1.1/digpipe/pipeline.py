"""Pipeline orchestration."""

from .digtape import FileDigitTape
from .sources.pi_chudnovsky import PiDigitSource
from .mappers.gba_tenkey import GbaTenKeyMapper
from .sinks.frame_log import FrameLogSink
from .types import DigitSource, DigitMapper, InputSink

def get_source(name: str, total_digits: int) -> DigitSource:
    if name == "pi":
        return PiDigitSource(total_digits)
    raise ValueError(f"Unknown source: {name}")

def get_mapper(name: str) -> DigitMapper:
    if name == "gba-tenkey":
        return GbaTenKeyMapper()
    raise ValueError(f"Unknown mapper: {name}")

def get_sink(name: str, output: str) -> InputSink:
    if name == "frame-log":
        return FrameLogSink(output)
    raise ValueError(f"Unknown sink: {name}")

def run_generation(
    source_name: str,
    total_digits: int,
    chunk_size: int,
    tape_path: str
) -> None:
    """Runs the generation pipeline: Source -> Tape."""
    print(f"Initializing source '{source_name}' for {total_digits} digits...")
    source = get_source(source_name, total_digits)
    tape = FileDigitTape(tape_path)
    
    print(f"Generating digits in chunks of {chunk_size}...")
    count = 0
    for chunk in source.chunks(chunk_size):
        tape.write_chunk(chunk)
        count += len(chunk.digits)
        print(f"Wrote chunk {chunk.index} ({len(chunk.digits)} digits). Total: {count}")
    
    print(f"Generation complete. Total digits: {count}")

def run_rendering(
    tape_path: str,
    mapper_name: str,
    sink_name: str,
    output_path: str,
    start_chunk: int = 0
) -> None:
    """Runs the rendering pipeline: Tape -> Mapper -> Sink."""
    tape = FileDigitTape(tape_path, create_if_missing=False)
    if not tape.header_path.exists():
        raise FileNotFoundError(f"No tape found at {tape_path}")
        
    mapper = get_mapper(mapper_name)
    sink = get_sink(sink_name, output_path)
    
    current_frame = 0
    chunk_index = start_chunk
    
    try:
        while tape.exists(chunk_index):
            chunk = tape.read_chunk(chunk_index)
            actions, next_frame = mapper.map_chunk(chunk, current_frame)
            sink.write_actions(actions)
            current_frame = next_frame
            chunk_index += 1
    finally:
        sink.close()
        
    print(f"Rendering complete. Processed {chunk_index} chunks. Final frame: {current_frame}")
