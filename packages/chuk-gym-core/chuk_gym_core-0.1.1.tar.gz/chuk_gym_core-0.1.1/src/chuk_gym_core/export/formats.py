"""
Export format definitions for dataset generation.
"""

from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats for datasets."""

    JSONL = "jsonl"  # JSON Lines (one record per line)
    JSON = "json"  # Pretty-printed JSON array
    CSV = "csv"  # Comma-separated values
    PARQUET = "parquet"  # Apache Parquet (columnar)

    # Training-specific formats
    CHAT = "chat"  # Chat/conversation format
    QA = "qa"  # Question-answer pairs
    INSTRUCT = "instruct"  # Instruction-following format

    # Framework-specific
    HF_DATASET = "hf_dataset"  # Hugging Face datasets format
