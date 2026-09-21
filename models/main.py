import os
import sys
import shutil
import tempfile
import logging
import json
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator

from config import llm, LOG_DIR, GEMINI_MODEL, EMBEDDING_MODEL, VECTOR_DB_PATH
from QA_Chain import QAChain
from save_history import save_history, load_history, delete_history, CHAT_SESSION_DIR

# ==============================================================================
# Cấu hình logging hệ thống (hỗ trợ cả môi trường Docker và môi trường cục bộ)
# ==============================================================================
os.makedirs(LOG_DIR, exist_ok=True)
try:
    os.chmod(LOG_DIR, 0o777)
except Exception:
    pass

# Xóa các handler cũ để tránh ghi trùng lặp
logger = logging.getLogger()
for h in list(logger.handlers):
    logger.removeHandler(h)
logger.setLevel(logging.DEBUG)

fmt = logging.Formatter('ts="%(asctime)s" level="%(levelname)s" name="%(name)s" msg="%(message)s"')

# 1. fastapi_app.log: log ứng dụng (DEBUG+)
app_file = os.path.join(LOG_DIR, "fastapi_app.log")
app_handler = RotatingFileHandler(app_file, maxBytes=10*1024*1024, backupCount=5, mode='a', encoding='utf-8')
app_handler.setLevel(logging.DEBUG)
app_handler.setFormatter(fmt)
logger.addHandler(app_handler)

# 2. syslog.log: log hệ thống (INFO+)
syslog_file = os.path.join(LOG_DIR, "syslog.log")
syslog_handler = RotatingFileHandler(syslog_file, maxBytes=5*1024*1024, backupCount=3, mode='a', encoding='utf-8')
syslog_handler.setLevel(logging.INFO)
syslog_handler.setFormatter(fmt)
logger.addHandler(syslog_handler)

# 3. stdout.log: ghi log ra stdout (INFO+)
stdout_file = os.path.join(LOG_DIR, "stdout.log")
stdout_handler = RotatingFileHandler(stdout_file, maxBytes=5*1024*1024, backupCount=3, mode='a', encoding='utf-8')
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(fmt)
stdout_handler.stream = sys.stdout
logger.addHandler(stdout_handler)

# 4. stderr.log: chỉ log lỗi ra stderr (ERROR+)
stderr_file = os.path.join(LOG_DIR, "stderr.log")
stderr_handler = RotatingFileHandler(stderr_file, maxBytes=5*1024*1024, backupCount=3, mode='a', encoding='utf-8')
stderr_handler.setLevel(logging.ERROR)
stderr_handler.setFormatter(fmt)
stderr_handler.stream = sys.stderr
logger.addHandler(stderr_handler)

# Đảm bảo phân quyền các file log nếu hệ điều hành hỗ trợ
for f in [app_file, syslog_file, stdout_file, stderr_file]:
    try:
        os.chmod(f, 0o666)
    except Exception:
        pass

# ==============================================================================
# Khởi tạo ứng dụng FastAPI & Middleware CORS
# ==============================================================================
app = FastAPI(
    title="MLOps AI QA Chatbot API",
    description="Hệ thống hỏi đáp tài liệu thông minh sử dụng Gemini và FAISS",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kích hoạt đo lường Prometheus metrics (/metrics)
Instrumentator().instrument(app).expose(app)

# Khởi tạo global QAChain
qa_chain = QAChain(llm=llm)
active_db_loaded = False  # Cờ kiểm tra trạng thái vector DB đã được nạp hay chưa

# Tự động nạp vector DB đã lưu sẵn nếu có trên ổ đĩa
if os.path.exists(os.path.join(VECTOR_DB_PATH, "index.faiss")):
    try:
        qa_chain.load_vector_db()
        active_db_loaded = True
        logging.info("Đã tự động nạp cơ sở dữ liệu vector DB hiện có.")
    except Exception as e:
        logging.warning(f"Chưa thể tự động nạp vector DB cũ: {e}")

# ==============================================================================
# Các endpoint API
# ==============================================================================

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/")
@app.get("/health")
def health_check():
    """
    Kiểm tra tình trạng hoạt động của dịch vụ (Health check).
    """
    return {
        "status": "healthy",
        "service": "MLOps Chatbot QA Backend",
        "gemini_model": GEMINI_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "active_db_loaded": active_db_loaded
    }

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Tải lên tệp PDF, xử lý phân tách và tạo vector DB với FAISS.
    """
    global active_db_loaded

    # Tạo thư mục tạm để xử lý file an toàn
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_pdf_path = os.path.join(tmpdirname, file.filename)

        with open(tmp_pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            qa_chain.create_chain(tmpdirname)
            active_db_loaded = True
            logging.info(f"Đã xử lý và nhúng vector thành công PDF: {file.filename}")
            return {"message": f"Đã xử lý PDF: {file.filename}"}
        except Exception as e:
            logging.error(f"Lỗi khi xử lý PDF: {e}")
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                return JSONResponse(
                    status_code=429,
                    content={"error": "Hạn mức Google Gemini API miễn phí (100 lượt/phút) tạm thời bị quá tải. Vui lòng chờ 30 giây rồi thử tải lại tệp."}
                )
            return JSONResponse(status_code=500, content={"error": f"Lỗi xử lý tài liệu: {err_str}"})

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    """
    Nhận câu hỏi của người dùng và truy vấn nội dung từ vector database.
    """
    if not active_db_loaded:
        return JSONResponse(status_code=400, content={"error": "Chưa upload file PDF nào hoặc cơ sở dữ liệu chưa sẵn sàng."})

    try:
        answer = qa_chain.query(question)
        logging.info(f"Truy vấn thành công cho câu hỏi: '{question}'")
        return {"question": question, "answer": answer}
    except Exception as e:
        logging.error(f"Lỗi khi trả lời câu hỏi '{question}': {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/save_history/")
async def save_chat_history(request: Request):
    """
    Lưu lại toàn bộ lịch sử đoạn chat của phiên.
    """
    data = await request.json()
    session_id = data.get("session_id")
    history = data.get("history", [])
    session_name = data.get("session_name")

    if not session_id:
        return JSONResponse(status_code=400, content={"error": "Thiếu session_id"})

    try:
        save_history(session_id, history, session_name)
        return {"message": "Lưu lịch sử thành công"}
    except Exception as e:
        logging.error(f"Lỗi khi lưu lịch sử: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Lấy chi tiết lịch sử tin nhắn của một session cụ thể.
    """
    try:
        history = load_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logging.error(f"Lỗi khi tải lịch sử session {session_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/history/{session_id}")
async def delete_chat_history(session_id: str):
    """
    Xoá lịch sử của một phiên hội thoại.
    """
    try:
        deleted = delete_history(session_id)
        if deleted:
            return {"message": f"Đã xoá lịch sử chat với session_id: {session_id}"}
        else:
            return JSONResponse(status_code=404, content={"error": "Không tìm thấy session_id"})
    except Exception as e:
        logging.error(f"Lỗi khi xoá session {session_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/list_sessions/")
def list_sessions():
    """
    Lấy danh sách tất cả các phiên trò chuyện đã lưu trữ.
    """
    try:
        os.makedirs(CHAT_SESSION_DIR, exist_ok=True)
        files = os.listdir(CHAT_SESSION_DIR)
        # Sắp xếp theo thời gian sửa đổi gần nhất lên đầu
        files = sorted(
            [f for f in files if f.endswith('.json')],
            key=lambda f: os.path.getmtime(os.path.join(CHAT_SESSION_DIR, f)),
            reverse=True
        )

        sessions = []
        for f in files:
            sid = f.replace('.json', '')
            # Đọc tên phiên chat nếu có
            try:
                with open(os.path.join(CHAT_SESSION_DIR, f), encoding='utf-8') as file:
                    obj = json.load(file)
                    name = obj.get('session_name', sid)
            except Exception:
                name = sid
            sessions.append({'id': sid, 'name': name})

        return {"sessions": sessions}
    except Exception as e:
        logging.error(f"Lỗi khi liệt kê danh sách session: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
