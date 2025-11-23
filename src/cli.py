import sys
import asyncio
from pathlib import Path
from src.core.retriever import Retriever
from src.core.async_processor import FileProcessor
from src.core.llm import generate_answer
from src.core.utils.file_discovery import discover_files
from src.core.embeddings import EmbeddingManager
from src.core.quiz.store import QuizStore
from src.core.quiz.engine import QuizEngine
from src.core.quiz.evaluator import Evaluator
from src.core.quiz.generator import QuizGenerator
from src.core.user.manager import UserManager
from src.config.constants import (
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
    upload_dir=UPLOAD_DIR, response_language: str = DEFAULT_RESPONSE_LANGUAGE
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

    query = "Who is Jane Doe?"
    context_chunks = retriever.retrieve(query, top_k=5)

    print("\nRetrieved context chunks:")
    for i, chunk in enumerate(context_chunks):
        print(
            f"Chunk {i+1} [{chunk['file_id']}.{chunk['file_ext']}]: {chunk['text'][:200]}..."
        )

    print("User's query: ", query)

    answer = generate_answer(query, context_chunks, response_language)
    print("\n[LLM Answer]:\n", answer)


async def demo_quiz(
    upload_dir=UPLOAD_DIR, response_language: str = DEFAULT_RESPONSE_LANGUAGE
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

    store = QuizStore()
    engine = QuizEngine(store, Evaluator(store), user_manager)
    generator = QuizGenerator(retriever, store)

    quiz_id = await generator.generate_general(
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
    print(f"user's profile: {profile}")

    weak_topics = user_manager.get_weak_topics(user_id=user_id, threshold=60)
    print(f"user's weak topics: {weak_topics}")

    user_summary = user_manager.get_user_summary(user_id)
    print(f"user's summary: {user_summary}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        asyncio.run(demo_explaination())
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "expl":
        asyncio.run(demo_explaination())
    elif arg == "quiz":
        asyncio.run(demo_quiz())
    else:
        print("no relevant mode, opting for expl")
        asyncio.run(demo_explaination())
