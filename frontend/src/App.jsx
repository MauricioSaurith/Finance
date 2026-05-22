import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { RefreshCcw, Send } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const INITIAL_MESSAGE = {
  role: 'agent',
  content: 'Hola. Soy tu agente financiero inteligente. En que mercado o accion te gustaria profundizar hoy?',
  trace: [],
};

function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showNewsType, setShowNewsType] = useState(null);
  const [newsData, setNewsData] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const fetchNews = useCallback(async (type) => {
    setNewsLoading(true);
    setNewsData([]);
    try {
      const res = await axios.get(`${API_URL}/${type}`);
      if (type === 'nyt') setNewsData(res.data.news);
      if (type === 'tweets') setNewsData(res.data.tweets);
    } catch (err) {
      console.error(err);
      setNewsData([{ title: 'Error', summary: 'No se pudo cargar la informacion.', analysis: '' }]);
    } finally {
      setNewsLoading(false);
    }
  }, []);

  const handleNewsToggle = (type) => {
    const nextType = showNewsType === type ? null : type;
    setShowNewsType(nextType);

    if (nextType) {
      fetchNews(nextType);
    }
  };

  const handleNewSession = async () => {
    const previousSessionId = sessionId;

    setMessages([INITIAL_MESSAGE]);
    setSessionId(null);
    setInput('');
    setShowNewsType(null);
    setNewsData([]);

    if (!previousSessionId) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/chat/${previousSessionId}`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || loading) return;

    const userMsg = { role: 'user', content: trimmedInput, trace: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, {
        message: trimmedInput,
        session_id: sessionId,
      });

      if (res.data.session_id) {
        setSessionId(res.data.session_id);
      }

      const agentMsg = {
        role: 'agent',
        content: res.data.response,
        trace: res.data.trace || [],
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail || err.message;
      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          content: `Lo siento, tuve un problema procesando la solicitud. Detalle: ${detail}`,
          trace: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-title">
          <h1>Finance Agent</h1>
        </div>

        <div className="sidebar-section">
          <h3>Evaluacion</h3>
          <button className="sidebar-btn reset-btn" onClick={handleNewSession}>
            <RefreshCcw size={14} />
            Nueva sesion limpia
          </button>
          <p className="sidebar-note">
            Reinicia la memoria para probar consistencia, alucinaciones y uso de tools.
          </p>
        </div>

        <div className="sidebar-section">
          <h3>Fuentes de datos</h3>
          <button
            className={`sidebar-btn ${showNewsType === 'nyt' ? 'active' : ''}`}
            onClick={() => handleNewsToggle('nyt')}
          >
            New York Times
          </button>
          <button
            className={`sidebar-btn ${showNewsType === 'tweets' ? 'active' : ''}`}
            onClick={() => handleNewsToggle('tweets')}
          >
            Tendencias (Tweets)
          </button>
        </div>
      </aside>

      <main className="chat-area">
        <header className="chat-header">
          <h2>Analisis en tiempo real</h2>
          <span className="session-status">
            {sessionId ? 'Sesion aislada activa' : 'Sesion nueva'}
          </span>
        </header>

        {showNewsType ? (
          <div className="news-panel">
            <h2>{showNewsType === 'nyt' ? 'New York Times - Business' : 'Tendencias Financieras'}</h2>
            {newsLoading ? (
              <div className="message agent">Cargando y analizando datos en tiempo real...</div>
            ) : (
              <div className="news-list">
                {newsData.map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="news-card"
                  >
                    {showNewsType === 'nyt' ? (
                      <>
                        <h3>{item.title}</h3>
                        <p>{item.summary}</p>
                        <a href={item.link} target="_blank" rel="noreferrer">Leer articulo original</a>
                      </>
                    ) : (
                      <>
                        <h3>{item.user}</h3>
                        <p>{item.text}</p>
                      </>
                    )}
                    <div className="news-analysis">
                      <strong>Analisis del LLM:</strong> {item.analysis}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="chat-messages">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`message ${msg.role}`}
                >
                  <div className="message-content">{msg.content}</div>
                  {msg.role === 'agent' && msg.trace?.length > 0 && (
                    <details className="message-trace">
                      <summary>Ver tools y fuentes usadas</summary>
                      <div className="trace-list">
                        {msg.trace.map((step, index) => (
                          <div key={`${step.tool}-${index}`} className="trace-item">
                            <div className="trace-tool">{step.tool}</div>
                            <div className="trace-input">
                              Input: {typeof step.input === 'string' ? step.input : JSON.stringify(step.input)}
                            </div>
                            <div className="trace-observation">{step.observation}</div>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <motion.div
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="message agent"
              >
                Analizando mercados...
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        <div className="input-container">
          <form className="input-wrapper" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Preguntame sobre Apple (AAPL), Bitcoin o noticias de Nvidia..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="send-btn" disabled={loading}>
              <Send size={20} color="#000" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;
