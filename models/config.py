import os
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# Nạp biến môi trường từ tệp .env (hỗ trợ cả thư mục hiện tại và thư mục gốc)
# ==============================================================================
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent

env_current = current_dir / ".env"
env_root = root_dir / ".env"

if env_current.exists():
    load_dotenv(dotenv_path=env_current)
elif env_root.exists():
    load_dotenv(dotenv_path=env_root)
else:
    load_dotenv()

# ==============================================================================
# Đọc các thông số cấu hình từ biến môi trường
# ==============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8085"))
LOG_DIR = os.getenv("LOG_DIR", "./logs")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_db_path")
CHAT_SESSION_DIR = os.getenv("CHAT_SESSION_DIR", "./data/chat_sessions")

# ==============================================================================
# Khởi tạo mô hình LLM và Embedding của OpenAI
# ==============================================================================
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Mô hình LLM
llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=OPENAI_API_KEY or None,
    temperature=0.2,
    max_retries=3
)

# Mô hình tạo vector nhúng (Embedding)
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY or None
)

# ==============================================================================
# Các thư viện bổ trợ phân tách văn bản và vector store
# ==============================================================================
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
