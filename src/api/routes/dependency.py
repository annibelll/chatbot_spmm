from src.core.async_processor import FileProcessor
from src.core.embeddings import EmbeddingManager
from src.core.retriever import Retriever
from src.core.user.manager import UserManager
from src.core.quiz.store import QuizStore
from src.core.quiz.engine import QuizEngine
from src.core.quiz.generator import QuizGenerator
from src.core.quiz.evaluator import Evaluator

processor = FileProcessor()
embedder = EmbeddingManager()
retriever = Retriever(embedder)

user_manager = UserManager()
store = QuizStore()

evaluator = Evaluator(store)
engine = QuizEngine(store, evaluator, user_manager)
generator = QuizGenerator(retriever, store)


def get_processor() -> FileProcessor:
    return processor

def get_embedder() -> EmbeddingManager:
    return embedder

def get_retriever() -> Retriever:
    return retriever

def get_user_manager() -> UserManager:
    return user_manager

def get_quiz_store() -> QuizStore:
    return store

def get_quiz_engine() -> QuizEngine:
    return engine

def get_quiz_generator() -> QuizGenerator:
    return generator
