"""
CLI Module for ublkit.

Command-line interface for single file and batch conversion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ublkit import convert_file, convert_batch, __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="ublkit",
        description="Convert UBL XML files to JSON or CSV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file to JSON
  ublkit convert invoice.xml --format json --output output.json --config ublkit.yaml
  
  # Convert single file to CSV
  ublkit convert invoice.xml --format csv --output output.csv --config ublkit.yaml
  
  # Batch convert directory to CSV
  ublkit batch ./xml_files ./output --format csv --config ublkit.yaml
  
  # Dry run (preview without writing)
  ublkit batch ./xml_files ./output --format json --config ublkit.yaml --dry-run
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"ublkit {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Convert command (single file)
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a single XML file",
    )
    convert_parser.add_argument(
        "xml_file",
        help="Path to UBL XML file",
    )
    convert_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv"],
        required=True,
        help="Output format",
    )
    convert_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file path",
    )
    convert_parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to ublkit.yaml configuration file",
    )

    # Batch command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Convert multiple XML files",
    )
    batch_parser.add_argument(
        "input_dir",
        help="Directory containing XML files",
    )
    batch_parser.add_argument(
        "output_dir",
        help="Output directory",
    )
    batch_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv"],
        required=True,
        help="Output format",
    )
    batch_parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to ublkit.yaml configuration file",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be converted without writing files",
    )

    return parser


def handle_convert(args: argparse.Namespace) -> int:
    """Handle single file conversion."""
    try:
        print(f"Converting: {args.xml_file}")

        result = convert_file(
            xml_path=args.xml_file,
            output_format=args.format,
            config_path=args.config,
        )

        if result["success"]:
            # Write output file
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if args.format == "json":
                import json

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result["content"], f, indent=2, ensure_ascii=False)
            else:  # csv
                import polars as pl

                df = pl.DataFrame(result["content"])
                df.write_csv(output_path)

            print(f"✓ Success!")
            print(f"  Document type: {result['ubl_document_type']}")
            print(f"  Processing time: {result['processing_time_seconds']:.2f}s")
            print(f"  Output: {args.output}")
            return 0
        else:
            print(f"✗ Failed: {result['error_message']}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def handle_batch(args: argparse.Namespace) -> int:
    """Handle batch conversion."""
    try:
        print(f"Batch converting: {args.input_dir} -> {args.output_dir}")
        print(f"Format: {args.format}")

        if args.dry_run:
            print("\n⚠ DRY RUN MODE - No files will be written\n")

        summary = convert_batch(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            output_format=args.format,
            config_path=args.config,
        )

        print(f"\n{'=' * 60}")
        print("Conversion Complete")
        print(f"{'=' * 60}")
        print(f"Total files: {summary.total_files}")
        print(f"Successful: {summary.successful}")
        print(f"Failed: {summary.failed}")

        if summary.start_time and summary.end_time:
            duration = (summary.end_time - summary.start_time).total_seconds()
            print(f"Duration: {duration:.2f}s")

        if summary.failed > 0:
            print(f"\n⚠ {summary.failed} files failed")
            return 1

        return 0

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "convert":
        return handle_convert(args)
    elif args.command == "batch":
        return handle_batch(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
