from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Optional, Union




class MetadataWriterConfig:

    def __init__(
        self,
        *,
        include_blank_map: bool = False,
        pretty: bool = True,
        sort_keys: bool = True,
    ) -> None:
        self.include_blank_map = include_blank_map
        self.pretty = pretty
        self.sort_keys = sort_keys





def _maybe_dataclass_to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    return obj


def write_json(path: str, data: Dict[str, Any], *, pretty: bool = True, sort_keys: bool = True) -> None:

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=sort_keys)
        else:
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False, sort_keys=sort_keys)
    os.replace(tmp, path)




def build_batch_metadata(batch_result: Any, cfg: MetadataWriterConfig) -> Dict[str, Any]:

    scan = batch_result.scan
    grouping = _maybe_dataclass_to_dict(batch_result.grouping)

    # Build processes list with optional checksums
    processes = []
    for p in batch_result.process_pdfs:
        proc: Dict[str, Any] = {
            "group_id": p.group_id,
            "input_files": list(p.input_files),
            "output_pdf": p.output_pdf,
            "success": p.success,
            "error": p.error,
        }

        processes.append(proc)

    meta: Dict[str, Any] = {
        "batch_name": batch_result.batch_name,
        "batch_path": batch_result.batch_path,
        "started_at": batch_result.started_at,
        "finished_at": batch_result.finished_at,
        "duration_s": max(0.0, (batch_result.finished_at or 0) - (batch_result.started_at or 0)),
        "success": batch_result.success,
        "error": batch_result.error,
        "scan": {
            "batch_path": scan.batch_path,
            "total_files": scan.total_files,
            "total_blank": scan.total_blank,
            "total_nonblank": scan.total_nonblank,
        },
        "grouping": grouping,
        "processes": processes,
    }

    if cfg.include_blank_map:
        meta["scan"]["blank_map"] = dict(scan.blank_map)

    return meta


def build_run_metadata(run_result: Any, cfg: MetadataWriterConfig) -> Dict[str, Any]:

    batches_meta = []
    for b in run_result.batches:
        batches_meta.append({
            "batch_name": b.batch_name,
            "batch_path": b.batch_path,
            "success": b.success,
            "error": b.error,
            "scan": {
                "total_files": b.scan.total_files,
                "total_blank": b.scan.total_blank,
                "total_nonblank": b.scan.total_nonblank,
            },
            "grouping": _maybe_dataclass_to_dict(b.grouping),
            "process_count": len(b.process_pdfs),
        })

    meta = {
        "input_root": run_result.input_root,
        "output_root": run_result.output_root,
        "batch_count": run_result.batch_count,
        "started_at": run_result.started_at,
        "finished_at": run_result.finished_at,
        "duration_s": max(0.0, (run_result.finished_at or 0) - (run_result.started_at or 0)),
        "success": run_result.success,
        "batches": batches_meta,
    }
    return meta
