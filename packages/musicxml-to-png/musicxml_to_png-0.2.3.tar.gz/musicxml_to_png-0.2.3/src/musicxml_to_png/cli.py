"""Command-line interface for MusicXML to PNG converter."""

import argparse
import sys
import warnings
from pathlib import Path

from music21.musicxml.xmlToM21 import MusicXMLWarning

from musicxml_to_png.converter import convert_musicxml_to_png
from musicxml_to_png.instruments import (
    ENSEMBLE_UNGROUPED,
    ENSEMBLE_ORCHESTRA,
    ENSEMBLE_BIGBAND,
)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert MusicXML files into clean, analyzable PNG visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.xml
  %(prog)s input.xml -o output.png
  %(prog)s input.xml --title "My Composition"
  %(prog)s input.xml --no-grid
  %(prog)s input.xml --minimal
  %(prog)s input.xml --ensemble bigband
  %(prog)s input.xml --verbose
        """,
    )
    
    parser.add_argument(
        "input",
        type=str,
        help="Path to the input MusicXML file",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path to the output PNG file (default: input filename with .png extension)",
    )
    
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        default=None,
        help="Title for the visualization (default: input filename)",
    )
    
    parser.add_argument(
        "--no-grid",
        action="store_true",
        help="Disable grid lines in the visualization",
    )
    
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Remove all labels, legend, title, and borders for a clean visualization",
    )
    
    parser.add_argument(
        "--ensemble",
        type=str,
        default=ENSEMBLE_UNGROUPED,
        choices=[ENSEMBLE_UNGROUPED, ENSEMBLE_ORCHESTRA, ENSEMBLE_BIGBAND],
        help=(
            "Ensemble type for instrument categorization. "
            "Defaults to per-instrument colors; choose orchestra or bigband to group by family."
        ),
    )
    
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show music21 warnings and other diagnostic information",
    )
    
    args = parser.parse_args()
    
    # Configure warning display based on verbose mode
    if args.verbose:
        # In verbose mode, ensure warnings are shown
        warnings.filterwarnings('always', category=MusicXMLWarning)
    else:
        # In quiet mode (default), suppress music21 warnings
        warnings.filterwarnings('ignore', category=MusicXMLWarning)
    
    # Convert input path to Path object
    input_path = Path(args.input)
    
    # Validate input file exists
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Validate input file extension
    if input_path.suffix.lower() not in [".xml", ".musicxml", ".mxl"]:
        print(
            f"Warning: Input file doesn't have a standard MusicXML extension: {input_path.suffix}",
            file=sys.stderr,
        )
    
    # Convert output path if provided
    output_path = Path(args.output) if args.output else None
    
    try:
        # Perform conversion
        result_path = convert_musicxml_to_png(
            input_path=input_path,
            output_path=output_path,
            title=args.title if not args.minimal else None,
            show_grid=not args.no_grid,
            minimal=args.minimal,
            ensemble=args.ensemble,
        )
        print(f"Successfully created visualization: {result_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
