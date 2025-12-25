"""Prompt building utilities for Pydantic AI agent, including file handling and context management."""

import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional

import tiktoken
from markitdown import MarkItDown
from pydantic_ai import BinaryContent

from aixtools.context import SessionIdTuple
from aixtools.logging.logging_config import get_logger
from aixtools.server import container_to_host_path
from aixtools.utils.config import (
    EXTRACTABLE_DOCUMENT_TYPES,
    IMAGE_ATTACHMENT_TYPES,
    MAX_EXTRACTED_TEXT_TOKENS,
    MAX_IMAGE_ATTACHMENT_SIZE,
    PROMPTS_DIR,
)
from aixtools.utils.files import is_text_content

logger = get_logger(__name__)

# cl100k_base encoding (OpenAI GPT-4) - not a perfect fit for all models but good enough for our use case
_tokenizer = tiktoken.get_encoding("cl100k_base")


@dataclass
class FileExtractionResult:
    """Result of file content extraction.

    Attributes:
        content: Extracted file content (str for text/documents, BinaryContent for images, None on failure)
        success: True if file was successfully read or extracted, False on any failure
        error_message: Error description if extraction failed, None otherwise
        was_extracted: True if document extraction via markitdown was used successfully
    """

    content: str | BinaryContent | None
    success: bool
    error_message: str | None = None
    was_extracted: bool = False


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string using tiktoken."""
    try:
        return len(_tokenizer.encode(text))
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Token counting failed, falling back to character-based estimate: %s", e)
        # Fallback: rough estimate of 1 token per 4 characters
        return len(text) // 4


def truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to a maximum number of tokens.

    Args:
        text: The text to truncate
        max_tokens: Maximum number of tokens to keep

    Returns:
        Truncated text that fits within the token limit
    """
    try:
        tokens = _tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated_tokens = tokens[:max_tokens]
        return _tokenizer.decode(truncated_tokens)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Token truncation failed, falling back to character-based truncation: %s", e)
        # Fallback: rough estimate of 4 characters per token
        max_chars = max_tokens * 4
        return text[:max_chars]


def should_be_included_into_context(
    file_content: BinaryContent | str | None,
    *,
    max_image_size_bytes: int = MAX_IMAGE_ATTACHMENT_SIZE,
    max_extracted_text_tokens: int = MAX_EXTRACTED_TEXT_TOKENS,
) -> bool:
    """Check if file content should be included in model context based on type and size limits."""
    if file_content is None:
        return False

    # Handle extracted text (strings)
    if isinstance(file_content, str):
        token_count = count_tokens(file_content)
        return token_count < max_extracted_text_tokens

    # Handle binary content (images only)
    if isinstance(file_content, BinaryContent):
        if file_content.media_type not in IMAGE_ATTACHMENT_TYPES:
            return False
        image_size = len(file_content.data)
        return image_size < max_image_size_bytes

    return False


def file_to_binary_content(file_path: str | Path, mime_type: Optional[str] = None) -> FileExtractionResult:
    """Read file and extract text from documents (PDF, DOCX, XLSX, PPTX) using markitdown."""
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

    # Extract text from supported document types using markitdown
    if mime_type in EXTRACTABLE_DOCUMENT_TYPES:
        try:
            markitdown = MarkItDown()
            result = markitdown.convert(str(file_path))
            return FileExtractionResult(
                content=result.text_content, success=True, error_message=None, was_extracted=True
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_msg = f"Extraction failed: {type(e).__name__}: {str(e)}"
            logger.error("Document extraction failed for %s: %s", file_path, error_msg)
            return FileExtractionResult(content=None, success=False, error_message=error_msg)

    # Read the file data for non-document types
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        # Return as string if it's text content
        if is_text_content(data, mime_type):
            return FileExtractionResult(content=data.decode("utf-8"), success=True)

        # Return as binary content for images and other binary files
        return FileExtractionResult(content=BinaryContent(data=data, media_type=mime_type), success=True)
    except Exception as e:  # pylint: disable=broad-exception-caught
        error_msg = f"Failed to read file: {type(e).__name__}: {str(e)}"
        logger.error("File reading failed for %s: %s", file_path, error_msg)
        return FileExtractionResult(content=None, success=False, error_message=error_msg)


def truncate_extracted_text(text: str, max_tokens: int | None = None) -> str:
    """Truncate text to max_tokens with warning prefix."""
    if max_tokens is None:
        max_tokens = MAX_EXTRACTED_TEXT_TOKENS

    total_tokens = count_tokens(text)

    if total_tokens <= max_tokens:
        return text

    truncated_text = truncate_text_to_tokens(text, max_tokens)
    truncated_tokens = max_tokens

    return f"[TRUNCATED - showing first {truncated_tokens} of {total_tokens} tokens]\n\n{truncated_text}"


def build_user_input(
    session_tuple: SessionIdTuple,
    user_text: str,
    file_paths: list[Path],
) -> str | list[str | BinaryContent]:
    """Build user input for the Pydantic AI agent, including file attachments if provided."""
    if not file_paths:
        return user_text

    attachment_info_lines = []
    binary_attachments: list[str | BinaryContent] = []

    for workspace_path in file_paths:
        # Convert Path to PurePosixPath for container_to_host_path
        workspace_posix_path = PurePosixPath(workspace_path)
        host_path = container_to_host_path(workspace_posix_path, ctx=session_tuple)

        # Handle None return from container_to_host_path
        if host_path is None:
            attachment_info = (
                f"* {workspace_path.name} (path in workspace: {workspace_path}) -- conversion failed: invalid path"
            )
            attachment_info_lines.append(attachment_info)
            continue

        file_size = host_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(host_path)
        mime_type = mime_type or "application/octet-stream"

        attachment_info = f"* {workspace_path.name} (file_size={file_size} bytes) (path in workspace: {workspace_path})"
        extraction_result = file_to_binary_content(host_path, mime_type)

        # Handle extraction failure - exclude from attachments
        if not extraction_result.success:
            attachment_info += f" -- extraction failed: {extraction_result.error_message}"
            attachment_info_lines.append(attachment_info)
            continue

        # Handle successful extraction
        if extraction_result.was_extracted:
            attachment_info += " -- extracted as text"

        # Check if content should be included in context
        if should_be_included_into_context(extraction_result.content) and extraction_result.content is not None:
            binary_attachments.append(extraction_result.content)
            attachment_info += f" -- provided to model context at index {len(binary_attachments) - 1}"
        elif (
            isinstance(extraction_result.content, str) and extraction_result.content and extraction_result.was_extracted
        ):
            # Truncate large extracted text and include with warning (only for extracted documents)
            truncated_content = truncate_extracted_text(extraction_result.content)
            binary_attachments.append(truncated_content)
            attachment_info += f" -- truncated and provided to model context at index {len(binary_attachments) - 1}"
        elif extraction_result.content is not None:
            # Content exists but excluded from context (e.g., images too large, non-extracted text)
            attachment_info += " -- too large for context"

        attachment_info_lines.append(attachment_info)

    full_prompt = user_text + "\nAttachments:\n" + "\n".join(attachment_info_lines)

    return [full_prompt] + binary_attachments


def load_prompt(prompt_path: Path, **kwargs) -> str:
    """Load a specific prompt file from the prompts directory.

    Args:
        prompt_path: Path to the markdown file (e.g., PROMPTS_DIR / 'system_prompt.md')
        **kwargs: Variables to substitute in the prompt template

    Returns:
        Content of the prompt file as a string, with variables substituted

    Raises:
        ValueError: If template has variables not provided in kwargs, or kwargs has unused variables
    """
    template = prompt_path.read_text(encoding="utf-8")

    # Extract all variables from the template using regex
    template_vars = set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template))
    provided_vars = set(kwargs.keys())

    # Check for missing variables
    missing_vars = template_vars - provided_vars
    if missing_vars:
        raise ValueError(
            f"Template '{prompt_path.name}' requires variables that were not provided: {sorted(missing_vars)}"
        )

    # Check for unused variables
    unused_vars = provided_vars - template_vars
    if unused_vars:
        raise ValueError(f"Template '{prompt_path.name}' received unused variables: {sorted(unused_vars)}")

    if kwargs:
        return template.format(**kwargs)
    return template


def get_system_prompt(**kwargs) -> str:
    """Load the system prompt from prompts/system_prompt.md."""
    return load_prompt(PROMPTS_DIR / "system_prompt.md", **kwargs)


def get_prompt(prompt_name: str, **kwargs) -> str:
    """Load a prompt from prompts/{prompt_name}.md."""
    return load_prompt(PROMPTS_DIR / f"{prompt_name}.md", **kwargs)


def get_instructions(**kwargs) -> str:
    """Load the instructions from prompts/instructions.md."""
    return load_prompt(PROMPTS_DIR / "instructions.md", **kwargs)
