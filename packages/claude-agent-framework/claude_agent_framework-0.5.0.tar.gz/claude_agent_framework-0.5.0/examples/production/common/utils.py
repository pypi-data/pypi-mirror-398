"""
Common utilities for production examples.

Provides shared functionality across all examples including:
- Configuration loading (YAML)
- Logging setup
- Result saving (JSON, Markdown, PDF)
- Progress indicators
- Error handling
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {config_path}: {e}") from e


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    format_str: str | None = None,
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging output
        format_str: Custom format string

    Returns:
        Configured logger instance
    """
    if format_str is None:
        format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # Create formatter
    formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_file}")

    return root_logger


class ResultSaver:
    """
    Unified result saving interface.

    Supports multiple output formats: JSON, Markdown, PDF.
    """

    def __init__(self, output_dir: Path | str):
        """
        Initialize ResultSaver.

        Args:
            output_dir: Directory for saving results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        result: dict[str, Any],
        format: str = "json",
        filename: str | None = None,
    ) -> Path:
        """
        Save result in specified format.

        Args:
            result: Result data to save
            format: Output format (json, markdown, pdf)
            filename: Optional custom filename

        Returns:
            Path to saved file

        Raises:
            ValueError: If format is not supported
        """
        format = format.lower()

        if filename is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"result_{timestamp}"

        if format == "json":
            return self._save_json(result, filename)
        elif format == "markdown":
            return self._save_markdown(result, filename)
        elif format == "pdf":
            return self._save_pdf(result, filename)
        else:
            raise ValueError(f"Unsupported format: {format}. Supported: json, markdown, pdf")

    def _save_json(self, result: dict, filename: str) -> Path:
        """Save result as JSON file."""
        output_path = self.output_dir / f"{filename}.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to JSON: {output_path}")
        return output_path

    def _save_markdown(self, result: dict, filename: str) -> Path:
        """Save result as Markdown file."""
        output_path = self.output_dir / f"{filename}.md"

        with output_path.open("w", encoding="utf-8") as f:
            f.write(self._format_markdown(result))

        logger.info(f"Results saved to Markdown: {output_path}")
        return output_path

    def _format_markdown(self, result: dict) -> str:
        """Format result dictionary as Markdown."""
        lines = []

        # Title
        if "title" in result:
            lines.append(f"# {result['title']}\n")

        # Summary
        if "summary" in result:
            lines.append("## Summary\n")
            lines.append(f"{result['summary']}\n")

        # Main content
        if "content" in result:
            lines.append("## Content\n")
            if isinstance(result["content"], dict):
                for key, value in result["content"].items():
                    lines.append(f"### {key}\n")
                    lines.append(f"{value}\n")
            else:
                lines.append(f"{result['content']}\n")

        # Metadata
        if "metadata" in result:
            lines.append("## Metadata\n")
            for key, value in result["metadata"].items():
                lines.append(f"- **{key}**: {value}\n")

        return "\n".join(lines)

    def _save_pdf(self, result: dict, filename: str) -> Path:
        """Save result as PDF file."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError:
            raise ImportError(
                "PDF generation requires reportlab. "
                "Install with: pip install 'claude-agent-framework[pdf]'"
            )

        output_path = self.output_dir / f"{filename}.pdf"

        # Create PDF document
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []

        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        body_style = styles["BodyText"]

        # Title
        if "title" in result:
            story.append(Paragraph(result["title"], title_style))
            story.append(Spacer(1, 0.2 * inch))

        # Summary
        if "summary" in result:
            story.append(Paragraph("Summary", heading_style))
            story.append(Paragraph(result["summary"], body_style))
            story.append(Spacer(1, 0.2 * inch))

        # Content
        if "content" in result:
            story.append(Paragraph("Content", heading_style))
            if isinstance(result["content"], dict):
                for key, value in result["content"].items():
                    story.append(Paragraph(key, heading_style))
                    story.append(Paragraph(str(value), body_style))
                    story.append(Spacer(1, 0.1 * inch))
            else:
                story.append(Paragraph(str(result["content"]), body_style))

        # Build PDF
        doc.build(story)

        logger.info(f"Results saved to PDF: {output_path}")
        return output_path


def validate_config(config: dict, required_fields: list[str]) -> None:
    """
    Validate configuration has all required fields.

    Args:
        config: Configuration dictionary
        required_fields: List of required field names

    Raises:
        ValueError: If any required field is missing
    """
    missing = [field for field in required_fields if field not in config]

    if missing:
        raise ValueError(f"Missing required configuration fields: {', '.join(missing)}")


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class ExecutionError(Exception):
    """Raised when execution fails."""

    pass


def extract_message_content(msg: Any) -> str | None:
    """
    Extract string content from SDK message objects.

    Claude Agent SDK returns various message types (ResultMessage, AssistantMessage,
    SystemMessage, etc.) that need to be converted to strings for processing.

    Args:
        msg: SDK message object (ResultMessage, AssistantMessage, etc.)

    Returns:
        Extracted string content or None if no content
    """
    msg_type = type(msg).__name__

    if msg_type == "ResultMessage":
        # ResultMessage has 'result' attribute with final content
        return getattr(msg, "result", None)

    elif msg_type == "AssistantMessage":
        # AssistantMessage has content blocks
        content = getattr(msg, "content", [])
        texts = []
        for block in content:
            if type(block).__name__ == "TextBlock":
                text = getattr(block, "text", "")
                if text:
                    texts.append(text)
        return "\n".join(texts) if texts else None

    elif msg_type in ("ErrorMessage", "Error"):
        # Error messages
        return getattr(msg, "error", None) or getattr(msg, "message", None)

    else:
        # Unknown type - try to convert to string if has result or text
        result = getattr(msg, "result", None)
        if result:
            return str(result)
        text = getattr(msg, "text", None)
        if text:
            return str(text)
        return None
