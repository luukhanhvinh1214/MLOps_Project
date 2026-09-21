import os
import time
import re
import logging
from config import embeddings, VECTOR_DB_PATH

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS

class VectorDBCreator:
    def __init__(self, vector_db_path=None):
        # Đường dẫn lưu trữ FAISS vector database
        self.vector_db_path = vector_db_path if vector_db_path else VECTOR_DB_PATH
        self.embedding_model = embeddings

    def _build_faiss_with_retry(self, chunks):
        """
        Tạo và nhúng vectorstore FAISS theo từng đợt (batch) với cơ chế tự động chờ và thử lại
        khi chạm giới hạn Rate Limit (100 RPM) của gói miễn phí Google Gemini API.
        """
        if not chunks:
            raise ValueError("Không thể trích xuất nội dung văn bản từ tài liệu (tệp rỗng hoặc dạng ảnh scan chưa có OCR).")

        BATCH_SIZE = 35  # Giới hạn 35 chunks/batch để luôn an toàn dưới hạn mức 100 requests/phút của Gemini Free Tier
        db = None
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        logging.info(f"Bắt đầu nhúng {len(chunks)} đoạn văn bản thành {total_batches} đợt xử lý...")

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    if db is None:
                        db = FAISS.from_documents(batch, embedding=self.embedding_model)
                    else:
                        db.add_documents(batch)
                    logging.info(f"Hoàn thành đợt nhúng vector {batch_num}/{total_batches} ({len(batch)} đoạn)")
                    break
                except Exception as e:
                    err_str = str(e)
                    if ("429" in err_str or "quota" in err_str.lower()) and attempt < max_retries - 1:
                        retry_match = re.search(r"retry in ([\d\.]+)s", err_str)
                        wait_time = float(retry_match.group(1)) + 2.0 if retry_match else 25.0
                        logging.warning(f"[Đợt {batch_num}/{total_batches}] Chạm hạn mức Gemini Free Tier (429). Đang tạm nghỉ {wait_time:.1f}s trước khi thử lại...")
                        time.sleep(wait_time)
                    else:
                        logging.error(f"Lỗi khi nhúng đợt {batch_num}/{total_batches}: {e}")
                        raise e

            # Nghỉ nhẹ 1.5s giữa các đợt để giãn cách request
            if i + BATCH_SIZE < len(chunks):
                time.sleep(1.5)

        # Lưu vectorstore vào thư mục
        os.makedirs(self.vector_db_path, exist_ok=True)
        db.save_local(self.vector_db_path)
        return db

    def create_db_from_text(self, raw_text: str):
        # Chia nhỏ text với kích thước chuẩn 1500 ký tự (khoảng 250-300 từ)
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1500,
            chunk_overlap=150,
            length_function=len
        )
        chunks = text_splitter.split_text(raw_text)

        if not chunks:
            raise ValueError("Văn bản đầu vào trống, không thể tạo vector database.")

        doc_chunks = [Document(page_content=c) for c in chunks if c.strip()]
        return self._build_faiss_with_retry(doc_chunks)

    def create_db_from_pdfs(self, pdf_dir_path: str):
        # Loader quét toàn bộ file pdf trong thư mục
        loader = DirectoryLoader(pdf_dir_path, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()

        if not documents:
            raise ValueError(f"Không tìm thấy tệp PDF hoặc tài liệu rỗng trong thư mục: {pdf_dir_path}")

        # Chia nhỏ tài liệu thành các đoạn vừa phải (1500 ký tự phù hợp với context window lớn của LLM hiện đại)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        chunks = text_splitter.split_documents(documents)

        # Lọc bỏ các chunk quá ngắn (chỉ có tiêu đề đầu trang/số trang rác)
        valid_chunks = [c for c in chunks if len(c.page_content.strip()) >= 15]

        if not valid_chunks:
            raise ValueError("Không thể trích xuất nội dung văn bản từ tệp PDF (tệp có thể là trang trắng hoặc ảnh quét chưa qua OCR).")

        return self._build_faiss_with_retry(valid_chunks)
