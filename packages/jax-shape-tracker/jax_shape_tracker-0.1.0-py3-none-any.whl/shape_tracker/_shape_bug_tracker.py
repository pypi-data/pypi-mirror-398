import inspect
import linecache
import os
import re
import types
from collections import deque
from collections.abc import Callable
from typing import Any

import jax
import jax.numpy as jnp
from jax.extend.core import Primitive

try:
    from colorama import Fore, Style
    from colorama import init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    # Fallback if colorama is not installed
    class MockColor:
        def __getattr__(self, _name: str) -> str:
            return ""
    Fore = Style = MockColor()

# Regex to detect if an exception message refers to shape/dimension errors
SHAPE_MISMATCH_PATTERN: re.Pattern = re.compile(
    r"\b(shape|dimension|broadcast|incompatible|mismatch|size)\b",
    re.IGNORECASE,
)

# Ops that are often internal or overly verbose for debugging logs
NOISY_OPS: set[str] = {
    "convert_element_type",
    "bitcast_convert_type",
}

class JaxShapeTracker:
    """A context manager that tracks JAX primitive operations and their shapes.

    If an error occurs within the context, it prints a history of the most recent
    operations to help diagnose where tensor dimensions diverged.
    """

    def __init__(self, history_len: int = 0) -> None:
        """Initialize the tracker.

        Args:
            history_len: Number of recent operations to store. 0 means unlimited.

        """
        self.history: deque[str] = deque(maxlen=history_len if history_len > 0 else None)
        self.history_len: int = history_len
        self.original_bind: Callable = lambda *_args, **_kwargs: None

    def _get_user_location(self) -> str:
        """Crawl the stack to find the first frame outside of JAX internals.

        Returns:
            A formatted string containing the filename, line number, and source code.

        """
        stack = inspect.stack()
        for frame_info in stack:
            fname = frame_info.filename
            # Skip JAX internals and core logic
            if "jax/_src" in fname or "jax/core.py" in fname or "jax/extend" in fname:
                continue
            # Skip this tracker's own methods
            if os.path.basename(__file__) in fname or \
                frame_info.function in dir(JaxShapeTracker):
                    continue

            line = linecache.getline(fname, frame_info.lineno).strip()
            return f"{os.path.basename(fname)}:{frame_info.lineno}\n -> \
{Fore.YELLOW}{line}{Style.RESET_ALL}"

        return "Unknown Location"

    def _get_shape_str(self, obj: Any) -> str:
        """Recursively extracts shape information from JAX arrays or containers.

        Args:
            obj: The object to inspect (array, list, tuple, etc.).

        Returns:
            A string representation of the shape(s).

        """
        if hasattr(obj, "shape"):
            return str(obj.shape)
        if isinstance(obj, (list, tuple)):
            return str([self._get_shape_str(x) for x in obj])
        return str(type(obj).__name__)

    def _format_op_info(
        self,
        primitive: Primitive,
        args: tuple[Any, ...],
        params: dict[str, Any],
        location: str,
        output: Any = None,
        error: str | None = None,
    ) -> str:
        """Format operation details into a human-readable string.

        Args:
            primitive: The JAX primitive being executed.
            args: Arguments passed to the primitive.
            params: Parameters (metadata) of the primitive.
            location: String describing where in the user code this was called.
            output: The result of the operation, if successful.
            error: The error message, if the operation failed.

        Returns:
            A formatted multi-line string log entry.

        """
        name = primitive.name if hasattr(primitive, "name") else str(primitive)

        def safe_shape(x: Any) -> str:
            return str(x.shape) if hasattr(x, "shape") else "scalar"

        try:
            arg_shapes = jax.tree_util.tree_map(safe_shape, args)
        except Exception:
            arg_shapes = "unknown"

        msg = f"[{location}]\n"
        msg += f"    Op: {Fore.LIGHTWHITE_EX}{name}{Style.RESET_ALL} {params if params else ''}\n"
        msg += f"    In : {Fore.LIGHTGREEN_EX}{arg_shapes}{Style.RESET_ALL}\n"

        if error:
            msg += f"    >>> {Style.BRIGHT}{Fore.LIGHTRED_EX}ERROR: {error}{Style.RESET_ALL}\n"
        else:
            try:
                out_shape = jax.tree_util.tree_map(safe_shape, output)
                msg += f"    Out: {Fore.LIGHTGREEN_EX}{out_shape}{Style.RESET_ALL}\n"
            except Exception:
                msg += "    Out: unknown\n"

        return msg

    def _process_bind(
        self,
        primitive: Primitive,
        args: tuple[Any, ...],
        params: dict[str, Any],
        location: str,
    ) -> Any:
        """Intercept the primitive bind, logs metadata, and handles failures.

        Args:
            primitive: The JAX primitive.
            args: Positional arguments.
            params: Keyword parameters.
            location: Source code location.

        Returns:
            The output of the original JAX bind.

        Raises:
            Exception: Re-raises any exception caught during bind, after logging history.

        """
        try:
            # Execute original JAX logic
            output = self.original_bind(primitive, *args, **params)
            log_entry = self._format_op_info(primitive, args, params, location, output=output)

            # Avoid spamming history if the same line produces multiple identical entries
            if (self.history and self.history[-1].startswith(f"[{location}]")) or \
               (hasattr(primitive, "name") and primitive.name in NOISY_OPS):
                return output

            self.history.append(log_entry)
            return output

        except Exception as e:
            print("\n" + "=" * 60)
            print(f"🛑 {Fore.LIGHTWHITE_EX}JAX SHAPE/OP MISMATCH: {type(e).__name__}{Style.RESET_ALL}")
            print("=" * 60)

            history_len = len(self.history)
            print(f"\n--- Recent Operation History (Last {history_len}) ---")
            for i, entry in enumerate(self.history):
                print(f"{i+1}. {entry}")

            print("\n--- ❌ THE OPERATION THAT FAILED ---")
            print(self._format_op_info(primitive, args, params, location, error=str(e)))
            print("=" * 60 + "\n")
            raise

    def __enter__(self) -> "JaxShapeTracker":
        """Monkey-patches Primitive.bind to start tracking."""
        self.original_bind = Primitive.bind

        def wrapper(prim: Primitive, *args: Any, **params: Any) -> Any:
            loc = self._get_user_location()
            return self._process_bind(prim, args, params, loc)

        Primitive.bind = wrapper # pyright: ignore[reportAttributeAccessIssue]
        return self

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: types.TracebackType | None,
        ) -> None:
        """Restores the original Primitive.bind."""
        if self.original_bind:
            Primitive.bind = self.original_bind

def track_when_shape_mismatch(
    func: Callable[[], Any],
    history_len: int = 10,
    disable_jit: bool = True,
) -> Any:
    """Run a function and automatically activates JaxShapeTracker if a shape error occurs.

    Args:
        func: The function to execute.
        history_len: How many ops to track in the history buffer.
        disable_jit: Whether to disable JIT (recommended for accurate stack traces).

    Returns:
        The result of func().

    Raises:
        Exception: The original exception if it doesn't match a shape error,
                  or the error caught during the tracked re-run.

    """
    if disable_jit:
        jax.config.update("jax_disable_jit", disable_jit)

    try:
        return func()
    except Exception as e:
        if SHAPE_MISMATCH_PATTERN.search(str(e)):
            print(f"\n{Fore.CYAN}Shape mismatch likely. Re-running with Tracker...{Style.RESET_ALL}\n")
            with JaxShapeTracker(history_len=history_len):
                return func()
        raise e

# --- Usage Example ---
if __name__ == "__main__":
    def faulty_pipeline() -> jnp.ndarray:
        """Trigger a dimension mismatch for a faulty matrix multiplication."""
        key = jax.random.PRNGKey(0)
        x = jax.random.normal(key, (32, 128))

        # Correct Reshape
        y = x.reshape(32, 64, 2)

        # Reduce operation
        z = jnp.sum(y, axis=2)  # Shape becomes (32, 64)

        # Intentional Error: Mismatched Matmul
        key2 = jax.random.PRNGKey(1)
        weight = jax.random.normal(key2, (100, 100))

        print("Attempting faulty matrix multiplication...")
        return jnp.matmul(z, weight)  # <--- CRASH HERE

    def correct_pipeline() -> jnp.ndarray:
        """A pipeline that works correctly with matrix multiplication."""
        key = jax.random.PRNGKey(0)
        x = jax.random.normal(key, (32, 128))
        y = x.reshape(32, 64, 2)
        z = jnp.sum(y, axis=2)  # (32, 64)

        key2 = jax.random.PRNGKey(1)
        w = jax.random.normal(key2, (64, 10))

        return jnp.matmul(z, w)

    print("--- Running Faulty Pipeline ---")
    try:
        track_when_shape_mismatch(faulty_pipeline)
    except Exception:
        print("Tracker successfully caught the error.")

    print("\n--- Running Correct Pipeline ---")
    try:
        with JaxShapeTracker():
            correct_pipeline()
        print("Correct pipeline executed without errors.")
    except Exception as e:
        print(f"This should not happen! {e}")
        raise e
