"""Main interface for context engineering file processing with file type detection."""

import mimetypes
from collections.abc import Callable
from pathlib import Path

import tiktoken

from aixtools.agents.context.data_models import FileExtractionResult, FileType
from aixtools.agents.context.processors.audio import process_audio
from aixtools.agents.context.processors.code import process_code
from aixtools.agents.context.processors.document import process_document
from aixtools.agents.context.processors.image import process_image
from aixtools.agents.context.processors.json import process_json
from aixtools.agents.context.processors.spreadsheet import process_spreadsheet
from aixtools.agents.context.processors.tabular import process_tabular
from aixtools.agents.context.processors.text import process_text
from aixtools.agents.context.processors.xml import process_xml
from aixtools.agents.context.processors.yaml import process_yaml
from aixtools.utils import config

# Code file extensions
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".go",
    ".rs",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".r",
    ".m",
    ".mm",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".sql",
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".vue",
    ".svelte",
}

# Markdown extensions
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd", ".rmd"}

# Text extensions
TEXT_EXTENSIONS = {".txt", ".log", ".cfg", ".conf", ".ini", ".properties", ".env"}

# Document extensions
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx"}

# Spreadsheet extensions
SPREADSHEET_EXTENSIONS = {".xlsx", ".xls", ".ods"}

# Structured data extensions
JSON_EXTENSIONS = {".json", ".jsonl", ".ipynb"}
YAML_EXTENSIONS = {".yaml", ".yml"}
XML_EXTENSIONS = {".xml", ".xsd", ".xsl", ".xslt", ".svg"}

# Tabular extensions
TABULAR_EXTENSIONS = {".csv", ".tsv"}

# Image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

# Audio extensions
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"}

# Archive extensions
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}


def _detect_file_type(file_path: Path) -> FileType:
    """Detect file type from extension and MIME type."""
    suffix = file_path.suffix.lower()

    # Check by extension first
    if suffix in CODE_EXTENSIONS:
        return FileType.CODE
    if suffix in MARKDOWN_EXTENSIONS:
        return FileType.MARKDOWN
    if suffix in TEXT_EXTENSIONS:
        return FileType.TEXT
    if suffix in DOCUMENT_EXTENSIONS:
        if suffix == ".pdf":
            return FileType.PDF
        if suffix == ".pptx":
            return FileType.PPTX
        return FileType.DOCX
    if suffix in SPREADSHEET_EXTENSIONS:
        return FileType.SPREADSHEET
    if suffix in JSON_EXTENSIONS:
        return FileType.JSON
    if suffix in YAML_EXTENSIONS:
        return FileType.YAML
    if suffix in XML_EXTENSIONS:
        return FileType.XML
    if suffix in TABULAR_EXTENSIONS:
        return FileType.CSV
    if suffix in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    if suffix in AUDIO_EXTENSIONS:
        return FileType.AUDIO
    if suffix in ARCHIVE_EXTENSIONS:
        return FileType.ARCHIVE

    # Fallback to MIME type detection
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if mime_type.startswith("text/"):
            return FileType.TEXT
        if mime_type.startswith("image/"):
            return FileType.IMAGE
        if mime_type.startswith("audio/"):
            return FileType.AUDIO
        if mime_type in {"application/json"}:
            return FileType.JSON
        if mime_type in {"application/xml", "text/xml"}:
            return FileType.XML
        if mime_type in {"text/csv"}:
            return FileType.CSV
        if mime_type in config.EXTRACTABLE_DOCUMENT_TYPES:
            if "pdf" in mime_type:
                return FileType.PDF
            if "word" in mime_type:
                return FileType.DOCX
            if "spreadsheet" in mime_type or "excel" in mime_type:
                return FileType.SPREADSHEET

    return FileType.BINARY


def _get_default_tokenizer() -> callable:
    """Get default tokenizer (tiktoken cl100k_base with fallback)."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return lambda text: len(encoding.encode(text))
    except Exception:
        # Fallback to character-based estimation
        return lambda text: len(text) // 4


def _apply_token_limit(
    result: FileExtractionResult, tokenizer: Callable[[str], int], max_tokens: int
) -> FileExtractionResult:
    """Apply token-based truncation if content exceeds max_tokens.

    This is applied after format-specific processing to ensure token limits are enforced.
    Only applies to string content, not binary data.
    """
    # Only apply to string content
    if not isinstance(result.content, str) or not result.success:
        return result

    # Count tokens
    token_count = tokenizer(result.content)

    # If within limit, just update truncation info with token count
    if token_count <= max_tokens:
        if result.truncation_info:
            result.truncation_info.tokens_shown = token_count
            result.truncation_info.total_tokens = token_count
        return result

    # Need to truncate - use tiktoken to truncate by tokens
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(result.content)
    truncated_tokens = tokens[:max_tokens]
    truncated_content = encoding.decode(truncated_tokens)

    # Update result
    result.content = truncated_content + "\n\n[... truncated due to token limit ...]"

    # Update truncation info
    if not result.truncation_info:
        from aixtools.agents.context.data_models import TruncationInfo

        result.truncation_info = TruncationInfo()

    result.truncation_info.tokens_shown = max_tokens
    result.truncation_info.total_tokens = token_count
    result.truncation_info.total_output_limit_reached = True

    return result


def read_file(
    file_path: Path | str,
    tokenizer: Callable[[str], int] | None = None,
    max_tokens_per_file: int = config.MAX_TOKENS_PER_FILE,
    max_total_output: int = config.MAX_TOTAL_OUTPUT,
    **kwargs,
) -> FileExtractionResult:
    """Read and process file based on detected type.

    Args:
        file_path: Path to file to process
        tokenizer: Optional tokenizer function (str -> int). Default: tiktoken cl100k_base
        max_tokens_per_file: Maximum tokens allowed per file
        max_total_output: Maximum total output length (characters)
        **kwargs: Additional processor-specific arguments

    Returns:
        FileExtractionResult with processed content
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        return FileExtractionResult(content=None, success=False, error_message=f"File not found: {file_path}")

    if tokenizer is None:
        tokenizer = _get_default_tokenizer()

    file_type = _detect_file_type(file_path)

    # Route to appropriate processor
    match file_type:
        case FileType.CODE:
            result = process_code(file_path, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs)
        case FileType.MARKDOWN:
            result = process_text(
                file_path, tokenizer=tokenizer, max_total_output=max_total_output, file_type=FileType.MARKDOWN, **kwargs
            )
        case FileType.TEXT:
            result = process_text(
                file_path, tokenizer=tokenizer, max_total_output=max_total_output, file_type=FileType.TEXT, **kwargs
            )
        case FileType.JSON:
            result = process_json(file_path, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs)
        case FileType.YAML:
            result = process_yaml(file_path, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs)
        case FileType.XML:
            result = process_xml(file_path, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs)
        case FileType.CSV:
            result = process_tabular(file_path, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs)
        case FileType.PDF | FileType.DOCX | FileType.PPTX:
            result = process_document(
                file_path, file_type=file_type, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs
            )
        case FileType.SPREADSHEET:
            result = process_spreadsheet(file_path, tokenizer=tokenizer, max_total_output=max_total_output, **kwargs)
        case FileType.IMAGE:
            result = process_image(file_path, **kwargs)
        case FileType.AUDIO:
            result = process_audio(file_path, **kwargs)
        case FileType.ARCHIVE:
            result = FileExtractionResult(
                content=None, success=False, error_message="Archive processing not yet implemented", file_type=file_type
            )
        case FileType.BINARY:
            result = FileExtractionResult(
                content=None,
                success=False,
                error_message="Binary file metadata processing not yet implemented",
                file_type=file_type,
            )
        case _:
            result = FileExtractionResult(
                content=None, success=False, error_message=f"Unknown file type: {file_type}", file_type=file_type
            )

    # Apply token-based truncation as a final check
    result = _apply_token_limit(result, tokenizer, max_tokens_per_file)

    return result
