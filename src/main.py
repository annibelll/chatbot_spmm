import asyncio
from pathlib import Path
from core.retriever import Retriever
from core.llm import format_answer_with_citations, generate_answer
from core.async_processor import FileProcessor
from core.utils.file_discovery import discover_files


async def demo(upload_dir: str = "./data/uploads", response_language: str = "English"):
    print("[DYNAMIC DEMO] Starting dynamic file discovery and processing...\n")

    # 1️⃣ Discover files
    upload_path = Path(upload_dir)
    files_to_process = discover_files(upload_path)

    if not files_to_process:
        print(f"No valid files found in {upload_path}")
        return

    print(f"[INFO] Found {len(files_to_process)} files to process.")
    for f in files_to_process:
        print(" -", f.name)

    # 2️⃣ Process files asynchronously
    processor = FileProcessor()
    results = await processor.process_files(files_to_process)
    print("[INFO] File processing completed:", results)

    # 3️⃣ Example query
    query = "Tell me about the topics which are related to mobile networks?"
    response_language = "English"
    retriever = Retriever(processor.embedder)
    context_chunks = retriever.retrieve(query, top_k=5)

    print("\n[INFO] Retrieved context chunks:")
    for i, chunk in enumerate(context_chunks):
        print(
            f"Chunk {i+1} [{chunk['file_id']}.{chunk['file_ext']}]: {chunk['text'][:150]}..."
        )

    # 4️⃣ Generate LLM answer
    answer = generate_answer(query, context_chunks, response_language)
    answer_with_citations = format_answer_with_citations(answer)
    print("\n[LLM Answer with citations]:\n", answer_with_citations)



if __name__ == "__main__":
    asyncio.run(demo())
