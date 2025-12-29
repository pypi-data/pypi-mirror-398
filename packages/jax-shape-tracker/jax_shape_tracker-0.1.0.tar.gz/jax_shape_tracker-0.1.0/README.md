# jax-shape-tracker

**Pinpoint JAX shape errors at the exact line of *your* code — not inside XLA.**

`jax-shape-tracker` is a lightweight debugging utility that intercepts JAX primitive execution and records a short history of operations with their input/output shapes. When a shape mismatch occurs, it prints a clear, human-readable trace showing **what operation failed, where it was called, and how shapes evolved leading up to the error**.

This tool exists because **JAX erases Python stack information once it lowers to XLA**, making shape errors notoriously painful to debug.

---

## Why This Exists

If you’ve ever seen this:

```
TypeError: dot_general requires contracting dimensions to have the same shape
```

…and the traceback points deep into `jax/_src/lax`, you already know the problem.

By the time the error is raised:

* Python stack frames are gone
* User source locations are lost
* You’re left guessing which reshape / broadcast / reduction broke things

**`jax-shape-tracker` captures the last meaningful Python context *before* JAX drops into XLA**, and shows you exactly what happened.

---

## Features

* 📍 Exact **user source line** for each operation
* 🧠 **Recent operation history** with input/output shapes
* 🔍 Clear display of the **failing JAX primitive**
* 🎨 Optional colored output (via `colorama`)
* 🧪 Zero dependencies required
* 🧩 Works with `jax.numpy`, `jax.random`, and core JAX ops
* 🛠 Context-manager based (no refactoring required)

---

## Installation

This is a pure-Python utility. Clone and use directly:

```bash
git clone https://github.com/KrisTHL181/jax-shape-tracker.git
cd jax-shape-tracker
```

Optional (for colored output):

```bash
pip install colorama
```

---

## Basic Usage

### 1. Wrap your code with the context manager

```python
from shape_tracker import JaxShapeTracker

with JaxShapeTracker():
    your_jax_function()
```

If a shape error occurs, a detailed operation trace will be printed automatically.

---

### 2. Run a script directly (CLI-style)

You can run an existing script under the tracker without modifying it:

```bash
python -m shape_tracker example_buggy_code.py
```

---

## Example

### Buggy Code (`example_buggy_code.py`)

```python
import jax
import jax.numpy as jnp

def main():
    key = jax.random.PRNGKey(0)
    x = jax.random.normal(key, (32, 128))

    y = x.reshape(32, 64, 2)
    z = jnp.sum(y, axis=2)  # (32, 64)

    key2 = jax.random.PRNGKey(1)
    weight = jax.random.normal(key2, (100, 100))

    jnp.matmul(z, weight)  # ❌ shape mismatch

if __name__ == "__main__":
    main()
```

---

### Output

```
============================================================
🛑 JAX SHAPE/OP MISMATCH: TypeError
============================================================

--- Recent Operation History ---
1. [example_buggy_code.py:17 -> y = x.reshape(32, 64, 2)]
    Op: reshape
    In : (32, 128)
    Out: (32, 64, 2)

2. [example_buggy_code.py:20 -> z = jnp.sum(y, axis=2)]
    Op: reduce_sum
    In : (32, 64, 2)
    Out: (32, 64)

--- ❌ THE OPERATION THAT FAILED ---
[example_buggy_code.py:26 -> jnp.matmul(z, weight)]
    Op: dot_general
    In : (32, 64), (100, 100)
    ERROR: contracting dimensions must match (64 vs 100)
```

You immediately see:

* **Where** the error occurred
* **Which shapes** caused it
* **How the shapes evolved**

No guessing. No XLA archaeology.

---

## Automatic Retry Mode

You can also run code normally and only enable tracking **after** a shape error is detected:

```python
from shape_tracker._shape_bug_tracker import track_when_shape_mismatch

track_when_shape_mismatch(your_function)
```

This avoids slowing down normal execution.

---

## Important Notes & Limitations

* ⚠️ **Recommended:** disable JIT for accurate source tracking

  ```python
  jax.config.update("jax_disable_jit", True)
  ```
* This is a **debugging tool**, not intended for production
* JAX internals are intentionally filtered to reduce noise
* Some primitives are suppressed to keep logs readable

These limitations are inherent to how JAX works, not this tool.

---

## When Should You Use This?

Perfect for debugging:

* Matrix multiplication mismatches
* Broadcasting errors
* Silent shape drift in long pipelines
* Complex model code where shapes change dynamically

---

## License

MIT License
© 2025 Kris

---

## Final Note

This tool exists because **debugging shape errors should not feel like reverse-engineering a compiler**.

If this saved you time, frustration, or sanity — mission accomplished.

Happy debugging 🚀
