import { useState, useRef, useEffect, useCallback } from 'react';
import './App.css';
import logoLkv from './assets/logo-lkv.png';

const API_BASE = import.meta.env.VITE_API_BASE || (
  typeof window !== 'undefined' && window.location.hostname
    ? `http://${window.location.hostname}:8085`
    : 'http://localhost:8085'
);

function App() {
  const [pdfName, setPdfName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [savingHistory, setSavingHistory] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('vklv_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'light') {
      document.documentElement.classList.add('theme-light');
    } else {
      document.documentElement.classList.remove('theme-light');
    }
    localStorage.setItem('vklv_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Modals & Notifications
  const [toast, setToast] = useState(null); // { type: 'success' | 'error' | 'info', message: string }
  const [activeSessionName, setActiveSessionName] = useState('');
  const [sessionToDelete, setSessionToDelete] = useState(null);

  const [sessionId, setSessionId] = useState(() => {
    let sid = localStorage.getItem('chat_session_id');
    if (!sid) {
      sid = Math.random().toString(36).substring(2, 10);
      localStorage.setItem('chat_session_id', sid);
    }
    return sid;
  });

  const [allSessions, setAllSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);

  const fileInputRef = useRef(null);
  const chatBottomRef = useRef(null);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev));
    }, 4000);
  };

  // Cuộn xuống tin nhắn mới nhất
  const scrollToBottom = () => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isAsking]);

  // Lấy danh sách phiên trò chuyện
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/list_sessions/`);
      if (res.ok) {
        const data = await res.json();
        setAllSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Lỗi khi tải danh sách phiên:', err);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Tải lịch sử tin nhắn
  useEffect(() => {
    const sid = selectedSession || sessionId;
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_BASE}/history/${sid}`);
        if (res.ok) {
          const data = await res.json();
          setChatHistory(data.history || []);
        }
      } catch (err) {
        console.error('Lỗi khi tải lịch sử chat:', err);
      }
    };
    fetchHistory();
  }, [sessionId, selectedSession]);

  // Upload PDF
  const handleUpload = async (e) => {
    e.preventDefault();
    const file = fileInputRef.current?.files[0];
    if (!file) return;

    setUploading(true);
    setUploadSuccess(false);
    setPdfName(file.name);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload_pdf/`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        setUploadSuccess(true);
        setChatHistory([]);
        const newSid = Math.random().toString(36).substring(2, 10);
        setSessionId(newSid);
        localStorage.setItem('chat_session_id', newSid);
        setSelectedSession(null);
        setActiveSessionName('');
        await fetchSessions();
        showToast('success', `Tệp PDF [${file.name}] đã được phân tích và sẵn sàng truy vấn.`);
      } else {
        const errorData = await res.json().catch(() => ({}));
        setUploadSuccess(false);
        showToast('error', errorData.error || 'Quá trình xử lý tệp PDF thất bại.');
      }
    } catch (err) {
      console.error(err);
      setUploadSuccess(false);
      showToast('error', 'Không thể kết nối đến máy chủ backend khi tải PDF.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Lưu lịch sử
  const saveHistory = async (sid, history, sessionName, callback) => {
    setSavingHistory(true);
    try {
      await fetch(`${API_BASE}/save_history/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, history, session_name: sessionName }),
      });
      if (typeof callback === 'function') callback();
    } catch (err) {
      console.error('Lỗi khi lưu lịch sử:', err);
    } finally {
      setSavingHistory(false);
    }
  };

  // Gửi câu hỏi
  const handleAsk = async (e) => {
    e.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || isAsking) return;

    setQuestion('');
    setIsAsking(true);

    const updatedHistory = [...chatHistory, { role: 'user', content: cleanQuestion }];
    setChatHistory(updatedHistory);

    // Tự động lưu tên cuộc trò chuyện là 20 ký tự đầu tiên của câu hỏi ([Bạn]) đầu tiên
    let sessionTitle = activeSessionName;
    if (!sessionTitle) {
      sessionTitle = cleanQuestion.length > 20 ? cleanQuestion.slice(0, 20) + '...' : cleanQuestion;
      setActiveSessionName(sessionTitle);
    }

    try {
      const formData = new FormData();
      formData.append('question', cleanQuestion);

      const res = await fetch(`${API_BASE}/ask/`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        const finalHistory = [...updatedHistory, { role: 'assistant', content: data.answer }];
        setChatHistory(finalHistory);
        saveHistory(sessionId, finalHistory, sessionTitle, () => {
          fetchSessions();
        });
      } else {
        const errorMsg = data.error || 'Máy chủ không thể tạo câu trả lời.';
        const finalHistory = [...updatedHistory, { role: 'assistant', content: `[Thông báo lỗi]: ${errorMsg}` }];
        setChatHistory(finalHistory);
        saveHistory(sessionId, finalHistory, sessionTitle, () => {
          fetchSessions();
        });
        showToast('error', errorMsg);
      }
    } catch (err) {
      console.error(err);
      const networkErrorMsg = 'Mất kết nối với máy chủ backend. Vui lòng kiểm tra lại dịch vụ.';
      const finalHistory = [...updatedHistory, { role: 'assistant', content: `[Lỗi mạng]: ${networkErrorMsg}` }];
      setChatHistory(finalHistory);
      saveHistory(sessionId, finalHistory, sessionTitle, () => {
        fetchSessions();
      });
      showToast('error', networkErrorMsg);
    } finally {
      setIsAsking(false);
    }
  };

  // Mở cuộc trò chuyện mới trực tiếp (bỏ modal lưu)
  const handleInitiateNewChat = () => {
    const newSid = Math.random().toString(36).substring(2, 10);
    setSessionId(newSid);
    localStorage.setItem('chat_session_id', newSid);
    setSelectedSession(null);
    setActiveSessionName('');
    setChatHistory([]);
    setPdfName('');
    setUploadSuccess(false);
    setIsSidebarOpen(false);
    showToast('info', 'Đã mở cuộc trò chuyện mới.');
  };

  // Xoá phiên chat
  const executeDeleteSession = async (sid) => {
    try {
      const res = await fetch(`${API_BASE}/history/${sid}`, { method: 'DELETE' });
      if (res.ok) {
        setAllSessions((prev) => prev.filter((s) => s.id !== sid));
        if ((selectedSession || sessionId) === sid) {
          setSelectedSession(null);
          setChatHistory([]);
        }
        showToast('info', 'Đã xoá phiên hội thoại.');
      } else {
        showToast('error', 'Không thể xoá phiên hội thoại.');
      }
    } catch (err) {
      console.error(err);
      showToast('error', 'Lỗi kết nối khi gửi yêu cầu xoá.');
    } finally {
      setSessionToDelete(null);
    }
  };

  const isCurrentViewingSession = !selectedSession || selectedSession === sessionId;

  return (
    <div className="app-layout">
      {/* Toast thông báo */}
      {toast && (
        <aside className={`toast-banner toast-${toast.type}`} role="status" aria-live="polite">
          <span className="toast-tag">
            {toast.type === 'success' ? '[Thành công]' : toast.type === 'error' ? '[Lỗi]' : '[Thông báo]'}
          </span>
          <span className="toast-text">{toast.message}</span>
          <button className="toast-close" onClick={() => setToast(null)} title="Đóng">
            Đóng
          </button>
        </aside>
      )}

      {/* Lớp mờ nền cho Mobile Drawer */}
      {isSidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar - Danh sách hội thoại & Tài liệu */}
      <aside className={`app-sidebar ${isSidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-section">
            <img src={logoLkv} alt="VKLV Logo" className="brand-logo" />
            <div className="brand-text">
              <h1 className="brand-title">VKLV</h1>
            </div>
          </div>
          <button
            type="button"
            className="mobile-close-btn"
            onClick={() => setIsSidebarOpen(false)}
            aria-label="Đóng danh sách"
          >
            Đóng
          </button>
        </div>

        <div className="sidebar-actions">
          <button
            type="button"
            className="action-btn primary-btn"
            onClick={handleInitiateNewChat}
          >
            + Đoạn chat mới
          </button>
        </div>

        <div className="sidebar-history-section">
          <div className="section-label">Lịch sử hội thoại</div>
          <ul className="session-list">
            <li
              className={`session-item ${isCurrentViewingSession ? 'session-item-active' : ''}`}
              onClick={() => {
                setSelectedSession(null);
                setIsSidebarOpen(false);
              }}
            >
              <span className="session-name">{activeSessionName || 'Đoạn chat mới'}</span>
              <span className="session-status-dot" title="Hiện hành" aria-label="Hiện hành" />
            </li>

            {allSessions.map((session) => {
              const isSelected = selectedSession === session.id;
              const displayName = session.name && session.name.trim() ? session.name : session.id;
              return (
                <li
                  key={session.id}
                  className={`session-item ${isSelected ? 'session-item-active' : ''}`}
                  onClick={() => {
                    setSelectedSession(session.id);
                    setIsSidebarOpen(false);
                  }}
                >
                  <span className="session-name" title={displayName}>
                    {displayName}
                  </span>
                  {session.id !== sessionId && (
                    <button
                      type="button"
                      className="delete-session-btn"
                      title="Xoá hội thoại"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSessionToDelete(session);
                      }}
                    >
                      Xoá
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        <div className="sidebar-footer">
          <div className="doc-status-panel">
            <div className="doc-status-header">
              <span className="doc-status-label">Tài liệu kích hoạt:</span>
              <span className={`doc-badge ${uploadSuccess ? 'badge-active' : 'badge-inactive'}`}>
                {uploadSuccess ? 'Đã nạp' : 'Chưa nạp'}
              </span>
            </div>
            <div className="doc-name-display" title={pdfName || 'Chưa tải lên tệp PDF'}>
              {pdfName ? pdfName : 'Chưa chọn tệp'}
            </div>
          </div>
        </div>
      </aside>

      {/* Vùng nội dung chính */}
      <div className="app-main-area">
        {/* Top Navbar */}
        <header className="app-navbar">
          <div className="navbar-left">
            <button
              type="button"
              className="sidebar-toggle-btn"
              onClick={() => setIsSidebarOpen(true)}
            >
              Danh sách hội thoại
            </button>
            <div className="navbar-brand-badge">
              <img src={logoLkv} alt="VKLV Logo" className="navbar-logo" />
            </div>
            <div className="navbar-session-info">
              <span className="session-current-title">
                {selectedSession
                  ? allSessions.find((s) => s.id === selectedSession)?.name || selectedSession
                  : activeSessionName || 'Đoạn chat mới'}
              </span>
              {!isCurrentViewingSession && (
                <button
                  type="button"
                  className="return-current-btn"
                  onClick={() => setSelectedSession(null)}
                >
                  Trở về phiên hiện tại
                </button>
              )}
            </div>
          </div>

          <div className="navbar-right">
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
              aria-label={theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
            >
              {theme === 'dark' ? (
                <svg className="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5"></circle>
                  <line x1="12" y1="1" x2="12" y2="3"></line>
                  <line x1="12" y1="21" x2="12" y2="23"></line>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                  <line x1="1" y1="12" x2="3" y2="12"></line>
                  <line x1="21" y1="12" x2="23" y2="12"></line>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
              ) : (
                <svg className="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
              )}
            </button>

            <input
              type="file"
              accept="application/pdf"
              ref={fileInputRef}
              id="pdf-upload-input"
              className="hidden-file-input"
              onChange={() => {
                if (fileInputRef.current?.files?.[0]) {
                  handleUpload({ preventDefault: () => {} });
                }
              }}
            />
            <label htmlFor="pdf-upload-input" className="upload-label">
              <button
                type="button"
                className={`upload-trigger-btn ${uploading ? 'btn-loading' : ''}`}
                disabled={uploading}
                onClick={() => fileInputRef.current?.click()}
              >
                {uploading ? 'Đang phân tích...' : 'Tải lên PDF'}
              </button>
            </label>
          </div>
        </header>

        {/* Khung chat */}
        <main className="chat-viewport">
          <div className="chat-stream">
            {chatHistory.length === 0 && (
              <div className="empty-state-card">
                <div className="empty-state-logo-wrapper">
                  <img src={logoLkv} alt="VKLV Logo" className="empty-state-logo" />
                </div>
                <div className="empty-state-tag">[Hướng dẫn bắt đầu]</div>
                <h2 className="empty-state-title">Hỏi đáp tài liệu với VKLV</h2>
                <div className="empty-state-steps">
                  <div className="step-card">
                    <span className="step-number">Bước 1</span>
                    <p className="step-text">Bấm nút "Tải lên PDF" ở góc phải để nạp tài liệu cần tra cứu.</p>
                  </div>
                  <div className="step-card">
                    <span className="step-number">Bước 2</span>
                    <p className="step-text">Đặt câu hỏi vào khung bên dưới để nhận câu trả lời đối soát trực tiếp từ nội dung văn bản.</p>
                  </div>
                  <div className="step-card">
                    <span className="step-number">Bước 3</span>
                    <p className="step-text">Bấm "+ Đoạn chat mới" để lưu trữ phiên và bắt đầu tài liệu hoặc chủ đề khác.</p>
                  </div>
                </div>
              </div>
            )}

            {chatHistory.map((msg, index) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={index}
                  className={`message-row ${isUser ? 'row-user' : 'row-assistant'}`}
                >
                  {!isUser && (
                    <div className="message-avatar" aria-hidden="true">
                      <img src={logoLkv} alt="VKLV Avatar" className="assistant-avatar-img" />
                    </div>
                  )}
                  <div className="message-bubble">
                    <div className="message-header">
                      <span className={`role-label ${isUser ? 'role-user' : 'role-assistant'}`}>
                        {isUser ? '[Bạn]' : '[VKLV]'}
                      </span>
                    </div>
                    <div className="message-body">{msg.content}</div>
                  </div>
                </div>
              );
            })}

            {isAsking && (
              <div className="message-row row-assistant">
                <div className="message-avatar" aria-hidden="true">
                  <img src={logoLkv} alt="VKLV Avatar" className="assistant-avatar-img avatar-pulsing" />
                </div>
                <div className="message-bubble thinking-bubble">
                  <span className="role-label role-assistant">[VKLV]</span>
                  <div className="thinking-text">Đang đối soát tài liệu và tổng hợp câu trả lời...</div>
                </div>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* Ô nhập câu hỏi */}
          <footer className="chat-input-area">
            {isCurrentViewingSession ? (
              <form onSubmit={handleAsk} className="input-form">
                <input
                  type="text"
                  className="chat-text-input"
                  placeholder={
                    uploadSuccess
                      ? 'Nhập câu hỏi dựa trên nội dung tài liệu...'
                      : 'Hãy tải tài liệu PDF trước khi đặt câu hỏi...'
                  }
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={!uploadSuccess || isAsking}
                />
                <button
                  type="submit"
                  className={`submit-send-btn ${isAsking ? 'btn-loading' : ''}`}
                  disabled={!uploadSuccess || !question.trim() || isAsking}
                  title={isAsking ? 'Đang phân tích...' : 'Gửi câu hỏi'}
                  aria-label="Gửi câu hỏi"
                >
                  {isAsking ? (
                    <svg className="send-icon spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="12"></circle>
                    </svg>
                  ) : (
                    <svg className="send-icon" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                  )}
                </button>
              </form>
            ) : (
              <div className="readonly-banner">
                <span>Bạn đang xem lại lịch sử phiên đã lưu.</span>
                <button
                  type="button"
                  className="return-btn-small"
                  onClick={() => setSelectedSession(null)}
                >
                  Chuyển sang phiên hiện tại để tiếp tục chat
                </button>
              </div>
            )}

            {savingHistory && (
              <div className="status-saving-hint">Đang đồng bộ dữ liệu phiên...</div>
            )}
          </footer>
        </main>
      </div>

      {/* Modal: Xác nhận xoá phiên chat */}
      {sessionToDelete && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3 className="modal-title">Xác nhận xoá hội thoại</h3>
            <p className="modal-desc">
              Bạn có chắc chắn muốn xoá vĩnh viễn đoạn chat:
              <strong style={{ display: 'block', marginTop: '6px', color: '#f8fafc' }}>
                {sessionToDelete.name || sessionToDelete.id}
              </strong>
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="modal-btn cancel-btn"
                onClick={() => setSessionToDelete(null)}
              >
                Huỷ bỏ
              </button>
              <button
                type="button"
                className="modal-btn danger-btn"
                onClick={() => executeDeleteSession(sessionToDelete.id)}
              >
                Xác nhận xoá
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
