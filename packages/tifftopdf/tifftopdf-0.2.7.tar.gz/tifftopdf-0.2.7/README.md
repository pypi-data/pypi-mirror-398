## **README.md — TIFF to PDF Conversion Pipeline**

### Overview

`TIFFtoPDF` is a modular, extensible Python library and CLI tool that automates the conversion of scanned TIFF batches into structured PDFs.
It detects blank separator pages, groups files into processes, merges them, and generates metadata for auditing and integration.

### Key Features

* Detects blank TIFF pages using **OpenCV** variance and pixel thresholding.
* Groups documents based on blank separators.
* Merges multi-page TIFFs into PDFs per process.
* Automatically logs progress with per-batch verbosity.
* Generates detailed JSON metadata for each batch and global runs.

---
## Pipeline Summary

| Stage       | Module               | Description                     |
| ----------- | -------------------- | ------------------------------- |
| Scan        | `scanner.py`         | Reads TIFFs, detects blanks     |
| Group       | `grouper.py`         | Groups documents by blank pages |
| Merge       | `tiff_to_pdf.py`     | Creates process-level PDFs      |
| Report      | `metadata_writer.py` | Builds structured metadata      |
| Orchestrate | `run.py`             | Coordinates pipeline execution  |
| CLI         | `cli.py`             | Exposes command-line interface  |

---

## **Module Architecture**

### `tifftopdf/cli.py`

Command-line entry point for running the pipeline.

#### Usage

```bash
tifftopdf --input-root <path/to/input> --output-root <path/to/output> -v
```

#### Parameters

* `--input-root` : Path containing batches or single batch folders.
* `--output-root` : Destination folder for PDFs and metadata.
* `-v / --verbose` : Enables detailed progress logs.

This module invokes the main orchestrator (`run_once` from `orchestrator/run.py`) and sets up logging verbosity.

---

### `tifftopdf/models.py`

Defines shared data structures and error types across modules.

#### Key Classes

| Class                           | Purpose                                                    |
| ------------------------------- | ---------------------------------------------------------- |
| `TiffToPdfError`                | Base exception for merge errors.                           |
| `ScannerError`, `GroupingError` | Error wrappers for scanning and grouping failures.         |
| `BatchScanSummary`              | Holds per-batch scan statistics (blank vs nonblank).       |
| `GroupingSummary`               | Tracks grouping statistics and counts.                     |
| `ProcessPdfResult`              | Captures result for a single process merge (success/fail). |
| `BatchResult`, `RunResult`      | Aggregate statistics for entire run.                       |

---

### `tifftopdf/detection/blank_detector.py`

Implements **blank page detection** using OpenCV.

#### Function: `is_blank_tiff_opencv(path: str, variance_thr=3.0, nonwhite_thr=0.002, white_threshold=245, crop_px=16, crop_ratio=0.01)`

Detects whether a TIFF is blank by analyzing pixel intensity variance and the ratio of non-white pixels.

**Parameters**

* `path` : Path to TIFF image.
* `variance_thr` : Max pixel variance for considering the page blank.
* `nonwhite_thr` : Max ratio of non-white pixels.
* `white_threshold` : Threshold for "white" pixels (0–255 scale).
* `crop_px` : Pixels cropped from each border to ignore edge noise.
* `crop_ratio` : Crop proportion of min dimension if greater than `crop_px`.

**Returns**

```python
{
    "path": str,
    "variance": float,
    "nonwhite_ratio": float,
    "is_blank": bool
}
```

---

### `tifftopdf/scanning/scanner.py`

Scans a batch folder, detects blank pages, and logs progress.

#### Function: `scan_batch_folder(batch_path: str, recursive=False) -> BatchScanSummary`

* Walks through a directory (optionally recursively).
* Filters `.tif` and `.tiff` files.
* Calls `is_blank_tiff_opencv()` for each.
* Logs every file analyzed and its status (`BLANK` / `NON-BLANK`).

**Logs e.g: **

```
[Scanner] (1/35) doc001.tif → NON-BLANK
[Scanner] (2/35) separator.tif → BLANK
```

---

### `tifftopdf/grouping/grouper.py`

Groups TIFF files into logical document processes separated by blank pages.

#### Function: `group_by_blank_markers(files_sorted, is_blank_map, cfg)`

Creates groups where each blank page acts as a separator.

**Config options**

* `zero_pad_width` : Number width for process IDs (e.g., `001`).
* `allow_blank_only_groups` : Whether groups with only blank pages are valid.

**Returns**

* A list of `ProcessGroup` objects.
* A `GroupingSummary` with totals.

---

### `tifftopdf/merging/tiff_to_pdf.py`

Merges one or more TIFFs into a single multi-page PDF.

#### Function: `merge_tiffs_to_pdf(tiff_paths: List[str], output_pdf: str)`

Uses Pillow to open TIFFs, iterate over all frames, convert to RGB, and append them as pages to the output PDF.

Raises:

* `TiffToPdfError` if any input file is missing or corrupted.

---

### `tifftopdf/reporting/metadata_writer.py`

Creates detailed JSON metadata files summarizing each batch and full run.

#### Key Functions

* `build_batch_metadata(batch_result, cfg)` → Dict with file and process stats.
* `build_run_metadata(run_result, cfg)` → Aggregated summary.
* `write_json(path, data, pretty=True)` → Writes metadata to disk.

Metadata includes:

* File counts
* Blank and nonblank statistics
* Processing time
* PDF paths generated

---

### `tifftopdf/orchestrator/run.py`

The **central orchestrator** of the pipeline.
Coordinates scanning, grouping, merging, and reporting 
#### Function: `run_once(cfg: OrchestratorConfig) -> RunResult`

Pipeline flow:

1. **Initialize**

   * Validate paths and prepare output directories.
2. **Per-batch execution**

   * Scan TIFFs → detect blanks.
   * Group pages into logical processes.
   * Immediately merge into PDFs.
   * Write per-batch metadata.
3. **Completion**

   * Generate global run summary.

**Config (OrchestratorConfig)**

| Param              | Description                                  |
| ------------------ | -------------------------------------------- |
| `input_root`       | Root folder containing batch directories.    |
| `output_root`      | Destination root for PDFs and metadata.      |
| `recursive_scan`   | Recurse into nested folders.                 |
| `max_workers`      | Parallel merges per batch.                   |
| `zero_pad_width`   | ID padding (e.g., `001`).                    |
| `pdf_subdir_name`  | Subfolder name for PDFs.                     |
| `meta_subdir_name` | Subfolder for metadata.                      |
| `verbose`          | Enables live logging via `utils/logging.py`. |

**Verbose Logging**
During execution:

```
Preparing to start conversion...
Plan ready. Batches: 4 | Processes to create: 130
[Batch 000000573] starting merge: 30 process(es)
[Batch 000000573] created 10/30
...
Conversion finished.
Global summary: batches=4 (ok=4, failed=0), processes=130
```

---

### `tifftopdf/utils/logging.py`

Custom logging setup for CLI and internal modules.

#### Function: `setup_logging(verbose: bool)`

Configures a global logger (`tifftopdf`) with timestamped output:

```
2025-10-03 10:59:41,242 | INFO | tifftopdf.orchestrator.run | [Batch 573] created 30/30
```

---

### `tifftopdf/utils/helpers.py`

Small utility helpers and path manipulation utilities for use throughout the codebase.

---

## Installation

### Build

```bash
python -m build
```

### Local install

```bash
pip install dist/tifftopdf-0.1.2-py3-none-any.whl
```

### Run via CLI

```bash
tifftopdf --input-root "./input_batches" --output-root "./output_results" -v
```