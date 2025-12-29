"""
Benchmark embedding performance for loading and query operations.

This script measures the performance of:
- Loading embeddings.json into memory
- Encoding a single query
- Computing cosine similarities with all operations

Usage:
    python scripts/benchmark_embeddings.py
    python scripts/benchmark_embeddings.py --embeddings-path data/embeddings.json

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

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from sentence_transformers import SentenceTransformer


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Benchmark embedding performance")
    parser.add_argument(
        "--embeddings-path",
        type=Path,
        default=Path("data/embeddings.json"),
        help="Path to embeddings.json file (default: data/embeddings.json)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of query iterations for averaging (default: 100)",
    )
    return parser.parse_args()


def benchmark_loading(
    embeddings_path: Path,
) -> tuple[float, dict[str, Any], npt.NDArray[np.float64]]:
    """Benchmark loading embeddings from file."""
    start = time.time()

    with open(embeddings_path, encoding="utf-8") as f:
        data = json.load(f)

    embeddings_dict = data["embeddings"]
    operation_ids = list(embeddings_dict.keys())
    embeddings = np.array([embeddings_dict[op_id] for op_id in operation_ids])

    elapsed = time.time() - start
    return elapsed, data, embeddings


def benchmark_query(
    model: SentenceTransformer,
    embeddings: npt.NDArray[np.float64],
    query: str,
    iterations: int,
) -> tuple[float, float]:
    """Benchmark query encoding and similarity computation."""
    # Warmup
    model.encode(query, normalize_embeddings=True)
    np.dot(embeddings, embeddings[0])

    # Benchmark encoding
    encode_times = []
    for _ in range(iterations):
        start = time.time()
        query_embedding = model.encode(query, normalize_embeddings=True)
        elapsed = time.time() - start
        encode_times.append(elapsed)

    # Benchmark similarity computation
    similarity_times = []
    query_embedding = model.encode(query, normalize_embeddings=True)
    for _ in range(iterations):
        start = time.time()
        similarities = np.dot(embeddings, query_embedding)
        _ = np.argsort(similarities)[::-1][:5]
        elapsed = time.time() - start
        similarity_times.append(elapsed)

    avg_encode = sum(encode_times) / len(encode_times)
    avg_similarity = sum(similarity_times) / len(similarity_times)

    return avg_encode, avg_similarity


def main() -> None:
    """Main entry point."""
    args = parse_args()

    print("=" * 80)
    print("Embedding Performance Benchmark")
    print("=" * 80)
    print()

    # Benchmark loading
    print("1. Loading embeddings.json...")
    print("-" * 80)
    load_time, data, embeddings = benchmark_loading(args.embeddings_path)
    print(f"File size: {args.embeddings_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"Operations: {len(embeddings)}")
    print(f"Load time: {load_time*1000:.2f} ms")
    if load_time < 0.5:
        print("✅ PASS: Load time under 500ms")
    else:
        print("❌ FAIL: Load time exceeds 500ms")
    print()

    # Load model
    print("2. Loading sentence-transformers model...")
    print("-" * 80)
    model_name = "all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    print(f"Model: {model_name}")
    print()

    # Benchmark query
    print(f"3. Query performance ({args.iterations} iterations)...")
    print("-" * 80)
    query = "listar filas"
    avg_encode, avg_similarity = benchmark_query(
        model, embeddings, query, args.iterations
    )

    total_query_time = avg_encode + avg_similarity

    print(f"Query encoding: {avg_encode*1000:.2f} ms (avg)")
    print(f"Similarity computation: {avg_similarity*1000:.2f} ms (avg)")
    print(f"Total query time: {total_query_time*1000:.2f} ms (avg)")
    print()

    if total_query_time < 0.1:
        print("✅ PASS: Total query time under 100ms")
    else:
        print("❌ FAIL: Total query time exceeds 100ms")

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Load time:        {load_time*1000:8.2f} ms (target: <500ms)")
    print(f"Query time:       {total_query_time*1000:8.2f} ms (target: <100ms)")
    print(f"Embeddings count: {len(embeddings):8d}")
    print(
        f"File size:        {args.embeddings_path.stat().st_size/(1024*1024):8.2f} MB (target: <50MB)"
    )
    print()

    # Overall result
    all_passed = load_time < 0.5 and total_query_time < 0.1
    if all_passed:
        print("✅ All performance targets met!")
        sys.exit(0)
    else:
        print("❌ Some performance targets not met")
        sys.exit(1)


if __name__ == "__main__":
    main()
