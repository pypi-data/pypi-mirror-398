"""Benchmark comparing add_records implementations.

Compares the optimized batch insert vs simple loop approach.
"""

from __future__ import annotations

import time
from typing import Any

from bear_shelf.datastore.columns import Columns
from bear_shelf.datastore.record import Record
from bear_shelf.datastore.tables.data import TableData


def create_test_table(name: str = "benchmark_table") -> TableData:
    """Create a test table with string PK and some columns."""
    columns = [
        Columns(name="id", type="str", primary_key=True, autoincrement=False),
        Columns(name="name", type="str"),
        Columns(name="value", type="int"),
        Columns(name="category", type="str"),
    ]
    return TableData(name=name, columns=columns)


def simple_add_records(table: TableData, records: list[Record]) -> None:
    """Original implementation: loop calling add_record."""
    for record in records:
        table.add_record(record)


def generate_records(count: int, offset: int = 0) -> list[Record]:
    """Generate test records."""
    return [
        Record(
            id=f"ID-{i + offset:06d}",
            name=f"Name {i + offset}",
            value=(i + offset) * 100,
            category=f"Cat-{(i + offset) % 10}",
        )
        for i in range(count)
    ]


def benchmark_implementation(
    name: str,
    insert_func: Any,
    record_counts: list[int],
    existing_records: int = 0,
) -> dict[int, float]:
    """Benchmark an implementation across different record counts.

    Args:
        name: Name of the implementation
        insert_func: Function that takes (table, records) and inserts them
        record_counts: List of batch sizes to test
        existing_records: Number of existing records in table before insert

    Returns:
        Dict mapping record count to execution time in seconds
    """
    results: dict[int, float] = {}

    print(f"\n{'=' * 60}")
    print(f"Benchmarking: {name}")
    print(f"Existing records in table: {existing_records}")
    print(f"{'=' * 60}")

    for count in record_counts:
        # Create fresh table with existing records
        table = create_test_table()
        if existing_records > 0:
            existing = generate_records(existing_records)
            for rec in existing:
                table.records.append(rec)

        # Generate new records to insert
        records = generate_records(count, offset=existing_records)

        # Benchmark the insert
        start = time.perf_counter()
        insert_func(table, records)
        elapsed = time.perf_counter() - start

        results[count] = elapsed
        print(f"  {count:5d} records: {elapsed:8.5f}s ({count / elapsed:10.0f} rec/sec)")

    return results


def compare_implementations() -> None:
    """Compare both implementations across various scenarios."""
    # Test scenarios: (description, batch_sizes, existing_records)
    scenarios = [
        ("Small batches, empty table", [10, 50, 100], 0),
        ("Medium batches, empty table", [500, 1000, 2000], 0),
        ("Large batches, empty table", [5000, 10000], 0),
        ("Small batches, 1000 existing", [10, 50, 100], 1000),
        ("Medium batches, 5000 existing", [500, 1000, 2000], 5000),
    ]

    all_results: dict[str, dict[str, dict[int, float]]] = {
        "simple": {},
        "optimized": {},
    }

    for scenario_name, batch_sizes, existing in scenarios:
        print(f"\n\n{'#' * 60}")
        print(f"SCENARIO: {scenario_name}")
        print(f"{'#' * 60}")

        # Benchmark simple implementation
        simple_results = benchmark_implementation(
            "Simple (loop + add_record)",
            simple_add_records,
            batch_sizes,
            existing,
        )
        all_results["simple"][scenario_name] = simple_results

        # Benchmark optimized implementation
        optimized_results = benchmark_implementation(
            "Optimized (batch validation + extend)",
            lambda t, r: t.add_records(r),
            batch_sizes,
            existing,
        )
        all_results["optimized"][scenario_name] = optimized_results

        # Print comparison
        print(f"\n{'─' * 60}")
        print("SPEEDUP COMPARISON:")
        print(f"{'─' * 60}")
        for count in batch_sizes:
            simple_time = simple_results[count]
            optimized_time = optimized_results[count]
            speedup = simple_time / optimized_time if optimized_time > 0 else 0
            status = "✓ FASTER" if speedup > 1.0 else "✗ SLOWER"

            print(
                f"  {count:5d} records: {speedup:5.2f}x speedup ({simple_time:.5f}s → {optimized_time:.5f}s) {status}"
            )

    # Summary
    print(f"\n\n{'#' * 60}")
    print("OVERALL SUMMARY")
    print(f"{'#' * 60}")

    total_simple = sum(sum(results.values()) for results in all_results["simple"].values())
    total_optimized = sum(sum(results.values()) for results in all_results["optimized"].values())
    overall_speedup = total_simple / total_optimized if total_optimized > 0 else 0

    print(f"\nTotal time (simple):    {total_simple:8.5f}s")
    print(f"Total time (optimized): {total_optimized:8.5f}s")
    print(f"Overall speedup:        {overall_speedup:8.2f}x")

    if overall_speedup > 1.0:
        print(f"\n✓ Optimized version is {overall_speedup:.2f}x faster overall!")
    else:
        print(f"\n✗ Simple version is {1 / overall_speedup:.2f}x faster overall!")


if __name__ == "__main__":
    print("Bear Shelf add_records() Performance Benchmark")
    print("=" * 60)
    compare_implementations()
