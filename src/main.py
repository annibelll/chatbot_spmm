import asyncio
from pathlib import Path
from core.retriever import Retriever
from core.async_processor import FileProcessor
from core.llm import generate_answer
from core.utils.file_discovery import discover_files
from config.constants import UPLOAD_DIR, DEFAULT_RESPONSE_LANGUAGE


async def demo(
    upload_dir: str = UPLOAD_DIR, response_language: str = DEFAULT_RESPONSE_LANGUAGE
):
    upload_path = Path(upload_dir)
    files_to_process = discover_files(upload_path)

    if not files_to_process:
        print(f"No valid files found in {upload_path}")
        return

    print(f"Found {len(files_to_process)} files to process.")
    for f in files_to_process:
        print(" -", f.name)

    processor = FileProcessor()
    await processor.process_files(files_to_process)

    query = "Who is Jane Doe?"
    retriever = Retriever(processor.embedder)
    context_chunks = retriever.retrieve(query, top_k=5)

    print("\nRetrieved context chunks:")
    for i, chunk in enumerate(context_chunks):
        print(
            f"Chunk {i+1} [{chunk['file_id']}.{chunk['file_ext']}]: {chunk['text'][:150]}..."
        )

    print("User's query: ", query)

    answer = generate_answer(query, context_chunks, response_language)
    print("\n[LLM Answer]:\n", answer)


if __name__ == "__main__":
    asyncio.run(demo())
