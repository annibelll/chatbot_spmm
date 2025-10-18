from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any


class EmbeddingManager:
    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.Client(Settings(persist_directory="./data/embeddings"))
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def add_texts(self, chunks: List[Dict[str, Any]]):
        """
        Expects a list of dicts with at least:
        - 'text': str
        - 'file_id': str
        Optional:
        - 'file_ext': str
        - 'uid': str
        Additional metadata can be added freely.
        """
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        metadatas = [{k: v for k, v in c.items() if k != "text"} for c in chunks]
        ids = [f"{c['file_id']}_{c.get('uid', idx)}" for idx, c in enumerate(chunks)]

        embeddings = self.model.encode(texts, show_progress_bar=False)

        self.collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=ids,
            metadatas=metadatas,
        )

    def query(self, query_text: str, top_k: int = 3):
        query_vec = self.model.encode([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_vec.tolist()], n_results=top_k
        )
        return results
