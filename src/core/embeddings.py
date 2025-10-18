import logging
import hashlib
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EmbeddingManager:
    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(path="./data/embeddings")
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(
            f"Connected to ChromaDB with {self.collection.count()} stored documents."
        )

    def _hash_text(self, text: str) -> str:
        """Generate a short, consistent hash for a text chunk."""
        return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]

    def add_texts(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        # Prepare data
        for idx, c in enumerate(chunks):
            c.setdefault("uid", str(idx))
            c["hash"] = self._hash_text(c["text"])

        ids = [f"{c['file_id']}_{c['uid']}" for c in chunks]

        # Fetch existing IDs
        existing = set(self.collection.get(ids=ids)["ids"])

        # Filter out duplicates
        new_chunks = [c for c, id_ in zip(chunks, ids) if id_ not in existing]

        if not new_chunks:
            return

        texts = [c["text"] for c in new_chunks]
        metadatas = [{k: v for k, v in c.items() if k != "text"} for c in new_chunks]
        ids = [f"{c['file_id']}_{c['uid']}" for c in new_chunks]

        logger.info(f"Adding {len(new_chunks)} new chunks to collection...")
        embeddings = self.model.encode(texts, show_progress_bar=False)

        self.collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=ids,
            metadatas=metadatas,
        )
        logger.info(
            f"Collection now contains {self.collection.count()} total documents."
        )

    def query(self, query_text: str, top_k: int = 3):
        query_vec = self.model.encode([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_vec.tolist()], n_results=top_k
        )
        return results
