from typing import List, Dict, Any
import re


def normalize_query(query: str) -> str:
    query = query.lower().strip()
    query = re.sub(r"\s+", " ", query)
    return query


class Retriever:
    def __init__(self, embedder):
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top-k chunks from the embedding store for a query.
        Each dict contains:
        - 'text': chunk text
        - 'file_id': originating file name
        - 'file_ext': file extension
        - 'score': similarity score
        - 'id': unique chunk ID
        """
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
