import os
from config import embeddings, llm, VECTOR_DB_PATH
from prepare_vector_db import VectorDBCreator
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class QAChain:
    """
    Lớp xử lý chuỗi RAG (Retrieval-Augmented Generation)
    sử dụng kiến trúc hiện đại LCEL (LangChain Expression Language).
    """
    def __init__(self, llm=llm, vector_db_path=None, k=5, max_tokens_limit=1024):
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        self.vector_db_path = vector_db_path if vector_db_path else VECTOR_DB_PATH
        self.embedding_model = embeddings
        self.llm = llm
        self.k = k
        self.max_tokens_limit = max_tokens_limit
        self.db = None
        self.chain = None
        self.prompt = None
        self.vector_creator = VectorDBCreator(vector_db_path=self.vector_db_path)

    def create_prompt(self, template=None):
        """
        Khởi tạo khuôn mẫu prompt tiếng Việt cho mô hình hỏi đáp.
        """
        if template is None:
            template = """Bạn là trợ lý AI thông minh trong hệ thống hỏi đáp tài liệu.
Sử dụng thông tin ngữ cảnh sau đây để trả lời câu hỏi bằng tiếng Việt một cách chính xác, rõ ràng và đầy đủ.
Nếu không biết hoặc thông tin không có trong tài liệu, hãy trả lời trung thực là bạn không biết, không cố suy đoán.

[Ngữ cảnh tài liệu]:
{context}

[Câu hỏi]:
{question}

[Câu trả lời]:"""
        self.prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        return self.prompt

    def _build_lcel_chain(self):
        """
        Xây dựng chuỗi truy vấn RAG theo kiến trúc chuẩn LCEL.
        """
        if self.db is None:
            raise ValueError("Vector DB chưa được tạo hoặc load. Vui lòng gọi create_chain hoặc load_vector_db trước.")
        if self.llm is None:
            raise ValueError("Bạn chưa truyền hoặc khởi tạo mô hình LLM.")
        if self.prompt is None:
            self.create_prompt()

        retriever = self.db.as_retriever(search_kwargs={"k": self.k})

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return self.chain

    def create_chain(self, pdf_dir_path: str):
        """
        Tạo FAISS vector DB từ thư mục chứa file PDF và kết nối chuỗi RAG.
        """
        print(f"Tạo vector DB từ thư mục PDF: {pdf_dir_path} ...")
        self.db = self.vector_creator.create_db_from_pdfs(pdf_dir_path)
        print("Đã tạo vector DB từ PDF và lưu tại:", self.vector_db_path)
        return self._build_lcel_chain()

    def load_vector_db(self):
        """
        Tải vector DB đã lưu sẵn từ ổ đĩa và kết nối chuỗi RAG.
        """
        print("Đang load vector DB từ:", self.vector_db_path)
        if not os.path.exists(self.vector_db_path):
            raise FileNotFoundError(f"Thư mục vector DB chưa tồn tại: {self.vector_db_path}")
        self.db = FAISS.load_local(self.vector_db_path, self.embedding_model, allow_dangerous_deserialization=True)
        print("Load vector DB thành công")
        return self._build_lcel_chain()

    def query(self, question: str) -> str:
        """
        Truy vấn câu hỏi dựa trên tài liệu đã được nạp.
        """
        if self.chain is None:
            raise ValueError("Chain chưa được tạo. Vui lòng gọi create_chain() hoặc tạo/load DB trước.")
        answer = self.chain.invoke(question)
        return str(answer).replace("<|file_separator|>", "").strip()