# Copyright (c) 2025 Sethu Pavan Venkata Reddy Pastula
# Licensed under the Apache License, Version 2.0. See LICENSE file for details.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .config import MarkdownifyConfig
from .markdownifier import Markdownifier

app = typer.Typer(
    help=(
        "Convert documents (PDF/DOCX) or images (PNG/JPG/JPEG) to Markdown using Vision LLMs via LiteLLM."
    )
)


@app.command()
def run(
    input_path: str = typer.Argument(
        ...,
        help=(
            "Path to input .pdf (preferred), .docx (discouraged), or image file (.png/.jpg/.jpeg)"
        ),
    ),
    output: str = typer.Option(..., "-o", "--output", help="Output .md path"),
    model: Optional[str] = typer.Option(
        None, help="LiteLLM model, e.g. gpt-4.1-mini, azure/<deployment>, gemini/gemini-2.5-flash"
    ),
    dpi: int = typer.Option(
        72,
        help=(
            "DPI for rendering PDF pages (ignored for direct image inputs). Higher DPI may improve OCR accuracy if the document is blurry."
        ),
    ),
    max_group_pages: int = typer.Option(3, help="Max pages to merge for continued content"),
    grouping: bool = typer.Option(
        True,
        "--grouping/--no-grouping",
        help="Enable LLM-based grouping of continued content",
    ),
    temperature: float = typer.Option(
        0.2, help="LLM temperature. Lower makes OCR results more reliable."
    ),
    max_tokens: Optional[int] = typer.Option(
        None, help="LLM max tokens (defaults to config default). Change based on model limitations"
    ),
    concurrency: int = typer.Option(
        4,
        help="Max concurrent LLM requests for page groups. Higher concurrency means faster processing at the risk of hitting rate limits.",
    ),
    grouping_concurrency: Optional[int] = typer.Option(
        None,
        help="Max concurrent LLM requests for adjacent-page continuation checks (defaults to --concurrency)",
    ),
    profile: Optional[str] = typer.Option(
        None, help="Prompt profile name (e.g., 'contracts', 'generic') or path to JSON profile"
    ),
    allow_docx: bool = typer.Option(
        False, help="Allow DOCX via Word/COM conversion (not recommended). Prefer PDFs."
    ),
    # Retry options
    max_retries: int = typer.Option(3, help="Max retry attempts for failed LLM calls"),
    retry_delay: float = typer.Option(
        1.0, help="Initial delay between retries in seconds (exponential backoff)"
    ),
    # Rate limiting
    rate_limit: Optional[int] = typer.Option(
        None, "--rate-limit", help="Max requests per minute (None = no limit)"
    ),
    # Caching
    cache: bool = typer.Option(
        False, "--cache/--no-cache", help="Enable response caching to avoid redundant LLM calls"
    ),
    cache_dir: Optional[str] = typer.Option(
        None, help="Directory for response cache (defaults to ~/.cache/llm-markdownify)"
    ),
    # Logging
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose logging (debug level)"
    ),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Suppress non-error output"),
):
    # Determine log level
    log_level = "normal"
    if quiet:
        log_level = "quiet"
    elif verbose:
        log_level = "verbose"

    cfg_kwargs = dict(
        input_path=Path(input_path),
        output_path=Path(output),
        dpi=dpi,
        max_group_pages=max_group_pages,
        enable_grouping=grouping,
        temperature=temperature,
        concurrency=concurrency,
        allow_docx=allow_docx,
        max_retries=max_retries,
        retry_delay=retry_delay,
        enable_cache=cache,
        log_level=log_level,
    )
    if model:
        cfg_kwargs["model"] = model
    if max_tokens is not None:
        cfg_kwargs["max_tokens"] = max_tokens
    if grouping_concurrency is not None:
        cfg_kwargs["grouping_concurrency"] = grouping_concurrency
    if rate_limit is not None:
        cfg_kwargs["rate_limit_rpm"] = rate_limit
    if cache_dir:
        cfg_kwargs["cache_dir"] = Path(cache_dir)

    cfg = MarkdownifyConfig(**cfg_kwargs)
    Markdownifier(cfg, profile=profile).run()


if __name__ == "__main__":  # pragma: no cover
    app()
