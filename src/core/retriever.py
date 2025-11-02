import re
from typing import List, Dict, Any
from core.embeddings import EmbeddingManager


def normalize_query(query: str) -> str:
    query = query.lower().strip()
    query = re.sub(r"\s+", " ", query)
    return query


class Retriever:
    def __init__(self, embedder: EmbeddingManager):
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        query_norm = normalize_query(query)
        results = self.embedder.query(query_norm, top_k)

        docs = [
            {
                "id": chunk_id,
                "file_id": metadata.get("file_id", "unknown"),
                "file_ext": metadata.get("file_ext", "unknown"),
                "text": doc,
                "score": score,
            }
            for chunk_id, doc, metadata, score in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
        return docs
