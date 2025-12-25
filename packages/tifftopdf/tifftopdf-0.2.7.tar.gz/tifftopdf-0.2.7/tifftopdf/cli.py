import argparse
import sys
import traceback

from .orchestrator.run import OrchestratorConfig, run_once


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="TIFF-to-PDF batch processor (detect blanks → group → merge → report)."
    )
    parser.add_argument(
        "--input-root", required=False,
        help="Root folder containing batch subfolders (each batch is a folder of TIFFs)."
    )
    parser.add_argument(
        "--output-root", required=False,
        help="Folder to store PDFs (and metadata, unless --metadata-root is set)."
    )
    parser.add_argument(
        "--metadata-root", required=False,
        help="Separate folder to store metadata/state (default: inside output-root)."
    )
    parser.add_argument(
        "--recursive-scan", action="store_true",
        help="Recursively scan TIFFs inside each batch folder."
    )
    parser.add_argument(
        "--max-workers", type=int, default=1,
        help="Max threads for parallel PDF merging (default=1; increase carefully)."
    )
    parser.add_argument(
        "--zero-pad-width", type=int, default=3,
        help="Width for process IDs, e.g. 3 → '001', '002'."
    )
    parser.add_argument(
        "--allow-blank-only-groups", action="store_true",
        help="If set, allow groups that consist of only a blank separator page."
    )
    parser.add_argument(
        "--allow-root-as-batch", action="store_true",
        help="If set, process input-root itself as a batch if it has no subfolders."
    )
    parser.add_argument(
        "--no-per-batch-meta", action="store_true",
        help="Disable writing per-batch metadata JSON files."
    )
    parser.add_argument(
        "--no-run-meta", action="store_true",
        help="Disable writing run-level metadata JSON file."
    )
    parser.add_argument(
        "--include-blank-map", action="store_true",
        help="Include blank_map (per-file True/False) in batch metadata."
    )
    parser.add_argument("--resume", dest="resume", action="store_true", default=True,
                   help="Retomar de onde parou (default: on)")
    parser.add_argument("--no-resume", dest="resume", action="store_false",
                   help="Desativar retoma; reprocessa tudo (salvo --force)")
    parser.add_argument("--force", action="store_true", default=False,
                   help="Força reprocessar grupos mesmo se já concluídos")
    parser.add_argument("--state-file", default="run_state.json",
                   help="Nome do ficheiro de estado no diretório de metadata")
    parser.add_argument("--verify-existing", action="store_true", default=False,
                   help="Revalidar PDFs existentes (lento, opcional)")
    
    parser.add_argument("--get-processed", action="store_true",
                   help="Retorna JSON com lista de batches já processados com sucesso")

    parser.add_argument("-v","--verbose", action="count", default=0)
    parser.add_argument("-q","--quiet",   action="count", default=0)
    parser.add_argument(
        "--version", action="store_true", help="Show version and exit."
    )

    args = parser.parse_args(argv)

    if args.version:
        import importlib.metadata
        try:
            version = importlib.metadata.version("tifftopdf")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        print(f"tifftopdf {version}")
        return 0

    # --- Handle --get-processed mode ---
    if args.get_processed:
        if not args.output_root:
            print("Error: --output-root is required for --get-processed", file=sys.stderr)
            return 1
        
        from tifftopdf.reporting.query import get_processed_batches
        import json
        
        processed = get_processed_batches(args.output_root)
        print(json.dumps(processed, indent=2))
        return 0

    # --- Standard Run Mode Validation ---
    if not args.input_root:
        parser.error("the following arguments are required: --input-root")
    if not args.output_root:
        parser.error("the following arguments are required: --output-root")

    level = "INFO"
    if args.verbose >= 2:
        level = "DEBUG"
    elif args.verbose == 1:
        level = "INFO"
    elif args.quiet >= 2:
        level = "ERROR"
    elif args.quiet == 1:
        level = "WARNING"

    from tifftopdf.utils.logging import setup_logging
    setup_logging(level)

    # Lazy import to avoid dependency issues when running lightweight commands
    from .orchestrator.run import OrchestratorConfig, run_once

    cfg = OrchestratorConfig(
        input_root=args.input_root,
        output_root=args.output_root,
        recursive_scan=args.recursive_scan,
        max_workers=args.max_workers,
        zero_pad_width=args.zero_pad_width,
        allow_blank_only_groups=args.allow_blank_only_groups,
        allow_root_as_single_batch=args.allow_root_as_batch,
        write_per_batch_metadata=not args.no_per_batch_meta,
        write_run_metadata=not args.no_run_meta,
        include_blank_map=args.include_blank_map,
        resume=args.resume,
        force=args.force,
        state_filename=args.state_file,
        verify_existing=args.verify_existing,
        metadata_root=args.metadata_root,
    )

    try:
        result = run_once(cfg)
        print(f"\nCompleted run: {result.batch_count} batches processed")
        print(f"Output root: {result.output_root}")
        print(f"Success: {result.success}")
        for b in result.batches:
            status = "OK" if b.success else f"FAIL ({b.error})"
            print(f"   - {b.batch_name}: {b.grouping.process_count} processes, {status}")
        return 0 if result.success else 1
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
