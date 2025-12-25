from __future__ import annotations

import os
import time
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from tifftopdf.utils.helpers import (
    _assert_output_outside_input,
    _ensure_output_roots,
    _resolve_batches,
    resolve_preferred_batches,
    fingerprint_group,
    get_state_path,
    load_state,
    save_state,
    mark_done,
    atomic_write_pdf,
)
from tifftopdf.utils.logging import get_logger
from tifftopdf.models import (
    OrchestratorConfig,
    RunResult,
    BatchResult,
    ProcessPdfResult,
    GroupingSummary,
    BatchScanSummary,
    ResumeState,
)
from tifftopdf.scanning.scanner import scan_batch_folder, ScannerError
from tifftopdf.grouping.grouper import (
    group_by_blank_markers,
    GroupingConfig as GroupingCfg,
    ProcessGroup,
    GroupingError,
)
from tifftopdf.merging.tiff_to_pdf import merge_tiffs_to_pdf, TiffToPdfError
from tifftopdf.reporting.metadata_writer import (
    MetadataWriterConfig,
    build_batch_metadata,
    build_run_metadata,
    write_json,
)
from tifftopdf.reporting.query import get_processed_batches

log = get_logger(__name__)


def run_once(cfg: OrchestratorConfig) -> RunResult:
    started_at = time.time()

    if not os.path.isdir(cfg.input_root):
        raise ValueError(f"input_root not found or not a directory: {cfg.input_root}")

    os.makedirs(cfg.output_root, exist_ok=True)
    _assert_output_outside_input(cfg.input_root, cfg.output_root)

    pdf_root, meta_root = _ensure_output_roots(cfg)

    # Discover all batches, then resolve preferred ones (original vs copies)
    _ = _resolve_batches(cfg)  # (kept for side-effects/consistency if any)
    batches = resolve_preferred_batches(cfg.input_root)

    # --- Fast Resume Optimization ---
    if cfg.resume and not cfg.force:
        log.info("Scanning metadata files for resume...")
        processed_names = set(get_processed_batches(meta_root, "."))
        initial_count = len(batches)
        batches = [b for b in batches if b[0] not in processed_names]
        skipped_count = initial_count - len(batches)
        if skipped_count > 0:
            log.info("Resume: Skipping %d already completed batches.", skipped_count)

    # Load resume state (or fresh)
    state_path = get_state_path(meta_root, cfg.state_filename)
    state: ResumeState = load_state(state_path) if cfg.resume else ResumeState()

    meta_cfg = MetadataWriterConfig(
        include_blank_map=cfg.include_blank_map,
        pretty=True,
        sort_keys=True,
    )

    log.info("Preparing to start conversion...")
    log.info("Batches discovered: %d", len(batches))

    # Tracking variables instead of accumulating heavy data
    batch_results: List[BatchResult] = []
    batch_count = 0
    batch_success_count = 0
    total_processes_count = 0

    for batch_name, batch_path in batches:
        bstart = time.time()
        process_results: List[ProcessPdfResult] = []
        batch_success = True
        batch_error = None

        # --- Scan this batch ---
        try:
            scan_summary = scan_batch_folder(batch_path, recursive=cfg.recursive_scan)
        except ScannerError as e:
            batch_success = False
            batch_error = f"scan_error:{e}"
            empty_scan = BatchScanSummary(
                batch_path=batch_path,
                total_files=0,
                total_blank=0,
                total_nonblank=0,
                blank_map={},
            )
            empty_group = GroupingSummary(
                total_files=0,
                total_blank=0,
                total_nonblank=0,
                process_count=0,
                groups_with_blank_terminator=0,
                groups_without_terminator=0,
                blank_only_groups=0,
            )
            batch_result = BatchResult(
                batch_name=batch_name,
                batch_path=batch_path,
                scan=empty_scan,
                grouping=empty_group,
                process_pdfs=[],
                success=False,
                error=batch_error,
                started_at=bstart,
                finished_at=time.time(),
            )

            # Stream: write metadata ASAP for failed scan
            if cfg.write_per_batch_metadata:
                per_batch_meta_path = os.path.join(meta_root, f"{batch_name}.json")
                write_json(
                    per_batch_meta_path,
                    build_batch_metadata(batch_result, meta_cfg),
                    pretty=meta_cfg.pretty,
                    sort_keys=meta_cfg.sort_keys,
                )

            # Keep minimal batch info for final report
            batch_results.append(batch_result)
            batch_count += 1
            log.error("[Batch %s] scan failed: %s", batch_name, e)
            continue

        files_sorted = sorted(scan_summary.blank_map.keys())

        # --- Group this batch ---
        try:
            grouping_cfg = GroupingCfg(
                zero_pad_width=cfg.zero_pad_width,
                allow_blank_only_groups=cfg.allow_blank_only_groups,
            )
            groups, grouping_summary = group_by_blank_markers(
                files_sorted=files_sorted,
                is_blank_map=scan_summary.blank_map,
                cfg=grouping_cfg,
            )
        except GroupingError as e:
            batch_success = False
            batch_error = f"grouping_error:{e}"
            empty_group = GroupingSummary(
                total_files=scan_summary.total_files,
                total_blank=scan_summary.total_blank,
                total_nonblank=scan_summary.total_nonblank,
                process_count=0,
                groups_with_blank_terminator=0,
                groups_without_terminator=0,
                blank_only_groups=0,
            )

            # Release large dictionaries early
            scan_summary.blank_map = {}
            del files_sorted

            batch_result = BatchResult(
                batch_name=batch_name,
                batch_path=batch_path,
                scan=scan_summary,
                grouping=empty_group,
                process_pdfs=[],
                success=False,
                error=batch_error,
                started_at=bstart,
                finished_at=time.time(),
            )

            if cfg.write_per_batch_metadata:
                per_batch_meta_path = os.path.join(meta_root, f"{batch_name}.json")
                write_json(
                    per_batch_meta_path,
                    build_batch_metadata(batch_result, meta_cfg),
                    pretty=meta_cfg.pretty,
                    sort_keys=meta_cfg.sort_keys,
                )

            batch_results.append(batch_result)
            batch_count += 1
            log.error("[Batch %s] grouping failed: %s", batch_name, e)
            continue

        # Release large structures after grouping
        scan_summary.blank_map = {}
        del files_sorted

        total_processes_count += grouping_summary.process_count
        log.info(
            "[Batch %s] processes to create: %d",
            batch_name,
            grouping_summary.process_count,
        )

        # --- Merge this batch ---
        batch_pdf_dir = os.path.join(pdf_root, batch_name)
        os.makedirs(batch_pdf_dir, exist_ok=True)

        def _merge_one(g: ProcessGroup) -> ProcessPdfResult:
            out_pdf = os.path.join(cfg.output_root, f"INPS_{batch_name}_{g.group_id}.pdf")
            files = list(g.files)
            fpr = fingerprint_group(files)

            # Resume fast-path: skip if already completed with same fingerprint and file exists
            if cfg.resume and not cfg.force:
                k = f"{batch_name}:{g.group_id}"
                st = state.groups.get(k)
                if st and st.success and st.fingerprint == fpr and os.path.isfile(out_pdf):
                    # Consider it done; do not retain input_files to save memory
                    return ProcessPdfResult(
                        group_id=g.group_id,
                        input_files=[],
                        output_pdf=out_pdf,
                        success=True,
                        error=None,
                    )

            try:
                # Atomic write: produce to tmp and move to final
                def writer(tmp_path: str):
                    merge_tiffs_to_pdf(files, tmp_path)

                atomic_write_pdf(out_pdf, writer)

                # Mark done & checkpoint incrementally
                if cfg.resume:
                    mark_done(state, batch_name, g.group_id, out_pdf, files, fpr)
                    save_state(state_path, state)

                # On success we don't retain input list
                return ProcessPdfResult(
                    group_id=g.group_id,
                    input_files=[],
                    output_pdf=out_pdf,
                    success=True,
                    error=None,
                )
            except TiffToPdfError as e:
                # On failure retain inputs for diagnostics
                return ProcessPdfResult(
                    group_id=g.group_id,
                    input_files=files,
                    output_pdf=out_pdf,
                    success=False,
                    error=str(e),
                )

        log.info(
            "[Batch %s] starting merge: %d process(es) to create",
            batch_name,
            len(groups),
        )

        created = 0
        total = len(groups)
        max_workers = max(1, cfg.max_workers)

        def _handle_result(res: ProcessPdfResult) -> None:
            nonlocal created, batch_success
            process_results.append(res)
            if res.success:
                created += 1
            else:
                batch_success = False
            log.info("[Batch %s] created %d/%d", batch_name, created, total)

        if max_workers == 1:
            for g in groups:
                _handle_result(_merge_one(g))
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(_merge_one, g): g for g in groups}
                for fut in as_completed(futures):
                    _handle_result(fut.result())
                futures.clear()
                del futures

        del groups

        bfinish = time.time()

        # Build the batch_result (full)
        batch_result = BatchResult(
            batch_name=batch_name,
            batch_path=batch_path,
            scan=scan_summary,
            grouping=grouping_summary,
            process_pdfs=sorted(process_results, key=lambda x: x.group_id),
            success=batch_success,
            error=None if batch_success else (batch_error or "merge_error"),
            started_at=bstart,
            finished_at=bfinish,
        )

        # Stream results — write per-batch metadata immediately
        if cfg.write_per_batch_metadata:
            per_batch_meta_path = os.path.join(meta_root, f"{batch_name}.json")
            write_json(
                per_batch_meta_path,
                build_batch_metadata(batch_result, meta_cfg),
                pretty=meta_cfg.pretty,
                sort_keys=meta_cfg.sort_keys,
            )

        if batch_success:
            log.info("[Batch %s] done", batch_name)
        else:
            log.error("[Batch %s] done with errors", batch_name)

        # Keep only essential metadata for the final report, not full process details
        batch_result_lean = BatchResult(
            batch_name=batch_result.batch_name,
            batch_path=batch_result.batch_path,
            scan=BatchScanSummary(
                batch_path=batch_result.scan.batch_path,
                total_files=batch_result.scan.total_files,
                total_blank=batch_result.scan.total_blank,
                total_nonblank=batch_result.scan.total_nonblank,
                blank_map={},  # Don't retain this
            ),
            grouping=batch_result.grouping,
            process_pdfs=[],  # Already persisted in per-batch JSON
            success=batch_result.success,
            error=batch_result.error,
            started_at=batch_result.started_at,
            finished_at=batch_result.finished_at,
        )

        batch_results.append(batch_result_lean)
        batch_count += 1
        if batch_success:
            batch_success_count += 1

        # Explicitly delete heavy locals
        del process_results
        del batch_result
        del batch_result_lean
        del scan_summary
        del grouping_summary

    finished_at = time.time()
    run_success = batch_success_count == batch_count or all(b.success for b in batch_results)

    total_batches = len(batch_results)

    log.info("Conversion finished.")
    log.info(
        "Global summary: batches=%d, processes=%d",
        total_batches,
        total_processes_count,
    )

    run_result = RunResult(
        input_root=cfg.input_root,
        output_root=cfg.output_root,
        batch_count=total_batches,
        batches=batch_results,
        started_at=started_at,
        finished_at=finished_at,
        success=run_success,
    )

    if cfg.write_run_metadata:
        run_meta_path = os.path.join(meta_root, "run.json")
        write_json(
            run_meta_path,
            build_run_metadata(run_result, meta_cfg),
            pretty=meta_cfg.pretty,
            sort_keys=meta_cfg.sort_keys,
        )

    # Save final state snapshot (optional; per-group already saved incrementally)
    if cfg.resume:
        save_state(state_path, state)

    return run_result
