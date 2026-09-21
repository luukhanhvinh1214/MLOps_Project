# MLOps Project: AI Chatbot QA System

## Giới thiệu

Dự án này xây dựng một hệ thống hỏi đáp tài liệu (QA) sử dụng Large Language Model (Gemini 3.6 Flash) và Vector Database (FAISS), cung cấp API FastAPI và giao diện React (Vite). Hệ thống hỗ trợ tải lên tài liệu PDF, tạo vector database theo kiến trúc LCEL, hỏi đáp thông minh, lưu lịch sử hội thoại, giám sát metrics/log qua Prometheus, Grafana, Loki và tự động hóa triển khai bằng Jenkins và Docker Compose.

## Cấu trúc thư mục

```plaintext
├── models/                # Backend FastAPI, xử lý LLM, vector DB, API
│   ├── main.py            # FastAPI app & endpoints
│   ├── QA_Chain.py        # Xử lý chuỗi RAG (LCEL) và hỏi đáp
│   ├── prepare_vector_db.py # Tạo FAISS vector DB từ PDF
│   ├── save_history.py    # Lưu/xóa lịch sử hội thoại
│   ├── config.py          # Cấu hình LLM, embedding và biến môi trường
│   ├── .env.example       # Mẫu biến môi trường cho backend
│   └── ...
├── Front_end/             # Frontend React (Vite)
│   ├── src/               # Mã nguồn React
│   ├── Dockerfile         # Docker hóa frontend
│   └── ...
├── infrastructure/        # Triển khai Docker Compose
│   └── docker-compose.yml # Khởi tạo backend, frontend, monitoring
├── Monitoring/            # Giám sát Prometheus, Loki, Grafana, Promtail
│   └── ...
├── .env.example           # Mẫu biến môi trường cho dự án
├── requirements.txt       # Thư viện Python
├── Jenkinsfile            # CI/CD pipeline
└── README.md              # Tài liệu này
```

## Khởi động nhanh

### 1. Cấu hình biến môi trường

Trước khi chạy hệ thống, hãy sao chép tệp mẫu và cấu hình API Key:

```bash
cp .env.example .env
# Mở tệp .env và điền GOOGLE_API_KEY của bạn
```

### 2. Chạy Backend (FastAPI)

```bash
cd models
uvicorn main:app --reload --port 8085
```

Truy cập API Docs: http://localhost:8085/docs  
Health check: http://localhost:8085/health

### 3. Chạy Frontend (React)

```bash
cd Front_end
npm install
npm run dev
```

Truy cập giao diện: http://localhost:5173

### 4. Chạy bằng Docker Compose

```bash
cd infrastructure
docker compose up --build
```

- Frontend: http://localhost:8000
- Backend: http://localhost:8085

## Các thành phần chính

- **FastAPI**: Xây dựng API hỏi đáp, upload PDF, lưu lịch sử và health check.
- **LangChain, Google Gemini, FAISS**: Xử lý chuỗi RAG (LCEL), embedding vector và truy vấn ngữ cảnh.
- **React (Vite)**: Giao diện người dùng hiện đại, tối ưu cho cả Web và Mobile.
- **Prometheus, Grafana, Loki**: Giám sát log, metrics hệ thống.
- **Jenkins**: Tự động hóa CI/CD pipeline.

## Phát triển & Đóng góp

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

## Giám sát & Logging

- Truy cập Grafana, Prometheus, Loki qua các port cấu hình trong Monitoring.
- Log ứng dụng lưu tại volume `fastapi-logs` (hoặc thư mục `./logs` khi chạy cục bộ).

## Triển khai & CI/CD

- Sử dụng Jenkinsfile để tự động build, deploy lên server.
- Docker Compose quản lý toàn bộ stack.

## Tài liệu tham khảo

- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [Jenkins](https://www.jenkins.io/doc/)
- [Prometheus](https://prometheus.io/), [Grafana](https://grafana.com/), [Loki](https://grafana.com/oss/loki/)

