import asyncio
from pathlib import Path
from core.retriever import Retriever
from core.async_processor import FileProcessor
from core.llm import generate_answer
from core.utils.file_discovery import discover_files
from core.embeddings import EmbeddingManager
from core.quiz.store import QuizStore
from core.quiz.engine import QuizEngine
from core.quiz.evaluator import Evaluator
from core.quiz.generator import QuizGenerator
from core.user.manager import UserManager
from config.constants import (
    UPLOAD_DIR,
    DEFAULT_RESPONSE_LANGUAGE,
    QUIZ_QUESTIONS_NUMBER,
)

# Singletones
processor = FileProcessor()
embedder = EmbeddingManager()
retriever = Retriever(embedder)
user_manager = UserManager()


async def demo_explaination(
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

    await processor.process_files(files_to_process)

    query = "Explain the difference between AMF and SMF."
    context_chunks = retriever.retrieve(query, top_k=5)

    print("\nRetrieved context chunks:")
    for i, chunk in enumerate(context_chunks):
        print(
            f"Chunk {i+1} [{chunk['file_id']}.{chunk['file_ext']}]: {chunk['text'][:150]}..."
        )

    print("User's query: ", query)

    answer = generate_answer(query, context_chunks, response_language)
    print("\n[LLM Answer]:\n", answer)


async def demo_quiz(
    upload_dir: str = UPLOAD_DIR, response_language: str = DEFAULT_RESPONSE_LANGUAGE
):
    user_name = input("Enter your name: ").strip() or "default_user"
    user_id = user_manager.get_or_create_user(user_name)
    print(f"Welcome, {user_name} (user_id={user_id})")

    upload_path = Path(upload_dir)
    files_to_process = discover_files(upload_path)
    if not files_to_process:
        print(f"No valid files found in {upload_path}")
        return

    print(f"Found {len(files_to_process)} files to process.")
    for f in files_to_process:
        print(" -", f.name)

    await processor.process_files(files_to_process)

    topic = ""
    store = QuizStore()
    engine = QuizEngine(store, Evaluator(store), user_manager)
    generator = QuizGenerator(retriever, store)

    quiz_id = await generator.generate(
        topic,
        num_questions=QUIZ_QUESTIONS_NUMBER,
        response_language=response_language,
    )

    q = engine.start(user_id, quiz_id)
    while q:
        print(f"\nQ: {q['question']}")
        if q["options"]:
            for i, opt in enumerate(q["options"]):
                print(f"  {chr(97+i)}) {opt}")
        ans = input("Your answer: ")
        result = engine.answer(q["id"], ans)
        print(result["feedback"])
        q = result.get("next")
        if not q:
            print("\nQuiz complete!")
            print(result["summary"])
            break

    profile = user_manager.get_user_profile(user_id)
    print(profile)


if __name__ == "__main__":
    asyncio.run(demo_explaination())
    # asyncio.run(demo_quiz())
