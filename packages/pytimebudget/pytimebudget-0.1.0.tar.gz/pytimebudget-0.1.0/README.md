# pytimebudget

**Zero-effort performance regression detection for Python.**

pytimebudget helps you detect when parts of your code get slower over time, not just slow once.
It stores historical timing data and warns you when performance regresses, with almost no setup.

No configuration required.  
Just import it and use it.

---

## ✨ Features

- 📉 **Regression detection** - compares current runtime to historical baseline
- 💾 **SQLite backend** - persistent, fast, reliable
- 📦 **Per-project isolation** - each project gets its own database automatically
- ⚡ **Async support** - works with `async with`
- 🧠 **Safe by default** – never crashes your code
- 🔕 **Opt-out anytime** via environment variable


---

## 📦 Installation

```bash
pip install pytimebudget
````

---

## 🚀 Quick Start

### Basic usage

```python
import pytimebudget
import time

pytimebudget("startup", max_ms=100)
time.sleep(0.08)
```

If this code becomes significantly slower over time, pytimebudget will warn you.

---

### Context manager (recommended)

```python
import pytimebudget
import time

with pytimebudget("db_query", max_ms=40):
    time.sleep(0.05)
```

---

### Async support

```python
import pytimebudget
import asyncio

async def main():
    async with pytimebudget("async_task", max_ms=50):
        await asyncio.sleep(0.02)

asyncio.run(main())
```

---

## 🧠 How It Works

For each named timing:

1. Execution time is measured
2. The result is stored in a SQLite database
3. A rolling baseline is calculated
4. If the current run is significantly slower than the baseline,
   a warning is emitted

This allows you to catch gradual slowdowns that traditional profiling misses.

---

## 📁 Per-Project Isolation

Each project automatically gets its own database, based on the project root
(`.git`, `pyproject.toml`, or `setup.py`).

Databases are stored in:

```text
~/.pytimebudget/
```

This prevents unrelated projects from polluting each other’s timing data.

---

## ⚠️ Warnings

When a regression is detected, you’ll see something like:

```text
[pytimebudget] Performance regression detected
  Name:     db_query
  Baseline: 32.14 ms
  Current:  51.87 ms
  Slowdown: 1.61x
```

You can choose whether this is printed or emitted as a Python warning.

---

## 🎯 When Should You Use This?

* Detect performance regressions in long-lived projects
* Monitor critical paths (startup, I/O, parsing, DB access)
* Catch slowdowns before users do
* Add lightweight performance checks without profiling overhead

This is not a profiler, but it’s a regression detector.

---

## 🧪 Stability & Safety

* Uses only the Python standard library
* All internal errors are swallowed
* Never interrupts your application
* Safe for production use

---

## 📄 License

MIT License