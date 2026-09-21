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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8085"))
LOG_DIR = os.getenv("LOG_DIR", "./logs")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_db_path")
CHAT_SESSION_DIR = os.getenv("CHAT_SESSION_DIR", "./data/chat_sessions")

# ==============================================================================
# Khởi tạo mô hình LLM và Embedding của Google
# ==============================================================================
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Mô hình LLM (Gemini 3.6 Flash)
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY if GOOGLE_API_KEY else None,
    temperature=0.2,
    max_retries=3
)

# Mô hình tạo vector nhúng (Embedding)
embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    google_api_key=GOOGLE_API_KEY if GOOGLE_API_KEY else None
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
