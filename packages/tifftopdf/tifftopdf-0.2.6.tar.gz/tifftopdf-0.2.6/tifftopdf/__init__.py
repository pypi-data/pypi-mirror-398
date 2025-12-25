"""
tifftopdf
---------
Batch pipeline to group TIFFs by blank-page separators and merge them into PDFs.
"""

from __future__ import annotations

from .orchestrator.run import OrchestratorConfig, run_once
from .merging.tiff_to_pdf import merge_tiffs_to_pdf
from .grouping.grouper import (
    group_by_blank_markers,
    GroupingConfig,
    ProcessGroup,
    GroupingSummary,
)
from .scanning.scanner import scan_batch_folder, BatchScanSummary

__all__ = [
    "OrchestratorConfig",
    "run_once",
    "merge_tiffs_to_pdf",
    "group_by_blank_markers",
    "GroupingConfig",
    "ProcessGroup",
    "GroupingSummary",
    "scan_batch_folder",
    "BatchScanSummary",
]

