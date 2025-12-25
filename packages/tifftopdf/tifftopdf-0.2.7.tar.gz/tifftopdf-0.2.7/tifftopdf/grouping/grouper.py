from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
from tifftopdf.models import *


def _gid(n: int, width: int) -> str:
    return f"{n:0{width}d}"


def group_by_blank_markers(
    files_sorted: Sequence[str],
    is_blank_map: Dict[str, bool],
    cfg: Optional[GroupingConfig] = None,
) -> Tuple[List[ProcessGroup], GroupingSummary]:

    if cfg is None:
        cfg = GroupingConfig()

    # Validate completeness
    missing = [p for p in files_sorted if p not in is_blank_map]
    if missing:
        raise GroupingError(
            f"is_blank_map missing entries for: {missing[:5]}{' ...' if len(missing) > 5 else ''}"
        )

    total_files = len(files_sorted)
    total_blank = sum(1 for p in files_sorted if is_blank_map[p])
    total_nonblank = total_files - total_blank

    groups: List[ProcessGroup] = []
    buffer: List[str] = []
    next_group_index = 1

    groups_with_blank_terminator = 0
    groups_without_terminator = 0
    blank_only_groups = 0

    for path in files_sorted:
        is_blank = is_blank_map[path]

        if is_blank:
            if not buffer:
                # Blank arrives without any accumulated content pages.
                if cfg.allow_blank_only_groups:
                    groups.append(ProcessGroup(_gid(next_group_index, cfg.zero_pad_width), (path,)))
                    next_group_index += 1
                    blank_only_groups += 1
                # else: ignore stray blank (nothing to close)
                continue

            # Close the current process with this blank terminator
            buffer.append(path)  # include the blank at the end
            groups.append(ProcessGroup(_gid(next_group_index, cfg.zero_pad_width), tuple(buffer)))
            next_group_index += 1
            groups_with_blank_terminator += 1
            buffer.clear()

        else:
            # Content page: keep accumulating
            buffer.append(path)

    # close a final group WITHOUT a blank terminator
    if buffer:
        groups.append(ProcessGroup(_gid(next_group_index, cfg.zero_pad_width), tuple(buffer)))
        next_group_index += 1
        groups_without_terminator += 1
        buffer.clear()

    summary = GroupingSummary(
        total_files=total_files,
        total_blank=total_blank,
        total_nonblank=total_nonblank,
        process_count=len(groups),
        groups_with_blank_terminator=groups_with_blank_terminator,
        groups_without_terminator=groups_without_terminator,
        blank_only_groups=blank_only_groups,
    )
    return groups, summary
