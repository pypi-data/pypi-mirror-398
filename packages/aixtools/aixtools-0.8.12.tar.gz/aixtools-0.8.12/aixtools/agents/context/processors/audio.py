import io
import wave
from collections.abc import Callable
from pathlib import Path

from aixtools.agents.context.data_models import BinaryContent, FileExtractionResult, FileType, TruncationInfo
from aixtools.agents.context.processors.common import create_error_result, create_file_metadata


def _extract_audio_segment(file_path: Path, start_seconds: float, end_seconds: float | None = None) -> bytes:
    """Extract a segment of audio from start to end seconds."""
    with wave.open(str(file_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        frames = wav.getnframes()

        start_frame = int(start_seconds * framerate)

        if end_seconds is None:
            end_frame = frames
        else:
            end_frame = min(int(end_seconds * framerate), frames)

        if start_frame >= frames:
            start_frame = 0

        wav.setpos(start_frame)
        frames_to_read = end_frame - start_frame
        audio_data = wav.readframes(frames_to_read)

        output = io.BytesIO()
        with wave.open(output, "wb") as out_wav:
            out_wav.setnchannels(channels)
            out_wav.setsampwidth(sample_width)
            out_wav.setframerate(framerate)
            out_wav.writeframes(audio_data)

        return output.getvalue()


def _get_audio_info(file_path: Path) -> dict:
    """Extract basic audio file information."""
    try:
        with wave.open(str(file_path), "rb") as wav:
            return {
                "channels": wav.getnchannels(),
                "sample_width": wav.getsampwidth(),
                "framerate": wav.getframerate(),
                "frames": wav.getnframes(),
                "duration": wav.getnframes() / wav.getframerate(),
            }
    except Exception:
        return {}


def _subsample_audio(file_path: Path, max_duration: float) -> bytes:
    """Subsample audio by extracting first max_duration seconds."""
    with wave.open(str(file_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        frames = wav.getnframes()
        duration = frames / framerate

        if duration <= max_duration:
            wav.rewind()
            return wav.readframes(frames)

        frames_to_read = int(max_duration * framerate)

        wav.rewind()
        selected_frames = wav.readframes(frames_to_read)

        output = io.BytesIO()
        with wave.open(output, "wb") as out_wav:
            out_wav.setnchannels(channels)
            out_wav.setsampwidth(sample_width)
            out_wav.setframerate(framerate)
            out_wav.writeframes(selected_frames)

        return output.getvalue()


def process_audio(
    file_path: Path,
    max_duration: float = 30.0,
    max_size_bytes: int = 10 * 1024 * 1024,
    tokenizer: Callable | None = None,
) -> FileExtractionResult:
    """Process audio file, subsampling if it exceeds size limits.

    Args:
        file_path: Path to audio file
        max_duration: Maximum duration in seconds (default 30.0)
        max_size_bytes: Maximum output size in bytes (default 10MB)
        tokenizer: Optional tokenizer function (unused for audio)
    """
    try:
        info = _get_audio_info(file_path)
        metadata = create_file_metadata(file_path, mime_type="audio/wav")

        if not info:
            return FileExtractionResult(
                content=None,
                success=False,
                error_message="Failed to read audio file information",
                file_type=FileType.BINARY,
                metadata=metadata,
            )

        duration = info.get("duration", 0)
        truncation_info = None

        if duration > max_duration or file_path.stat().st_size > max_size_bytes:
            audio_data = _subsample_audio(file_path, max_duration)
            truncation_info = TruncationInfo(
                lines_shown=f"Subsampled to {max_duration:.1f}s (original: {duration:.1f}s)"
            )
        else:
            with open(file_path, "rb") as f:
                audio_data = f.read()

        content = BinaryContent(data=audio_data, mime_type="audio/wav")

        return FileExtractionResult(
            content=content, success=True, file_type=FileType.BINARY, truncation_info=truncation_info, metadata=metadata
        )

    except Exception as e:
        return create_error_result(e, FileType.BINARY, file_path, "audio file")


def process_audio_head(
    file_path: Path, duration: float = 10.0, tokenizer: Callable | None = None
) -> FileExtractionResult:
    """Extract first N seconds of audio file.

    Args:
        file_path: Path to audio file
        duration: Duration in seconds to extract (default 10.0)
        tokenizer: Optional tokenizer function (unused for audio)
    """
    try:
        info = _get_audio_info(file_path)
        metadata = create_file_metadata(file_path, mime_type="audio/wav")

        if not info:
            return FileExtractionResult(
                content=None,
                success=False,
                error_message="Failed to read audio file information",
                file_type=FileType.BINARY,
                metadata=metadata,
            )

        original_duration = info.get("duration", 0)
        actual_duration = min(duration, original_duration)

        audio_data = _extract_audio_segment(file_path, 0, actual_duration)

        truncation_info = TruncationInfo(
            lines_shown=f"First {actual_duration:.1f}s (of {original_duration:.1f}s total)"
        )

        content = BinaryContent(data=audio_data, mime_type="audio/wav")

        return FileExtractionResult(
            content=content, success=True, file_type=FileType.BINARY, truncation_info=truncation_info, metadata=metadata
        )

    except Exception as e:
        return create_error_result(e, FileType.BINARY, file_path, "audio head")


def process_audio_tail(
    file_path: Path, duration: float = 10.0, tokenizer: Callable | None = None
) -> FileExtractionResult:
    """Extract last N seconds of audio file.

    Args:
        file_path: Path to audio file
        duration: Duration in seconds to extract (default 10.0)
        tokenizer: Optional tokenizer function (unused for audio)
    """
    try:
        info = _get_audio_info(file_path)
        metadata = create_file_metadata(file_path, mime_type="audio/wav")

        if not info:
            return FileExtractionResult(
                content=None,
                success=False,
                error_message="Failed to read audio file information",
                file_type=FileType.BINARY,
                metadata=metadata,
            )

        original_duration = info.get("duration", 0)
        actual_duration = min(duration, original_duration)
        start_seconds = max(0, original_duration - actual_duration)

        audio_data = _extract_audio_segment(file_path, start_seconds, original_duration)

        truncation_info = TruncationInfo(lines_shown=f"Last {actual_duration:.1f}s (of {original_duration:.1f}s total)")

        content = BinaryContent(data=audio_data, mime_type="audio/wav")

        return FileExtractionResult(
            content=content, success=True, file_type=FileType.BINARY, truncation_info=truncation_info, metadata=metadata
        )

    except Exception as e:
        return create_error_result(e, FileType.BINARY, file_path, "audio tail")
