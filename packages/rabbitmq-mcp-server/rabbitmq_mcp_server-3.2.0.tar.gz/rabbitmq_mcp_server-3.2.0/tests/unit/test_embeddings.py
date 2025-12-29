"""
Unit tests for embedding generation functionality.

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

import numpy as np
import pytest
from sentence_transformers import SentenceTransformer


@pytest.fixture
def embeddings_file():
    """Get path to embeddings file."""
    return Path("data/embeddings.json")


@pytest.fixture
def embeddings_data(embeddings_file):
    """Load embeddings data."""
    if not embeddings_file.exists():
        pytest.skip(f"Embeddings file not found: {embeddings_file}")

    with open(embeddings_file, encoding="utf-8") as f:
        return json.load(f)


def test_embeddings_file_exists(embeddings_file):
    """Test that embeddings.json exists."""
    assert embeddings_file.exists(), f"Embeddings file not found: {embeddings_file}"


def test_embeddings_file_valid_json(embeddings_file):
    """Test that embeddings.json is valid JSON."""
    with open(embeddings_file, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_embeddings_file_structure(embeddings_data):
    """Test that embeddings file has expected structure."""
    required_fields = [
        "model_name",
        "model_version",
        "embedding_dimension",
        "generation_timestamp",
        "embeddings",
    ]

    for field in required_fields:
        assert field in embeddings_data, f"Missing required field: {field}"


def test_embeddings_model_name(embeddings_data):
    """Test that model name is correct."""
    assert "all-MiniLM-L6-v2" in embeddings_data["model_name"]


def test_embeddings_dimension(embeddings_data):
    """Test that embedding dimension is 384."""
    assert embeddings_data["embedding_dimension"] == 384


def test_embeddings_count(embeddings_data):
    """Test that we have embeddings for all operations."""
    embeddings = embeddings_data["embeddings"]
    assert len(embeddings) > 100, "Expected 100+ operation embeddings"


def test_embedding_vector_dimension(embeddings_data):
    """Test that all embedding vectors have correct dimension."""
    embeddings = embeddings_data["embeddings"]
    for op_id, embedding in embeddings.items():
        assert isinstance(embedding, list), f"Embedding for {op_id} is not a list"
        assert (
            len(embedding) == 384
        ), f"Embedding for {op_id} has wrong dimension: {len(embedding)}"


def test_embedding_vector_normalized(embeddings_data):
    """Test that embeddings are normalized (unit vectors)."""
    embeddings = embeddings_data["embeddings"]

    for op_id, embedding in list(embeddings.items())[:10]:  # Test first 10
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        assert np.isclose(
            norm, 1.0, atol=1e-6
        ), f"Embedding for {op_id} not normalized: norm={norm}"


def test_embeddings_file_size(embeddings_file):
    """Test that embeddings file is under 50MB."""
    size_mb = embeddings_file.stat().st_size / (1024 * 1024)
    assert size_mb < 50, f"Embeddings file too large: {size_mb:.2f}MB"


def test_embedding_quality_exact_match(embeddings_data):
    """Test that exact matches produce high similarity scores."""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embeddings_data["embeddings"]

    # Test: "listar filas" should match "queues.list" with high score
    if "queues.list" in embeddings:
        query = "listar filas"
        query_embedding = model.encode(query, normalize_embeddings=True)

        # Convert embeddings to numpy array
        op_ids = list(embeddings.keys())
        embeddings_array = np.array([embeddings[op_id] for op_id in op_ids])

        # Compute similarities
        similarities = np.dot(embeddings_array, query_embedding)
        top_idx = np.argmax(similarities)
        top_op = op_ids[top_idx]
        top_score = similarities[top_idx]

        assert top_op == "queues.list", f"Expected 'queues.list', got '{top_op}'"
        assert top_score > 0.7, f"Similarity score too low: {top_score}"


def test_embedding_quality_semantic_search(embeddings_data):
    """Test that semantic search returns relevant results."""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embeddings_data["embeddings"]

    # Test multiple queries
    test_cases = [
        ("deletar exchange", "exchanges.delete"),
        ("listar usuários", "users.list"),
    ]

    op_ids = list(embeddings.keys())
    embeddings_array = np.array([embeddings[op_id] for op_id in op_ids])

    for query, expected_prefix in test_cases:
        query_embedding = model.encode(query, normalize_embeddings=True)
        similarities = np.dot(embeddings_array, query_embedding)

        # Check if expected operation is in top 3 results
        top_3_indices = np.argsort(similarities)[::-1][:3]
        top_3_ops = [op_ids[i] for i in top_3_indices]

        found = any(expected_prefix in op for op in top_3_ops)
        assert (
            found
        ), f"Query '{query}' didn't return expected operation prefix '{expected_prefix}' in top 3: {top_3_ops}"


def test_embeddings_load_performance(embeddings_file):
    """Test that embeddings load quickly."""
    import time

    start = time.time()
    with open(embeddings_file, encoding="utf-8") as f:
        data = json.load(f)
    embeddings_dict = data["embeddings"]
    _ = np.array([embeddings_dict[op_id] for op_id in embeddings_dict])
    elapsed = time.time() - start

    assert elapsed < 0.5, f"Loading took too long: {elapsed:.2f}s"


def test_embeddings_generation_timestamp(embeddings_data):
    """Test that generation timestamp is valid ISO format."""
    timestamp = embeddings_data["generation_timestamp"]
    from datetime import datetime

    # Should be able to parse as ISO datetime
    datetime.fromisoformat(timestamp)
