from core.async_processor import FileProcessor
from core.embeddings import EmbeddingManager
from core.retriever import Retriever
from core.user.manager import UserManager
from core.quiz.store import QuizStore
from core.quiz.engine import QuizEngine
from core.quiz.generator import QuizGenerator
from core.quiz.evaluator import Evaluator

processor = FileProcessor()
embedder = EmbeddingManager()
retriever = Retriever(embedder)
user_manager = UserManager()
store = QuizStore()
engine = QuizEngine(store, Evaluator(store), user_manager)
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
