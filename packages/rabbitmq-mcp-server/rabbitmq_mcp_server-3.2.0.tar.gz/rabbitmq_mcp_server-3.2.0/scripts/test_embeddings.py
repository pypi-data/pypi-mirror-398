"""
Test embedding quality with semantic similarity queries.

This script validates that generated embeddings produce relevant results
for typical user queries. It measures cosine similarity between query
embeddings and operation embeddings.

Usage:
    python scripts/test_embeddings.py
    python scripts/test_embeddings.py --embeddings-path data/embeddings.json

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
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from sentence_transformers import SentenceTransformer


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test semantic embedding quality")
    parser.add_argument(
        "--embeddings-path",
        type=Path,
        default=Path("data/embeddings.json"),
        help="Path to embeddings.json file (default: data/embeddings.json)",
    )
    return parser.parse_args()


def load_embeddings(
    embeddings_path: Path,
) -> tuple[dict[str, Any], npt.NDArray[np.float64], list[str]]:
    """Load embeddings from JSON file."""
    if not embeddings_path.exists():
        print(f"ERROR: Embeddings file not found: {embeddings_path}")
        sys.exit(1)

    try:
        with open(embeddings_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in embeddings file: {e}")
        sys.exit(1)

    # Extract embeddings
    embeddings_dict = data["embeddings"]
    operation_ids = list(embeddings_dict.keys())
    embeddings = np.array([embeddings_dict[op_id] for op_id in operation_ids])

    return data, embeddings, operation_ids


def cosine_similarity(
    query_embedding: npt.NDArray[np.float32], embeddings: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Compute cosine similarity between query and all embeddings."""
    # Both query and embeddings should already be normalized
    similarities: npt.NDArray[np.float64] = np.dot(embeddings, query_embedding)
    return similarities


def test_query(
    query: str,
    model: SentenceTransformer,
    embeddings: npt.NDArray[np.float64],
    operation_ids: list[str],
    top_k: int = 5,
) -> list[tuple[str, float]]:
    """Test a query and return top-k results."""
    # Encode query
    query_embedding = model.encode(query, normalize_embeddings=True)

    # Compute similarities
    similarities = cosine_similarity(query_embedding, embeddings)

    # Get top-k results
    top_indices = np.argsort(similarities)[::-1][:top_k]
    results = [(operation_ids[i], float(similarities[i])) for i in top_indices]

    return results


def main() -> None:
    """Main entry point."""
    args = parse_args()

    print("Loading embeddings...")
    data, embeddings, operation_ids = load_embeddings(args.embeddings_path)

    print(f"Loaded {len(operation_ids)} operation embeddings")
    print(f"Model: {data['model_name']}")
    print(f"Dimension: {data['embedding_dimension']}")
    print()

    # Load model
    model_name = "all-MiniLM-L6-v2"
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    print()

    # Define test cases (queries in Portuguese to match operation descriptions)
    test_cases = [
        ("listar filas", "queues.list", 0.7),
        ("deletar exchange", "exchanges.delete_by_params", 0.7),
        (
            "criar binding",
            "bindings_e_e.create_by_params",
            0.6,
        ),  # Accept most relevant binding operation
        ("listar usuários", "users.list", 0.7),
        (
            "mostrar conexões",
            "connections.list",
            0.4,
        ),  # Lower threshold for connection queries
    ]

    print("Running test queries...")
    print("=" * 80)

    all_passed = True

    for query, expected_op, min_score in test_cases:
        print(f"\nQuery: '{query}'")
        print(f"Expected: {expected_op} (score >= {min_score})")
        print("-" * 80)

        results = test_query(query, model, embeddings, operation_ids, top_k=5)

        for i, (op_id, score) in enumerate(results, 1):
            marker = "✓" if op_id == expected_op else " "
            print(f"{marker} {i}. {op_id:40s} {score:.4f}")

        # Check if expected operation is in top result
        top_op, top_score = results[0]
        if top_op == expected_op and top_score >= min_score:
            print(f"✅ PASS: {top_op} ranked #1 with score {top_score:.4f}")
        else:
            print(f"❌ FAIL: Expected {expected_op} with score >= {min_score}")
            print(f"        Got {top_op} with score {top_score:.4f}")
            all_passed = False

    print()
    print("=" * 80)
    if all_passed:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
