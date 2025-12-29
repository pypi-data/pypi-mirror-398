"""Entry point for the Jax Shape Tracker script runner."""

import runpy
import sys

from . import JaxShapeTracker


def main() -> None:
    """Run a Python script with JaxShapeTracker enabled."""
    if len(sys.argv) < 2:
        print("Usage: shape-tracker <script.py> [args...]", file=sys.stderr)
        sys.exit(1)

    target_script = sys.argv[1]
    sys.argv = [target_script, *sys.argv[2:]]

    with JaxShapeTracker():
        runpy.run_path(target_script, run_name="__main__")

if __name__ == "__main__":
    main()
