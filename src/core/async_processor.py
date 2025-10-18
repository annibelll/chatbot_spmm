import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging
import uuid
from .processor import extract_text
from .chunker import chunk_text
from .embeddings import EmbeddingManager

# Setup structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileProcessor:
    def __init__(
        self, embedder: EmbeddingManager | None = None, max_concurrent: int = 4
    ):
        self.embedder = embedder or EmbeddingManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_files(self, file_paths: List[Path]) -> Dict[str, int]:
        """
        Process multiple files asynchronously with controlled concurrency.
        Returns a dict of file_id -> chunk count.
        """
        results: Dict[str, int] = {}

        async def process_with_semaphore(fp: Path):
            async with self.semaphore:
                file_id = fp.stem
                file_ext = fp.suffix.lower().replace(".", "") or "unknown"
                count = await self._process_single_file(fp, file_id, file_ext)
                results[file_id] = count

        await asyncio.gather(*(process_with_semaphore(fp) for fp in file_paths))
        return results

    async def _process_single_file(
        self, file_path: Path, file_id: str, file_ext: str
    ) -> int:
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
        batch_size = 16
        for i in range(0, len(chunks_metadata), batch_size):
            batch = chunks_metadata[i : i + batch_size]
            await asyncio.to_thread(self.embedder.add_texts, batch)

        logger.info(f"Completed {file_path.name} ({len(chunks)} chunks)")
        return len(chunks)
