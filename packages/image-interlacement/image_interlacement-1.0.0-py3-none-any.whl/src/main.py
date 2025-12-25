"""Main CLI entry point for the image interlacing program."""

import argparse
import sys
from pathlib import Path

# Support running as installed module, PyInstaller binary, or plain script
# Try imports in order: package-relative, absolute within 'src', then plain
try:
    from .composite import composite_n_images, interlace  # when executed as module: python -m src.main
except Exception:
    try:
        from src.composite import composite_n_images, interlace  # when executed as script or frozen
    except Exception:
        from composite import composite_n_images, interlace  # fallback for legacy layouts


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Image Interlacing Program - Create composites by alternating rows/columns from multiple images (2-6)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py composite img1.png img2.png --output out.png --mode rows
    python main.py composite img1.png img2.png img3.png --output out.png --mode columns
    python main.py composite img1.png img2.png img3.png img4.png img5.png img6.png --output out.png --mode rows
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Composite command
    composite_parser = subparsers.add_parser('composite', help='Create a composite from multiple images (2-6)')
    composite_parser.add_argument('images', nargs='+', type=str, help='Input image paths (2-6); accepts "white"/"black" as solid colors')
    composite_parser.add_argument('--output', required=True, type=str, help='Output image path (required)')
    composite_parser.add_argument('--mode', type=str, default='rows', 
                                  choices=['rows', 'columns'],
                                  help='Alternation mode: rows or columns (default: rows)')
    composite_parser.add_argument('--tile-mode', type=str, default='max',
                                  choices=['max', 'lcm'],
                                  help='Tiling mode: max (use largest dimension) or lcm (use least common multiple in interleave direction) (default: max)')
    composite_parser.add_argument('--stride', type=int, nargs='+', 
                                  help='Pattern of rows/columns to take from each image (e.g., --stride 1 2 1 means 1 from img1, 2 from img2, 1 from img3, repeat). Defaults to 1 per image.')

    # Interlace command (same-size interlacing)
    interlace_parser = subparsers.add_parser('interlace', help='Interlace two images into a same-size image')
    interlace_parser.add_argument('image1', type=str, help='First input image path, or "white"/"black" for solid color')
    interlace_parser.add_argument('image2', type=str, help='Second input image path, or "white"/"black" for solid color')
    interlace_parser.add_argument('output', type=str, help='Output image path')
    interlace_parser.add_argument('--mode', type=str, default='rows', 
                                  choices=['rows', 'columns'],
                                  help='Interlace mode: rows or columns (default: rows)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'composite':
            if not (2 <= len(args.images) <= 6):
                raise ValueError("Provide between 2 and 6 input images.")
            stride = args.stride if hasattr(args, 'stride') and args.stride else None
            composite_n_images(args.images, args.output, args.mode, tiling_mode=args.tile_mode, stride=stride)
            print(f"✓ Composite created successfully: {args.output}")
        elif args.command == 'interlace':
            interlace(args.image1, args.image2, args.output, args.mode)
            print(f"✓ Interlaced image created successfully: {args.output}")
    except FileNotFoundError as e:
        print(f"✗ Error: File not found - {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
