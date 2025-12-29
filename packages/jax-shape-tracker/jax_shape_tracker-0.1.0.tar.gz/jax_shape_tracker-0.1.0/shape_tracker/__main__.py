"""Entry point for the Jax Shape Tracker script runner."""

import runpy
import sys

from . import JaxShapeTracker

if len(sys.argv) > 1:
    target_script = sys.argv[1]

    with JaxShapeTracker():
        runpy.run_path(target_script, run_name="__main__")
