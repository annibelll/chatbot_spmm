from pathlib import Path
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  
UPLOAD_DIR = PROJECT_ROOT / "src" / "data" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


SQL3_PATH = "./data/registry.db"
DEFAULT_RESPONSE_LANGUAGE = "English"

OLLAMA_API_URL = "https://ollama.kucy.online/api"
LLM_MODEL = "mistral:latest"

CHROMA_DB_SAVINGS = "./data/embeddings"
SENTENCE_TRANSFORMER_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_COLLECTION_NAME = "documents"

# File processor
MAX_CONCURENT_FILES = 5
BATCH_SIZE = 16 

# Explanation
DEFAULT_NUMBER_OF_CHUNKS = 3

# Testing
NUMBER_OF_QUIZ_CHUNKS = 10
QUIZ_QUESTIONS_NUMBER = 2

CORRECTNESS_TRESHOLD = 6
