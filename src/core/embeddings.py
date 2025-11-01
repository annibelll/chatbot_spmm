import hashlib
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from config.constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_SAVINGS,
    SENTENCE_TRANSFORMER_MODEL,
)


class EmbeddingManager:
    def __init__(self, collection_name: str = CHROMA_COLLECTION_NAME):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_SAVINGS)
        self.model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        self.collection = self.client.get_or_create_collection(collection_name)

    def _hash_text(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]

    def add_texts(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        for idx, c in enumerate(chunks):
            c.setdefault("uid", str(idx))
            c["hash"] = self._hash_text(c["text"])

        ids = [f"{c['file_id']}_{c['uid']}" for c in chunks]
        existing = set(self.collection.get(ids=ids)["ids"])
        new_chunks = [c for c, id_ in zip(chunks, ids) if id_ not in existing]

        if not new_chunks:
            return

        texts = [c["text"] for c in new_chunks]
        metadatas = [{k: v for k, v in c.items() if k != "text"} for c in new_chunks]
        ids = [f"{c['file_id']}_{c['uid']}" for c in new_chunks]

        print(f"Adding {len(new_chunks)} new chunks to collection...")
        embeddings = self.model.encode(texts, show_progress_bar=False)
        self.collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=ids,
            metadatas=metadatas,
        )
        print(f"Collection now contains {self.collection.count()} total documents.")

    def query(self, query_text: str, top_k: int = 3):
        query_vec = self.model.encode([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_vec.tolist()], n_results=top_k
        )
        return results
