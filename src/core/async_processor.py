import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from core.processor import extract_text
from core.chunker import chunk_text
from core.embeddings import EmbeddingManager
from core.registry import FileRegistry


class FileProcessor:
    def __init__(
        self,
        embedder: Optional[EmbeddingManager] = None,
        max_concurrent: int = 5,
        batch_size: int = 16,
    ):
        self.embedder = embedder or EmbeddingManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.registry = FileRegistry()
        self.batch_size = batch_size

    async def process_files(self, file_paths: List[Path]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        await asyncio.gather(
            *(self._process_file_with_semaphore(results, fp) for fp in file_paths)
        )
        return results

    async def _process_file_with_semaphore(
        self, results: Dict[str, Dict[str, Any]], file_path: Path
    ):
        async with self.semaphore:
            file_id = file_path.stem
            file_ext = file_path.suffix.lower().replace(".", "") or "unknown"

            if self.registry.has_changed(file_path) is False:
                results[file_id] = {"status": "skipped", "chunks": 0, "error": None}
                print(f"Skipped {file_path.name} — unchanged.")
                return

            try:
                chunk_count = await self.extract_and_chunk_from_file(
                    file_path, file_id, file_ext
                )
                results[file_id] = {
                    "status": "processed",
                    "chunks": chunk_count,
                    "error": None,
                }
                self.registry.upsert(file_path, chunk_count)
            except Exception as e:
                print(f"Failed to process {file_path.name}: {e}")
                results[file_id] = {"status": "error", "chunks": 0, "error": str(e)}

    async def extract_and_chunk_from_file(
        self, file_path: Path, file_id: str, file_ext: str
    ) -> int:
        print(f"Processing {file_path.name}...")
        text = await asyncio.to_thread(extract_text, file_path)
        if not text.strip():
            print(f"Skipping {file_path.name} — no readable text.")
            return 0

        chunks = await asyncio.to_thread(chunk_text, text)
        if not chunks:
            print(f"No chunks generated for {file_path.name}.")
            return 0

        chunks_metadata: List[Dict[str, Any]] = [
            {
                "text": chunk,
                "file_id": file_id,
                "file_ext": file_ext,
                "uid": uuid.uuid4().hex[:8],
            }
            for chunk in chunks
        ]

        for i in range(0, len(chunks_metadata), self.batch_size):
            batch = chunks_metadata[i : i + self.batch_size]
            await asyncio.to_thread(self.embedder.encode_and_store_chunks, batch)

        print(f"Completed {file_path.name} ({len(chunks)} chunks)")
        return len(chunks)
