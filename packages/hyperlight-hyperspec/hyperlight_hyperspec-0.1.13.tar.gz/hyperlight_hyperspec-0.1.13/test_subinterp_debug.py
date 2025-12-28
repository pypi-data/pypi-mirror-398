#!/usr/bin/env python3
"""Debug script for subinterpreter crash."""

import concurrent.interpreters as interpreters
import sys

import hyperspec

print(f"Python version: {sys.version}", flush=True)
print(f"Imported hyperspec {hyperspec.__version__}", flush=True)

print("Running 10 sequential subinterpreters...", flush=True)
for i in range(10):
    print(f"Creating interpreter {i + 1}...", flush=True)
    interp = interpreters.create()
    try:
        print(f"  Executing code in {i + 1}...", flush=True)
        interp.exec('import hyperspec; hyperspec.json.encode({"a": 1})')
        print(f"  ✓ Iteration {i + 1}/10 passed", flush=True)
    finally:
        print(f"  Closing {i + 1}...", flush=True)
        interp.close()
        print(f"  ✓ Closed {i + 1}", flush=True)

print("Done!", flush=True)
