"""
Generate semantic embeddings for RabbitMQ operations.

This script pre-computes vector embeddings for all operation descriptions
from operations.json using sentence-transformers. The embeddings are stored
in a JSON file for fast loading and semantic similarity calculations at runtime.

Usage:
    python scripts/generate_embeddings.py
    python scripts/generate_embeddings.py --registry-path data/operations.json
    python scripts/generate_embeddings.py --output-path data/embeddings.json
    python scripts/generate_embeddings.py --model-name all-MiniLM-L6-v2

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
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from sentence_transformers import SentenceTransformer

# Constants
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
DEFAULT_BATCH_SIZE = 32
MAX_FILE_SIZE_MB = 50


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate semantic embeddings for RabbitMQ operations"
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        default=Path("data/operations.json"),
        help="Path to operations.json registry file (default: data/operations.json)",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/embeddings.json"),
        help="Path to output embeddings.json file (default: data/embeddings.json)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help=f"Sentence-transformers model name (default: {DEFAULT_MODEL_NAME})",
    )
    return parser.parse_args()


def load_operations(registry_path: Path) -> dict[str, Any]:
    """Load operations from registry JSON file."""
    if not registry_path.exists():
        print(f"ERROR: Registry file not found: {registry_path}")
        print("Please ensure operations.json exists before generating embeddings.")
        sys.exit(1)

    try:
        with open(registry_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in registry file: {e}")
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: Registry file must contain a JSON object")
        sys.exit(1)

    # Handle both direct operations dict and nested structure
    if "operations" in data:
        operations = data["operations"]
    else:
        operations = data

    if not operations:
        print("ERROR: No operations found in registry file")
        sys.exit(1)

    return operations


def extract_descriptions(operations: dict[str, Any]) -> list[tuple[str, str]]:
    """Extract operation IDs and descriptions from registry."""
    descriptions = []

    for op_id, op_data in operations.items():
        if not isinstance(op_data, dict):
            continue

        description = op_data.get("description", "")
        if not description:
            print(f"WARNING: Operation {op_id} has no description")
            description = op_id  # Fallback to operation ID

        descriptions.append((op_id, description))

    if not descriptions:
        print("ERROR: No valid operations found in registry")
        sys.exit(1)

    return descriptions


def generate_embeddings(
    model: SentenceTransformer, descriptions: list[str]
) -> npt.NDArray[np.float32]:
    """Generate embeddings for descriptions using sentence-transformers."""
    print(f"Encoding {len(descriptions)} descriptions...")

    # Batch encode for efficiency
    embeddings: npt.NDArray[np.float32] = model.encode(
        descriptions,
        batch_size=DEFAULT_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,  # Normalize to unit vectors for cosine similarity
    )

    # Validate embedding dimension
    if embeddings.shape[1] != EMBEDDING_DIMENSION:
        print(
            f"ERROR: Expected embedding dimension {EMBEDDING_DIMENSION}, got {embeddings.shape[1]}"
        )
        sys.exit(1)

    return embeddings


def build_output_structure(
    model: SentenceTransformer,
    operation_ids: list[str],
    embeddings: npt.NDArray[np.float32],
) -> dict[str, Any]:
    """Build output JSON structure with metadata and embeddings."""
    # Extract model metadata
    model_name = f"sentence-transformers/{model.get_sentence_embedding_dimension()}"
    try:
        # Try to get actual model name from model config
        model_name = f"sentence-transformers/{DEFAULT_MODEL_NAME}"
    except Exception:
        pass

    # Build embeddings dict
    embeddings_dict = {}
    for op_id, embedding in zip(operation_ids, embeddings):
        embeddings_dict[op_id] = embedding.tolist()

    # Build output structure
    output = {
        "model_name": model_name,
        "model_version": "2.6.0",  # sentence-transformers version
        "embedding_dimension": EMBEDDING_DIMENSION,
        "generation_timestamp": datetime.now().isoformat(),
        "embeddings": embeddings_dict,
    }

    return output


def save_embeddings(output_path: Path, data: dict[str, Any]) -> None:
    """Save embeddings to JSON file."""
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with formatting
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Validate file is readable
    try:
        with open(output_path, encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Generated invalid JSON: {e}")
        sys.exit(1)

    # Check file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        print(
            f"WARNING: Embeddings file size {size_mb:.2f}MB exceeds {MAX_FILE_SIZE_MB}MB limit"
        )
    else:
        print(f"Embeddings file size: {size_mb:.2f}MB")


def main() -> None:
    """Main entry point."""
    start_time = time.time()

    args = parse_args()

    print("Starting embedding generation")
    print(f"Registry path: {args.registry_path}")
    print(f"Output path: {args.output_path}")
    print(f"Model: {args.model_name}")
    print()

    # Load operations
    print(f"Loading operations from {args.registry_path}...")
    operations = load_operations(args.registry_path)
    print(f"Loaded {len(operations)} operations")

    # Extract descriptions
    descriptions_list = extract_descriptions(operations)
    operation_ids = [op_id for op_id, _ in descriptions_list]
    descriptions = [desc for _, desc in descriptions_list]
    print(f"Extracted {len(descriptions)} descriptions")

    # Initialize model
    print(f"Loading model: {args.model_name}")
    print(
        "Note: First run will download model (~90MB) to ~/.cache/torch/sentence_transformers/"
    )
    try:
        model = SentenceTransformer(args.model_name)
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}")
        print("\nTroubleshooting:")
        print("- Check internet connection (model needs to download on first run)")
        print("- Verify disk space in ~/.cache/torch/sentence_transformers/")
        print("- Try running: pip install sentence-transformers torch")
        sys.exit(1)

    print("Model loaded successfully")
    print()

    # Generate embeddings
    embeddings = generate_embeddings(model, descriptions)
    print(f"Generated {len(embeddings)} embeddings")

    # Build output structure
    output = build_output_structure(model, operation_ids, embeddings)
    print("Built output structure with metadata")

    # Save to file
    print(f"Saving embeddings to {args.output_path}...")
    save_embeddings(args.output_path, output)
    print("Embeddings saved successfully")

    elapsed = time.time() - start_time
    print()
    print(f"Generation completed in {elapsed:.2f} seconds")

    if elapsed > 60:
        print("WARNING: Generation took longer than 60 seconds")


if __name__ == "__main__":
    main()
