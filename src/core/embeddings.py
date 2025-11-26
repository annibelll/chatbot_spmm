import hashlib
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from src.config.constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_SAVINGS,
    SENTENCE_TRANSFORMER_MODEL,
)


class EmbeddingManager:
    def __init__(self, collection_name: str = CHROMA_COLLECTION_NAME):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_SAVINGS)
        self.model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        self.collection = self.client.get_or_create_collection(collection_name)

    def encode_and_store_chunks(self, chunks: List[Dict[str, Any]]):
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
        embeddings = self.model.encode(texts, show_progress_bar=False)
        self.collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=ids,
            metadatas=metadatas,
        )

    def query(self, query_text: str, top_k: int):
        query_vec = self.model.encode([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_vec.tolist()], n_results=top_k
        )
        return results

    def delete_by_filename(self, filename: str):
        try:
            filename = filename.strip().lower()
            file_id = filename.split(".")[0]
            self.collection.delete(where={"file_id": file_id})
            print(f"✅ Embeddings for '{filename}' deleted.")
        except Exception as e:
            print(f"❌ Error deleting embeddings for {filename}: {e}")

    def clear_database(self):
        try:
            self.collection.delete(where={"file_id": {"$ne": None}})
            print("🧹 All embeddings cleared from collection.")
        except Exception as e:
            print(f"❌ Error clearing database: {e}")

    def _hash_text(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
