"""
Copyright (C) 2025 Luciano Guerche

This file is part of rabbitmq-mcp-server.

rabbitmq-mcp-server is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

rabbitmq-mcp-server is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with rabbitmq-mcp-server. If not, see <https://www.gnu.org/licenses/>.
"""

import json
from pathlib import Path

import pytest

pytest_plugins = ["pytest_benchmark"]


@pytest.fixture
def registry_path():
    """Path to the full operations registry."""
    return Path(__file__).parent.parent.parent / "data" / "operations.json"


@pytest.fixture
def registry_data(registry_path):
    """Load registry data once for all tests."""
    with open(registry_path, encoding="utf-8") as f:
        return json.load(f)


class TestRegistryLoadPerformance:
    """Test registry file loading performance."""

    def test_registry_file_load_time(self, benchmark, registry_path):
        """Test that registry file loads in <100ms."""

        def load_registry():
            with open(registry_path, encoding="utf-8") as f:
                return json.load(f)

        result = benchmark(load_registry)

        # Verify load completed
        assert result is not None
        assert "operations" in result

        # Get benchmark statistics
        stats = benchmark.stats.stats
        mean_time = stats.mean
        p95_time = stats.q_0_95 if hasattr(stats, "q_0_95") else mean_time * 1.2

        # Assert performance targets
        assert (
            mean_time < 0.1
        ), f"Mean load time {mean_time*1000:.2f}ms exceeds 100ms target"
        assert (
            p95_time < 0.15
        ), f"P95 load time {p95_time*1000:.2f}ms exceeds 150ms threshold"

        print("\nRegistry Load Performance:")
        print(f"  Mean: {mean_time*1000:.2f}ms")
        print(f"  Min:  {stats.min*1000:.2f}ms")
        print(f"  Max:  {stats.max*1000:.2f}ms")
        print(f"  P95:  {p95_time*1000:.2f}ms")


class TestOperationLookupPerformance:
    """Test operation lookup performance."""

    def test_operation_lookup_by_id(self, benchmark, registry_data):
        """Test that operation lookup completes in <1ms."""
        operations = registry_data["operations"]
        operation_id = "queues.list"  # Use a known operation

        def lookup_operation():
            return operations.get(operation_id)

        result = benchmark(lookup_operation)

        # Verify lookup succeeded
        assert result is not None
        assert result["operation_id"] == operation_id

        # Get benchmark statistics
        stats = benchmark.stats.stats
        mean_time = stats.mean
        p95_time = stats.q_0_95 if hasattr(stats, "q_0_95") else mean_time * 1.2

        # Assert performance targets (O(1) dict access should be sub-microsecond)
        assert (
            mean_time < 0.001
        ), f"Mean lookup time {mean_time*1000:.2f}ms exceeds 1ms target"
        assert (
            p95_time < 0.002
        ), f"P95 lookup time {p95_time*1000:.2f}ms exceeds 2ms threshold"

        print("\nOperation Lookup Performance:")
        print(f"  Mean: {mean_time*1000000:.2f}µs")
        print(f"  Min:  {stats.min*1000000:.2f}µs")
        print(f"  Max:  {stats.max*1000000:.2f}µs")
        print(f"  P95:  {p95_time*1000000:.2f}µs")

    def test_multiple_operation_lookups(self, benchmark, registry_data):
        """Test performance of multiple sequential lookups."""
        operations = registry_data["operations"]

        # Get first 10 operation IDs for testing
        operation_ids = list(operations.keys())[:10]

        def lookup_multiple():
            results = []
            for op_id in operation_ids:
                results.append(operations.get(op_id))
            return results

        results = benchmark(lookup_multiple)

        # Verify all lookups succeeded
        assert len(results) == 10
        assert all(r is not None for r in results)

        # Get benchmark statistics
        stats = benchmark.stats.stats
        mean_time = stats.mean
        avg_per_lookup = mean_time / 10

        # Each lookup should still be <1ms on average
        assert (
            avg_per_lookup < 0.001
        ), f"Average lookup time {avg_per_lookup*1000:.2f}ms exceeds 1ms target"

        print("\nMultiple Lookups Performance (10 operations):")
        print(f"  Total Mean: {mean_time*1000:.2f}ms")
        print(f"  Per Lookup: {avg_per_lookup*1000000:.2f}µs")

    def test_lookup_nonexistent_operation(self, benchmark, registry_data):
        """Test performance of looking up nonexistent operation."""
        operations = registry_data["operations"]
        nonexistent_id = "nonexistent.operation"

        def lookup_nonexistent():
            return operations.get(nonexistent_id)

        result = benchmark(lookup_nonexistent)

        # Verify returns None for nonexistent
        assert result is None

        # Performance should still be O(1)
        stats = benchmark.stats.stats
        mean_time = stats.mean
        assert (
            mean_time < 0.001
        ), f"Mean lookup time {mean_time*1000:.2f}ms exceeds 1ms target"


class TestRegistryStructurePerformance:
    """Test performance of registry structure operations."""

    def test_iterate_all_operations(self, benchmark, registry_data):
        """Test performance of iterating through all operations."""
        operations = registry_data["operations"]

        def iterate_operations():
            count = 0
            for op_id, op_data in operations.items():
                count += 1
            return count

        count = benchmark(iterate_operations)

        # Verify iteration completed
        assert count > 0
        assert count == len(operations)

        print(f"\nIteration Performance ({count} operations):")
        stats = benchmark.stats.stats
        print(f"  Mean: {stats.mean*1000:.2f}ms")
        print(f"  Per Operation: {(stats.mean/count)*1000000:.2f}µs")

    def test_filter_operations_by_namespace(self, benchmark, registry_data):
        """Test performance of filtering operations by namespace."""
        operations = registry_data["operations"]

        def filter_by_namespace():
            return [
                op_data
                for op_data in operations.values()
                if op_data["namespace"] == "queues"
            ]

        results = benchmark(filter_by_namespace)

        # Verify filtering completed
        assert len(results) > 0
        assert all(op["namespace"] == "queues" for op in results)

        print(f"\nNamespace Filtering Performance (found {len(results)} operations):")
        stats = benchmark.stats.stats
        print(f"  Mean: {stats.mean*1000:.2f}ms")

    def test_filter_operations_by_protocol(self, benchmark, registry_data):
        """Test performance of filtering operations by protocol."""
        operations = registry_data["operations"]

        def filter_by_protocol():
            return [
                op_data
                for op_data in operations.values()
                if op_data["protocol"] == "amqp"
            ]

        results = benchmark(filter_by_protocol)

        # Verify filtering completed
        assert len(results) >= 5  # At least 5 AMQP operations
        assert all(op["protocol"] == "amqp" for op in results)

        print(f"\nProtocol Filtering Performance (found {len(results)} operations):")
        stats = benchmark.stats.stats
        print(f"  Mean: {stats.mean*1000:.2f}ms")


class TestRegistrySize:
    """Test registry file size constraints."""

    def test_registry_file_size_under_5mb(self, registry_path):
        """Test that registry file size is under 5MB."""
        file_size_bytes = registry_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        print(f"\nRegistry File Size: {file_size_mb:.2f} MB")
        print(f"  Bytes: {file_size_bytes:,}")
        print("  Target: < 5.00 MB")

        assert (
            file_size_mb < 5.0
        ), f"Registry file size {file_size_mb:.2f}MB exceeds 5MB limit"

    def test_registry_operations_count(self, registry_data):
        """Test that registry has expected number of operations."""
        total_operations = registry_data["total_operations"]
        operations_count = len(registry_data["operations"])

        print("\nRegistry Operations Count:")
        print(f"  Declared: {total_operations}")
        print(f"  Actual:   {operations_count}")

        # Verify metadata matches actual count
        assert (
            total_operations == operations_count
        ), f"Operation count mismatch: {total_operations} != {operations_count}"

        # Verify we have a reasonable number of operations (100+ from OpenAPI)
        assert (
            operations_count >= 100
        ), f"Expected at least 100 operations, got {operations_count}"


class TestMemoryFootprint:
    """Test memory footprint of loaded registry."""

    def test_registry_memory_footprint(self, registry_data):
        """Test that loaded registry has reasonable memory footprint."""
        import sys

        # Rough estimate of memory usage
        memory_bytes = sys.getsizeof(registry_data)

        # Add approximate size of nested structures
        for key, value in registry_data.items():
            memory_bytes += sys.getsizeof(key) + sys.getsizeof(value)
            if isinstance(value, dict):
                for k, v in value.items():
                    memory_bytes += sys.getsizeof(k) + sys.getsizeof(v)

        memory_mb = memory_bytes / (1024 * 1024)

        print("\nRegistry Memory Footprint (approximate):")
        print(f"  {memory_mb:.2f} MB")
        print(f"  {memory_bytes:,} bytes")

        # Memory footprint should be reasonable for in-memory storage
        # Allow up to 10MB in memory (file is JSON, in-memory Python objects are larger)
        assert memory_mb < 10.0, f"Memory footprint {memory_mb:.2f}MB seems excessive"
