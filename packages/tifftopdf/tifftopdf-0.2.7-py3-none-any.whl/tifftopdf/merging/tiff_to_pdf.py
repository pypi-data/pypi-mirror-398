from __future__ import annotations

import gc
import os
import tempfile
from typing import List

from PIL import Image

from tifftopdf.models import TiffToPdfError

DEFAULT_MAX_IMAGES_IN_MEMORY = 50


def merge_tiffs_to_pdf(
    tiff_paths: List[str],
    output_pdf: str,
    *,
    max_images_in_memory: int = DEFAULT_MAX_IMAGES_IN_MEMORY,
) -> None:
    """Convert TIFFs into a PDF while capping how many pages stay in memory."""

    return _merge_tiffs_streamed(
        tiff_paths,
        output_pdf,
        max_images_in_memory=max_images_in_memory,
    )


# Alternative: Stream-based approach for VERY large TIFF batches
# Use this if you're processing massive multi-page TIFFs

def merge_tiffs_to_pdf_streamed(
    tiff_paths: List[str],
    output_pdf: str,
    max_images_in_memory: int = DEFAULT_MAX_IMAGES_IN_MEMORY,
) -> None:
    """Backward-compatible alias that uses the streaming backend."""

    return _merge_tiffs_streamed(
        tiff_paths,
        output_pdf,
        max_images_in_memory=max_images_in_memory,
    )


def _merge_tiffs_streamed(
    tiff_paths: List[str],
    output_pdf: str,
    *,
    max_images_in_memory: int,
) -> None:
    if not tiff_paths:
        raise TiffToPdfError("No TIFF files provided")

    if max_images_in_memory <= 0:
        raise TiffToPdfError("max_images_in_memory must be >= 1")

    temp_pdfs: List[str] = []
    images_buffer: List[Image.Image] = []
    first_image: Image.Image | None = None
    temp_dir = os.path.dirname(os.path.abspath(output_pdf)) or "."

    try:
        for path in tiff_paths:
            if not os.path.exists(path):
                raise TiffToPdfError(f"File not found: {path}")

            im = None
            try:
                im = Image.open(path)

                if im.format not in ("TIFF", "TIF"):
                    raise TiffToPdfError(
                        f"Not a TIFF file: {path} (format={im.format})"
                    )

                page_idx = 0
                while True:
                    try:
                        im.seek(page_idx)
                    except EOFError:
                        break

                    page = im.convert("RGB")

                    if first_image is None:
                        first_image = page.copy()
                    else:
                        images_buffer.append(page.copy())

                    if len(images_buffer) >= max_images_in_memory and first_image is not None:
                        _flush_images_to_temp_pdf(
                            temp_pdfs,
                            first_image,
                            images_buffer,
                            temp_dir,
                        )
                        first_image = None
                        images_buffer = []
                        gc.collect()

                    page_idx += 1

            finally:
                if im is not None:
                    im.close()

        if first_image is None and not temp_pdfs and not images_buffer:
            raise TiffToPdfError("No images could be read from TIFFs")

        if first_image is not None or images_buffer:
            _flush_images_to_temp_pdf(temp_pdfs, first_image, images_buffer, temp_dir)
            first_image = None
            images_buffer = []

        if not temp_pdfs:
            raise TiffToPdfError("No images could be read from TIFFs")

        if len(temp_pdfs) == 1:
            os.replace(temp_pdfs[0], output_pdf)
        else:
            _merge_temp_pdfs(temp_pdfs, output_pdf)

    except TiffToPdfError:
        raise
    except Exception as e:
        raise TiffToPdfError(f"Failed to create PDF: {e}") from e

    finally:
        if first_image is not None:
            first_image.close()

        for img in images_buffer:
            if img is not None:
                img.close()

        for temp_pdf in temp_pdfs:
            try:
                if os.path.exists(temp_pdf):
                    os.remove(temp_pdf)
            except OSError:
                pass

        gc.collect()


def _flush_images_to_temp_pdf(
    temp_pdfs: List[str], first_image, images_buffer: List, temp_dir: str
) -> None:
    """Helper to write buffered images to a temporary PDF."""
    if first_image is None and not images_buffer:
        return
    
    os.makedirs(temp_dir, exist_ok=True)
    fd, temp_pdf = tempfile.mkstemp(prefix="tiff_batch_", suffix=".pdf", dir=temp_dir)
    os.close(fd)

    try:
        first_image.save(
            temp_pdf,
            save_all=True,
            append_images=images_buffer,
        )
    except Exception:
        try:
            os.remove(temp_pdf)
        finally:
            raise
    else:
        temp_pdfs.append(temp_pdf)
    finally:
        if first_image is not None:
            first_image.close()
        for img in images_buffer:
            img.close()


def _merge_temp_pdfs(temp_pdfs: List[str], output_pdf: str) -> None:
    """Helper to merge multiple temporary PDFs into one."""
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        raise TiffToPdfError(
            "PyPDF2 required for streaming mode. Install with: pip install PyPDF2"
        )
    
    merger = PdfMerger()
    try:
        for temp_pdf in temp_pdfs:
            merger.append(temp_pdf)
        merger.write(output_pdf)
    finally:
        merger.close()
