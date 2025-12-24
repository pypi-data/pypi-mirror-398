"""
Command-line interface for MagPy.
"""

import argparse
import sys
from pathlib import Path

from . import __version__


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="magpy",
        description="MagPy Bioacoustics",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Audio file to open",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        default=True,
        help="Launch GUI (default)",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode for batch processing",
    )

    parser.add_argument(
        "--compute-spectrogram",
        metavar="OUTPUT",
        help="Compute spectrogram and save as image",
    )

    parser.add_argument(
        "--measure",
        metavar="SELECTION_TABLE",
        help="Compute measurements for selections in the given table",
    )

    args = parser.parse_args()

    if args.headless:
        return run_headless(args)
    else:
        from .app import main as gui_main

        return gui_main(args.file)


def run_headless(args) -> int:
    """Run in headless mode for batch processing."""
    if args.file is None:
        print("Error: No input file specified", file=sys.stderr)
        return 1

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 1

    from .core import AudioFile, SpectrogramGenerator, SelectionTable, MeasurementCalculator
    from .core.measurements import SelectionBounds

    print(f"Loading: {filepath}")
    audio = AudioFile(filepath)
    print(f"  Duration: {audio.duration:.2f}s")
    print(f"  Channels: {audio.num_channels}")
    print(f"  Sample rate: {audio.sample_rate} Hz")

    if args.compute_spectrogram:
        print(f"Computing spectrogram...")
        generator = SpectrogramGenerator()
        result = generator.compute(audio.data, audio.sample_rate)

        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        plt.imshow(
            result.spectrogram,
            aspect="auto",
            origin="lower",
            extent=[0, result.duration, 0, result.frequencies[-1]],
            cmap="viridis",
        )
        plt.colorbar(label="Power (dB)")
        plt.xlabel("Time (s)")
        plt.ylabel("Frequency (Hz)")
        plt.title(f"Spectrogram: {filepath.name}")
        plt.savefig(args.compute_spectrogram, dpi=150, bbox_inches="tight")
        print(f"Saved spectrogram to: {args.compute_spectrogram}")

    if args.measure:
        selection_path = Path(args.measure)
        if not selection_path.exists():
            print(f"Error: Selection table not found: {selection_path}", file=sys.stderr)
            return 1

        print(f"Loading selection table: {selection_path}")
        table = SelectionTable.load(selection_path)
        print(f"  Found {len(table)} selections")

        calc = MeasurementCalculator()

        for i, selection in enumerate(table):
            bounds = SelectionBounds(
                start_time=selection.begin_time,
                end_time=selection.end_time,
                low_freq=selection.low_freq,
                high_freq=selection.high_freq,
            )
            result = calc.compute_all(audio.data, audio.sample_rate, bounds)
            selection.measurements = result.to_dict()
            print(f"  Measured selection {i + 1}: {selection.duration:.3f}s")

        # Save updated table
        output_path = selection_path.with_stem(selection_path.stem + "_measured")
        table.save(output_path)
        print(f"Saved measurements to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
