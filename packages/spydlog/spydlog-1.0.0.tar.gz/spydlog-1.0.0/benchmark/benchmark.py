#!/usr/bin/env python3

"""
Performance benchmark comparing spydlog against Python's built-in logging module.

This script measures throughput (messages/second) for various logging scenarios.
"""

import time
import logging
import tempfile
import os
from typing import Callable, Tuple

try:
    import spydlog as spd
    SPYDLOG_AVAILABLE = True
except ImportError:
    SPYDLOG_AVAILABLE = False
    print("Warning: spydlog not available. Install with: pip install spydlog")

# Number of messages to log in each test
NUM_MESSAGES = 100_000


def benchmark(func: Callable, name: str) -> Tuple[float, float]:
    """
    Run a benchmark function and return execution time and throughput.

    Args:
        func: Function to benchmark
        name: Name of the benchmark

    Returns:
        Tuple of (execution_time_seconds, messages_per_second)
    """
    print(f"Running: {name}...", end=" ", flush=True)

    start = time.perf_counter()
    func()
    end = time.perf_counter()

    elapsed = end - start
    throughput = NUM_MESSAGES / elapsed

    print(f"Done ({elapsed:.3f}s, {throughput:,.0f} msg/s)")

    return elapsed, throughput


def setup_python_logger(filename: str = None, level=logging.INFO) -> logging.Logger:
    """Setup Python's built-in logger."""
    logger = logging.getLogger(f"test_logger_{id(filename)}")
    logger.handlers.clear()
    logger.setLevel(level)

    if filename:
        handler = logging.FileHandler(filename, mode='w')
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Benchmark functions for Python logging
def bench_python_console():
    """Python logger to console (stdout)."""
    logger = setup_python_logger()
    for i in range(NUM_MESSAGES):
        logger.info("Benchmark message number %d", i)


def bench_python_file():
    """Python logger to file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_file = f.name

    try:
        logger = setup_python_logger(temp_file)
        for i in range(NUM_MESSAGES):
            logger.info("Benchmark message number %d", i)
    finally:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except PermissionError:
            pass


def bench_python_disabled():
    """Python logger with level set to disable logging."""
    logger = setup_python_logger(level=logging.CRITICAL + 10)
    for i in range(NUM_MESSAGES):
        logger.info("Benchmark message number %d", i)


# Benchmark functions for spydlog
def bench_spydlog_console_mt():
    """spydlog multi-threaded console logger."""
    logger = spd.stdout_logger_mt("bench_console_mt")
    logger.set_pattern("%Y-%m-%d %H:%M:%S [%n] [%l] %v")

    for i in range(NUM_MESSAGES):
        logger.info(f"Benchmark message number {i}")

    logger.flush()
    spd.drop("bench_console_mt")


def bench_spydlog_console_st():
    """spydlog single-threaded console logger."""
    logger = spd.stdout_logger_st("bench_console_st")
    logger.set_pattern("%Y-%m-%d %H:%M:%S [%n] [%l] %v")

    for i in range(NUM_MESSAGES):
        logger.info(f"Benchmark message number {i}")

    logger.flush()
    spd.drop("bench_console_st")


def bench_spydlog_file_mt():
    """spydlog multi-threaded file logger."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_file = f.name

    try:
        logger = spd.basic_logger_mt("bench_file_mt", temp_file, truncate=True)
        logger.set_pattern("%Y-%m-%d %H:%M:%S [%n] [%l] %v")

        for i in range(NUM_MESSAGES):
            logger.info(f"Benchmark message number {i}")

        logger.flush()
        spd.drop("bench_file_mt")
    finally:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except PermissionError:
            pass


def bench_spydlog_file_st():
    """spydlog single-threaded file logger."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_file = f.name

    try:
        logger = spd.basic_logger_st("bench_file_st", temp_file, truncate=True)
        logger.set_pattern("%Y-%m-%d %H:%M:%S [%n] [%l] %v")

        for i in range(NUM_MESSAGES):
            logger.info(f"Benchmark message number {i}")

        logger.flush()
        spd.drop("bench_file_st")
    finally:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except PermissionError:
            pass


def bench_spydlog_async():
    """spydlog async logger to file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_file = f.name

    try:
        sink = spd.basic_file_sink_mt(temp_file, truncate=True)
        logger = spd.async_logger("bench_async", sink)
        logger.set_pattern("%Y-%m-%d %H:%M:%S [%n] [%l] %v")

        for i in range(NUM_MESSAGES):
            logger.info(f"Benchmark message number {i}")

        logger.flush()
        spd.drop("bench_async")
    finally:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except PermissionError:
            pass


def bench_spydlog_disabled():
    """spydlog with logging disabled."""
    logger = spd.stdout_logger_mt("bench_disabled")
    logger.set_level(spd.level.off)

    for i in range(NUM_MESSAGES):
        logger.info(f"Benchmark message number {i}")

    spd.drop("bench_disabled")


def run_benchmarks():
    """Run all benchmarks and display results."""
    print(f"\n{'='*70}")
    print(f"spydlog vs Python logging Performance Benchmark")
    print(f"{'='*70}")
    print(f"Number of messages per test: {NUM_MESSAGES:,}\n")

    results = []

    # Python logging benchmarks
    print("Python Built-in Logging")
    print("-" * 70)

    _, py_console = benchmark(bench_python_console, "Console (stdout)")
    results.append(("Python", "Console", py_console))

    _, py_file = benchmark(bench_python_file, "File")
    results.append(("Python", "File", py_file))

    _, py_disabled = benchmark(bench_python_disabled, "Disabled")
    results.append(("Python", "Disabled", py_disabled))

    if SPYDLOG_AVAILABLE:
        print("\nspydlog")
        print("-" * 70)

        _, spd_console_mt = benchmark(bench_spydlog_console_mt, "Console MT")
        results.append(("spydlog", "Console (MT)", spd_console_mt))

        _, spd_console_st = benchmark(bench_spydlog_console_st, "Console (ST)")
        results.append(("spydlog", "Console (ST)", spd_console_st))

        _, spd_file_mt = benchmark(bench_spydlog_file_mt, "File MT")
        results.append(("spydlog", "File (MT)", spd_file_mt))

        _, spd_file_st = benchmark(bench_spydlog_file_st, "File (ST)")
        results.append(("spydlog", "File (ST)", spd_file_st))

        _, spd_async = benchmark(bench_spydlog_async, "Async File")
        results.append(("spydlog", "Async File", spd_async))

        _, spd_disabled = benchmark(bench_spydlog_disabled, "Disabled")
        results.append(("spydlog", "Disabled", spd_disabled))

    # Print markdown table
    print(f"\n{'='*70}")
    print("Results Summary (Markdown Table)")
    print(f"{'='*70}\n")

    print("| Library | Scenario | Messages/Second | Speedup vs Python |")
    print("|---------|----------|-----------------|-------------------|")

    for lib, scenario, throughput in results:
        if lib == "Python":
            if scenario == "Console":
                baseline_console = throughput
            elif scenario == "File":
                baseline_file = throughput
            elif scenario == "Disabled":
                baseline_disabled = throughput
            speedup = "1.0x"
        else:
            # Calculate speedup
            if "Console" in scenario:
                speedup = f"{throughput / baseline_console:.1f}x"
            elif "File" in scenario or "Async" in scenario:
                speedup = f"{throughput / baseline_file:.1f}x"
            elif "Disabled" in scenario:
                speedup = f"{throughput / baseline_disabled:.1f}x"
            else:
                speedup = "N/A"

        print(f"| {lib:7} | {scenario:15} | {throughput:>13,.0f} | {speedup:>17} |")

    print("\n" + "="*70)
    print("Notes:")
    print("- MT = Multi-threaded (thread-safe)")
    print("- ST = Single-threaded (faster, but not thread-safe)")
    print("- Async = Asynchronous logging (background thread)")
    print("- Disabled = Logging disabled (overhead measurement)")
    print(f"- All tests logged {NUM_MESSAGES:,} messages")
    print("="*70 + "\n")


if __name__ == "__main__":
    if not SPYDLOG_AVAILABLE:
        print("\nERROR: spydlog is not installed.")
        print("Install it with: pip install spydlog")
        print("Exiting...\n")
        exit(1)

    run_benchmarks()
