"""Utilities for BigKinds MCP Server."""

from .errors import (
    ErrorCode,
    MCPError,
    empty_results_response,
    error_response,
    handle_api_error,
    handle_scrape_error,
)
from .image_filter import (
    ImageFilter,
    filter_meaningful_images,
    get_image_filter,
    get_main_image,
)
from .markdown import (
    article_to_context,
    extract_key_sentences,
    html_to_markdown,
    summarize_for_llm,
    text_to_llm_context,
)

__all__ = [
    # errors
    "ErrorCode",
    "MCPError",
    "empty_results_response",
    "error_response",
    "handle_api_error",
    "handle_scrape_error",
    # image_filter
    "ImageFilter",
    "filter_meaningful_images",
    "get_image_filter",
    "get_main_image",
    # markdown
    "article_to_context",
    "extract_key_sentences",
    "html_to_markdown",
    "summarize_for_llm",
    "text_to_llm_context",
]
