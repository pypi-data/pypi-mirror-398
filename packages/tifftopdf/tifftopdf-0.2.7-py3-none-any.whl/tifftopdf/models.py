from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

class TiffToPdfError(Exception):
    pass


@dataclass
class BatchScanSummary:
    batch_path: str
    total_files: int
    total_blank: int
    total_nonblank: int
    blank_map: Dict[str, bool]


class ScannerError(Exception):
    pass


@dataclass(frozen=True)
class OrchestratorConfig:
    input_root: str
    output_root: str
    recursive_scan: bool = False
    max_workers: int = 1
    zero_pad_width: int = 3
    allow_blank_only_groups: bool = False
    write_per_batch_metadata: bool = True
    write_run_metadata: bool = True
    pdf_subdir_name: str = "pdf"
    meta_subdir_name: str = "metadata"
    allow_root_as_single_batch: bool = False
    include_blank_map: bool = False
    resume: bool = True
    force: bool = False
    state_filename: str = "run_state.json"
    verify_existing: bool = False
    metadata_root: Optional[str] = None  


@dataclass
class ProcessPdfResult:
    group_id: str
    input_files: List[str]
    output_pdf: str
    success: bool
    error: str | None = None


@dataclass
class BatchResult:
    batch_name: str
    batch_path: str
    scan: BatchScanSummary
    grouping: GroupingSummary
    process_pdfs: List[ProcessPdfResult]
    success: bool
    error: str | None = None
    started_at: float = 0.0
    finished_at: float = 0.0


@dataclass
class RunResult:
    input_root: str
    output_root: str
    batch_count: int
    batches: List[BatchResult]
    started_at: float
    finished_at: float
    success: bool

@dataclass(frozen=True)
class GroupingConfig:
    zero_pad_width: int = 3        
    allow_blank_only_groups: bool = False


@dataclass(frozen=True)
class ProcessGroup:
    group_id: str
    files: Tuple[str, ...]


@dataclass(frozen=True)
class GroupingSummary:
    total_files: int
    total_blank: int
    total_nonblank: int
    process_count: int
    groups_with_blank_terminator: int 
    groups_without_terminator: int
    blank_only_groups: int


class GroupingError(Exception):
    pass

@dataclass(frozen=True)
class GroupKey:
    batch_name: str
    group_id: str

    def key(self) -> str:
        return f"{self.batch_name}:{self.group_id}"

@dataclass
class GroupStatus:
    success: bool
    output_pdf: str
    input_files: List[str]
    fingerprint: str
    finished_at: float

@dataclass
class ResumeState:
    # mapa "batch:group_id" -> estado
    groups: Dict[str, GroupStatus] = field(default_factory=dict)
