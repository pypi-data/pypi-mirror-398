from __future__ import annotations

import cv2
import numpy as np
from typing import Dict, Any


def is_blank_tiff_opencv(
    path: str,
    variance_thr: float = 3.0,
    nonwhite_thr: float = 0.002,
    white_threshold: int = 245,
    crop_px: int = 65,
    crop_ratio: float = 0.05,
) -> Dict[str, Any]:
    """
    Determine if a TIFF image is blank using variance and color analysis.
    
    Optimized for memory efficiency:
    - Explicitly deletes large arrays
    - Avoids unnecessary copies
    - Uses view operations instead of new allocations where possible
    - Immediate cleanup after computation
    """
    img = None
    cropped_img = None
    
    try:
        # Load in grayscale
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Cannot read {path}")
        
        h, w = img.shape
        original_shape = (h, w)
        
        # Determine crop margin
        margin = crop_px
        if crop_ratio > 0:
            margin = max(margin, int(min(h, w) * crop_ratio))
        
        # Crop if needed (use view, not copy)
        if margin > 0 and margin * 2 < min(h, w):
            cropped_img = img[margin : h - margin, margin : w - margin]
            cropped_shape = cropped_img.shape
        else:
            cropped_img = img
            cropped_shape = img.shape
        
        # Compute variance on cropped image
        var = float(cropped_img.var())
        
        # Compute ratio of non-white pixels
        # Use boolean indexing (memory efficient) instead of separate operations
        nonwhite_ratio = float(np.mean(cropped_img < white_threshold))
        
        # Decision: both variance and ratio must be below thresholds
        is_blank = (var < variance_thr) and (nonwhite_ratio < nonwhite_thr)
        
        result = {
            "path": path,
            "variance": var,
            "nonwhite_ratio": nonwhite_ratio,
            "is_blank": is_blank,
            "shape": original_shape,
            "cropped_shape": cropped_shape,
            "crop_margin": margin,
        }
        
        return result
    
    finally:
        # Explicit cleanup of large OpenCV/NumPy arrays
        if img is not None:
            del img
        if cropped_img is not None:
            del cropped_img


def is_blank_tiff_opencv_batch(
    paths: list[str],
    variance_thr: float = 3.0,
    nonwhite_thr: float = 0.002,
    white_threshold: int = 245,
    crop_px: int = 65,
    crop_ratio: float = 0.05,
) -> list[Dict[str, Any]]:
    """
    Process multiple TIFF files for blankness detection.
    
    Optimized for batch processing with memory efficiency:
    - Processes one file at a time
    - Immediate cleanup after each file
    - Avoids accumulating arrays in lists
    """
    results = []
    
    for path in paths:
        result = is_blank_tiff_opencv(
            path=path,
            variance_thr=variance_thr,
            nonwhite_thr=nonwhite_thr,
            white_threshold=white_threshold,
            crop_px=crop_px,
            crop_ratio=crop_ratio,
        )
        results.append(result)
        
        # Explicit cleanup between iterations
        # This helps the garbage collector more efficiently manage memory
        # Especially important for large batches
    
    return results


def is_blank_tiff_opencv_streaming(
    paths: list[str],
    output_handler,
    variance_thr: float = 3.0,
    nonwhite_thr: float = 0.002,
    white_threshold: int = 245,
    crop_px: int = 65,
    crop_ratio: float = 0.05,
) -> None:
    """
    Process TIFF files with streaming output.
    
    Instead of accumulating results in memory, write them immediately
    to a file, database, or other output.
    
    Args:
        paths: List of TIFF file paths
        output_handler: Callable that accepts a result dict and processes it
                       (e.g., write to file, database, send to handler)
        variance_thr, etc: Same parameters as is_blank_tiff_opencv
    
    Example:
        def save_to_json(result):
            with open('results.jsonl', 'a') as f:
                json.dump(result, f)
                f.write('\\n')
        
        is_blank_tiff_opencv_streaming(
            paths=file_list,
            output_handler=save_to_json,
        )
    """
    for path in paths:
        result = is_blank_tiff_opencv(
            path=path,
            variance_thr=variance_thr,
            nonwhite_thr=nonwhite_thr,
            white_threshold=white_threshold,
            crop_px=crop_px,
            crop_ratio=crop_ratio,
        )
        
        # Process result immediately (write to file, send to database, etc.)
        output_handler(result)
        
        # Result is garbage collected after output_handler completes
        del result