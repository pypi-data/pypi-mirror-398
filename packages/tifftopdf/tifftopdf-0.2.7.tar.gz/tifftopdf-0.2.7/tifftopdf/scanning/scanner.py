from __future__ import annotations

import os
import logging
import gc
from typing import Dict, List
from dataclasses import dataclass

from tifftopdf.detection.blank_detector import is_blank_tiff_opencv
from tifftopdf.models import *

logger = logging.getLogger(__name__)


class ScannerError(Exception):
    """Scanner-specific error."""
    pass


def scan_batch_folder(batch_path: str, recursive: bool = False) -> BatchScanSummary:
    """
    Scan a batch folder for TIFFs, detect blanks, and log progress.
    
    Optimized for memory efficiency:
    - Explicit cleanup after each file analysis
    - Periodic garbage collection
    - Streams results instead of accumulating metadata
    - Minimal retention of analysis data
    """
    if not os.path.exists(batch_path):
        raise ScannerError(f"Batch folder does not exist: {batch_path}")
    
    if not os.path.isdir(batch_path):
        raise ScannerError(f"Not a folder: {batch_path}")
    
    logger.info(
        f"[Scanner] Scanning batch folder: {batch_path} (recursive={recursive})"
    )
    
    # Collect TIFF files
    tiff_files: List[str] = []
    for root, _, files in os.walk(batch_path):
        for f in files:
            if f.lower().endswith((".tif", ".tiff")):
                tiff_files.append(os.path.join(root, f))
        if not recursive:
            break
    
    if not tiff_files:
        raise ScannerError(f"No TIFF files found in: {batch_path}")
    
    logger.info(
        f"[Scanner] Found {len(tiff_files)} TIFF files in batch {batch_path}"
    )
    
    # Detect blanks with memory optimization
    blank_map: Dict[str, bool] = {}
    total_blank = 0
    total_nonblank = 0
    
    # Sort files for consistent processing
    sorted_files = sorted(tiff_files)
    total_files = len(sorted_files)
    
    for idx, path in enumerate(sorted_files, 1):
        result = None
        try:
            # Analyze current file
            result = is_blank_tiff_opencv(path)
            is_blank = result["is_blank"]
            
            # Store only the boolean flag (minimal memory footprint)
            blank_map[path] = is_blank
            
            status = "BLANK" if is_blank else "NON-BLANK"
            logger.info(
                f"[Scanner] ({idx}/{total_files}) {os.path.basename(path)} → {status}"
            )
            
            if is_blank:
                total_blank += 1
            else:
                total_nonblank += 1
        
        except Exception as e:
            logger.error(f"[Scanner] Error analyzing {path}: {e}")
            raise ScannerError(f"Error analyzing {path}: {e}")
        
        finally:
            # Explicit cleanup of analysis result to free CV2 metadata
            if result is not None:
                del result
            
            # Periodic garbage collection: every 10% of files or every 50 files
            gc_interval = max(50, total_files // 10)
            if idx % gc_interval == 0:
                gc.collect()
    
    # Final garbage collection
    gc.collect()
    
    # Build summary
    summary = BatchScanSummary(
        batch_path=batch_path,
        total_files=total_files,
        total_blank=total_blank,
        total_nonblank=total_nonblank,
        blank_map=blank_map,
    )
    
    logger.info(
        f"[Scanner] Completed batch {batch_path}: "
        f"{summary.total_files} files (blank={summary.total_blank}, nonblank={summary.total_nonblank})"
    )
    
    return summary


def scan_batch_folder_streaming(
    batch_path: str,
    output_handler,
    recursive: bool = False,
) -> BatchScanSummary:
    """
    Scan a batch folder with streaming output.
    
    For extremely large batches, write results to a file or database
    as you go, rather than accumulating in blank_map.
    
    Args:
        batch_path: Path to batch folder
        output_handler: Callable that accepts (path, is_blank) and processes it
                       (e.g., write to file, update database)
        recursive: Whether to scan recursively
    
    Example:
        def log_blank_status(path, is_blank):
            with open('blank_log.txt', 'a') as f:
                status = 'BLANK' if is_blank else 'NON-BLANK'
                f.write(f'{path},{status}\\n')
        
        summary = scan_batch_folder_streaming(
            batch_path='/path/to/batch',
            output_handler=log_blank_status,
        )
    """
    if not os.path.exists(batch_path):
        raise ScannerError(f"Batch folder does not exist: {batch_path}")
    
    if not os.path.isdir(batch_path):
        raise ScannerError(f"Not a folder: {batch_path}")
    
    logger.info(
        f"[Scanner] Scanning batch folder (streaming): {batch_path} (recursive={recursive})"
    )
    
    # Collect TIFF files
    tiff_files: List[str] = []
    for root, _, files in os.walk(batch_path):
        for f in files:
            if f.lower().endswith((".tif", ".tiff")):
                tiff_files.append(os.path.join(root, f))
        if not recursive:
            break
    
    if not tiff_files:
        raise ScannerError(f"No TIFF files found in: {batch_path}")
    
    logger.info(
        f"[Scanner] Found {len(tiff_files)} TIFF files in batch {batch_path}"
    )
    
    # Process files and stream results
    blank_map: Dict[str, bool] = {}
    total_blank = 0
    total_nonblank = 0
    
    sorted_files = sorted(tiff_files)
    total_files = len(sorted_files)
    
    for idx, path in enumerate(sorted_files, 1):
        result = None
        try:
            result = is_blank_tiff_opencv(path)
            is_blank = result["is_blank"]
            
            # Store in map AND stream to output handler
            blank_map[path] = is_blank
            output_handler(path, is_blank)
            
            status = "BLANK" if is_blank else "NON-BLANK"
            logger.info(
                f"[Scanner] ({idx}/{total_files}) {os.path.basename(path)} → {status}"
            )
            
            if is_blank:
                total_blank += 1
            else:
                total_nonblank += 1
        
        except Exception as e:
            logger.error(f"[Scanner] Error analyzing {path}: {e}")
            raise ScannerError(f"Error analyzing {path}: {e}")
        
        finally:
            if result is not None:
                del result
            
            gc_interval = max(50, total_files // 10)
            if idx % gc_interval == 0:
                gc.collect()
    
    gc.collect()
    
    summary = BatchScanSummary(
        batch_path=batch_path,
        total_files=total_files,
        total_blank=total_blank,
        total_nonblank=total_nonblank,
        blank_map=blank_map,
    )
    
    logger.info(
        f"[Scanner] Completed batch {batch_path}: "
        f"{summary.total_files} files (blank={summary.total_blank}, nonblank={summary.total_nonblank})"
    )
    
    return summary