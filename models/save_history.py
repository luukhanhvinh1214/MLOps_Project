import json
import os
from config import CHAT_SESSION_DIR

# Đảm bảo thư mục lưu trữ phiên chat tồn tại
os.makedirs(CHAT_SESSION_DIR, exist_ok=True)

def load_history(session_id: str):
    """
    Tải lịch sử hội thoại dựa trên session_id.
    """
    path = os.path.join(CHAT_SESSION_DIR, f"{session_id}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("history", [])
        except Exception as e:
            print(f"Lỗi khi đọc file lịch sử {path}: {e}")
            return []
    return []

def save_history(session_id: str, history: list, session_name: str = None):
    """
    Lưu lịch sử hội thoại và tên phiên chat vào file JSON.
    """
    os.makedirs(CHAT_SESSION_DIR, exist_ok=True)
    path = os.path.join(CHAT_SESSION_DIR, f"{session_id}.json")
    data = {
        "session_id": session_id,
        "history": history
    }
    if session_name:
        data["session_name"] = session_name

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi khi lưu file lịch sử {path}: {e}")

def delete_history(session_id: str) -> bool:
    """
    Xoá phiên hội thoại đã lưu.
    """
    path = os.path.join(CHAT_SESSION_DIR, f"{session_id}.json")
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"Lỗi khi xoá file lịch sử {path}: {e}")
            return False
    return False
