import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import uuid
from .processor import extract_text
from .chunker import chunk_text
from .embeddings import EmbeddingManager
from .registry import FileRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Processes multiple files asynchronously:
    - Extracts text from various file types
    - Chunks text
    - Generates embeddings in batches
    - Skips unchanged files using a registry
    """

    def __init__(
        self,
        embedder: Optional[EmbeddingManager] = None,
        max_concurrent: int = 4,
        batch_size: int = 16,
    ):
        self.embedder = embedder or EmbeddingManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.registry = FileRegistry()
        self.batch_size = batch_size

    async def process_files(self, file_paths: List[Path]) -> Dict[str, Dict[str, Any]]:
        """
        Processes multiple files asynchronously with concurrency control.

        Returns:
            Dict[file_id, Dict[str, Any]]: Summary per file with:
                - 'status': "processed", "skipped", or "error"
                - 'chunks': number of chunks generated (0 if skipped or error)
                - 'error': error message (None if successful)
        """
        results: Dict[str, Dict[str, Any]] = {}

        async def process_with_semaphore(fp: Path):
            async with self.semaphore:
                file_id = fp.stem
                file_ext = fp.suffix.lower().replace(".", "") or "unknown"

                # Skip unchanged files
                if self.registry.has_changed(fp) is False:
                    logger.info(f"[SKIP] {fp.name} (no changes detected)")
                    results[file_id] = {"status": "skipped", "chunks": 0, "error": None}
                    return

                try:
                    chunk_count = await self._process_single_file(fp, file_id, file_ext)
                    results[file_id] = {
                        "status": "processed",
                        "chunks": chunk_count,
                        "error": None,
                    }
                    self.registry.upsert(fp, chunk_count)
                except Exception as e:
                    logger.error(f"[ERROR] Failed to process {fp.name}: {e}")
                    results[file_id] = {"status": "error", "chunks": 0, "error": str(e)}

        await asyncio.gather(*(process_with_semaphore(fp) for fp in file_paths))
        return results

    async def _process_single_file(
        self, file_path: Path, file_id: str, file_ext: str
    ) -> int:
        """
        Processes a single file: text extraction, chunking, embedding generation.

        Returns:
            int: Number of chunks generated
        """
        logger.info(f"Processing {file_path.name}...")

        # 1️⃣ Extract text
        text = await asyncio.to_thread(extract_text, file_path)
        if not text.strip():
            logger.warning(f"Skipping {file_path.name} — no readable text.")
            return 0

        # 2️⃣ Chunk text
        chunks = await asyncio.to_thread(chunk_text, text)
        if not chunks:
            logger.warning(f"No chunks generated for {file_path.name}.")
            return 0

        # 3️⃣ Prepare chunk metadata with unique IDs
        chunks_metadata: List[Dict[str, Any]] = [
            {
                "text": chunk,
                "file_id": file_id,
                "file_ext": file_ext,
                "uid": uuid.uuid4().hex[:8],
            }
            for chunk in chunks
        ]

        # 4️⃣ Generate embeddings in batches
        for i in range(0, len(chunks_metadata), self.batch_size):
            batch = chunks_metadata[i : i + self.batch_size]
            await asyncio.to_thread(self.embedder.add_texts, batch)

        logger.info(f"Completed {file_path.name} ({len(chunks)} chunks)")
        return len(chunks)
