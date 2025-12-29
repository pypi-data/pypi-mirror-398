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

from pathlib import Path

import chromadb
import yaml
from sentence_transformers import SentenceTransformer

CONTRACTS_DIR = (
    Path(__file__).parent.parent / "specs" / "003-essential-topology-operations" / "contracts"
)
VECTOR_DB_DIR = Path(__file__).parent.parent / "data" / "vectors"
VECTOR_DB_PATH = VECTOR_DB_DIR / "rabbitmq.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# Load all operation IDs and descriptions from contracts
operations = []
for contract_file in CONTRACTS_DIR.glob("*.yaml"):
    with open(contract_file, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    for api_path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            op_id = op.get("operationId")
            desc = op.get("description", "")
            summary = op.get("summary", "")
            if op_id:
                operations.append({"id": op_id, "text": f"{op_id} {desc} {summary}".strip()})

# Generate embeddings
model = SentenceTransformer(MODEL_NAME)
texts = [op["text"] for op in operations]
embeddings = model.encode(texts)

# Store in ChromaDB
client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
collection = client.get_or_create_collection("rabbitmq_ops")
for op, emb in zip(operations, embeddings):
    collection.add(
        ids=[op["id"]],
        embeddings=[emb.tolist()],
        metadatas=[{"operation_id": op["id"]}],
        documents=[op["text"]],
    )

# Validate DB size
size_mb = sum(f.stat().st_size for f in VECTOR_DB_DIR.glob("*")) / (1024 * 1024)
if size_mb > 50:
    print(
        f"WARNING: Vector DB size {size_mb:.2f}MB exceeds 50MB limit. See plan.md for remediation steps."
    )
else:
    print(f"Vector DB generated: {size_mb:.2f}MB")
