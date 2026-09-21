# MLOps Project: AI Chatbot QA System

## 📝 Giới thiệu
Dự án này xây dựng một hệ thống hỏi đáp tài liệu (QA) sử dụng Large Language Model (LLM) và Vector Database (FAISS), cung cấp API FastAPI và giao diện React. Hệ thống hỗ trợ upload tài liệu PDF, tạo vector database, hỏi đáp thông minh, lưu lịch sử hội thoại, giám sát log và triển khai bằng Docker Compose.

## 📁 Cấu trúc thư mục
```plaintext
├── models/                # Backend FastAPI, xử lý LLM, vector DB, API
│   ├── main.py            # FastAPI app
│   ├── QA_Chain.py        # Xử lý tạo vector DB và hỏi đáp
│   ├── prepare_vector_db.py # Tạo FAISS vector DB từ PDF
│   ├── save_history.py    # Lưu/xóa lịch sử hội thoại
│   ├── config.py          # Cấu hình LLM, embedding
│   └── ...
├── Front_end/             # Frontend React (Vite)
│   ├── src/               # Mã nguồn React
│   ├── Dockerfile         # Docker hóa frontend
│   └── ...
├── infrastructure/        # Triển khai Docker Compose
│   └── docker-compose.yml # Khởi tạo backend, frontend
├── Monitoring/            # Giám sát Prometheus, Loki, Grafana
│   └── ...
├── requirements.txt       # Thư viện Python
├── Jenkinsfile            # CI/CD pipeline
└── README.md              # Tài liệu này
```

## 🚀 Khởi động nhanh
### 1. Chạy Backend (FastAPI)
```bash
cd models
uvicorn main:app --reload --port 8081
```
Truy cập docs: http://localhost:8081/docs

### 2. Chạy Frontend (React)
```bash
cd Front_end
npm install
npm run dev
```
Truy cập giao diện: http://localhost:5173

### 3. Chạy bằng Docker Compose
```bash
cd infrastructure
docker compose up --build
```
* Frontend: http://localhost:8000
* Backend: http://localhost:8085

## ⚙️ Các thành phần chính
- **FastAPI**: Xây dựng API hỏi đáp, upload PDF, lưu lịch sử.
- **LangChain, Google Gemini, FAISS**: Xử lý LLM, embedding, vector search.
- **React (Vite)**: Giao diện người dùng hiện đại.
- **Prometheus, Grafana, Loki**: Giám sát log, metrics hệ thống.
- **Jenkins**: Tự động hóa CI/CD.

## 🧑‍💻 Phát triển & Đóng góp
1. Cài Python 3.11+, Node.js 18+
2. Cài các thư viện Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Cài các package Node cho frontend:
   ```bash
   cd Front_end
   npm install
   ```
4. Đọc thêm hướng dẫn chi tiết trong `models/README.md` và `Front_end/README.md`.

## 📊 Giám sát & Logging
- Truy cập Grafana, Prometheus, Loki qua các port cấu hình trong Monitoring.
- Log ứng dụng lưu tại volume `fastapi-logs`.

## 📦 Triển khai & CI/CD
- Sử dụng Jenkinsfile để tự động build, deploy lên server.
- Docker Compose quản lý toàn bộ stack.

## 📚 Tài liệu tham khảo
- [LangChain](https://python.langchain.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vite + React](https://vitejs.dev/)
- [Prometheus](https://prometheus.io/), [Grafana](https://grafana.com/), [Loki](https://grafana.com/oss/loki/)


