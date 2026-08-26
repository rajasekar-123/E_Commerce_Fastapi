import { useState, useRef, useEffect } from 'react';
import api from '../services/api';

/**
 * AIChat — Shopping Assistant chat interface.
 *
 * Features:
 *   - Multi-turn conversation with session persistence (conversation_id)
 *   - Source citation display from RAG
 *   - Typing indicator while waiting for response
 *   - Message history displayed in chat bubble format
 */
export default function AIChat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Hi! I\'m your E-Shop shopping assistant. I can help you find products, check your order status, or answer questions about our store. What can I help you with?',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);

    // Optimistically add user message
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await api.post('/ai/chat', {
        message: userMessage,
        conversation_id: conversationId,
      });

      const { answer, sources, conversation_id } = response.data;

      setConversationId(conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: answer,
          sources: sources || [],
        },
      ]);
    } catch (err) {
      setError(err.message || 'Failed to get response. Please try again.');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '❌ Sorry, I encountered an error. Please try again.',
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 80px)',
      maxWidth: '900px',
      margin: '0 auto',
      padding: '24px 16px',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        borderRadius: '16px 16px 0 0',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <div style={{
          width: '40px', height: '40px',
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '20px',
        }}>🤖</div>
        <div>
          <h1 style={{ color: 'white', fontSize: '18px', fontWeight: 700, margin: 0 }}>
            E-Shop AI Assistant
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '13px', margin: 0 }}>
            Powered by RAG · Ask about products, orders, and more
          </p>
        </div>
        <div style={{
          marginLeft: 'auto',
          width: '10px', height: '10px',
          borderRadius: '50%',
          background: '#4ade80',
          boxShadow: '0 0 8px #4ade80',
        }} />
      </div>

      {/* Messages Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        background: '#f8fafc',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            gap: '10px',
            alignItems: 'flex-start',
          }}>
            {msg.role === 'assistant' && (
              <div style={{
                width: '32px', height: '32px', borderRadius: '50%', flexShrink: 0,
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '14px', color: 'white',
              }}>🤖</div>
            )}
            <div style={{
              maxWidth: '75%',
              padding: '12px 16px',
              borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              background: msg.role === 'user'
                ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                : msg.isError ? '#fef2f2' : 'white',
              color: msg.role === 'user' ? 'white' : msg.isError ? '#dc2626' : '#1e293b',
              boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              fontSize: '14px',
              lineHeight: '1.6',
            }}>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>

              {/* Source Citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div style={{
                  marginTop: '12px',
                  paddingTop: '10px',
                  borderTop: '1px solid #e2e8f0',
                }}>
                  <p style={{ fontSize: '11px', color: '#94a3b8', margin: '0 0 6px', fontWeight: 600 }}>
                    📚 Sources
                  </p>
                  {msg.sources.map((src, si) => (
                    <div key={si} style={{
                      fontSize: '11px', color: '#64748b',
                      padding: '4px 8px',
                      background: '#f1f5f9',
                      borderRadius: '6px',
                      marginBottom: '4px',
                    }}>
                      📄 {src.document}
                      {src.relevance_score && (
                        <span style={{ marginLeft: '8px', color: '#94a3b8' }}>
                          ({Math.round(src.relevance_score * 100)}% match)
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div style={{
                width: '32px', height: '32px', borderRadius: '50%', flexShrink: 0,
                background: '#e2e8f0',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '14px',
              }}>👤</div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '14px', color: 'white',
            }}>🤖</div>
            <div style={{
              padding: '12px 16px',
              background: 'white',
              borderRadius: '18px 18px 18px 4px',
              boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              display: 'flex', gap: '4px', alignItems: 'center',
            }}>
              {[0, 1, 2].map((i) => (
                <div key={i} style={{
                  width: '6px', height: '6px',
                  borderRadius: '50%',
                  background: '#6366f1',
                  animation: `bounce 1.2s infinite ${i * 0.2}s`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={sendMessage} style={{
        display: 'flex',
        gap: '12px',
        padding: '16px 24px',
        background: 'white',
        borderRadius: '0 0 16px 16px',
        borderTop: '1px solid #e2e8f0',
        boxShadow: '0 -2px 10px rgba(0,0,0,0.05)',
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about products, orders, or anything else..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: '12px',
            border: '2px solid #e2e8f0',
            fontSize: '14px',
            outline: 'none',
            transition: 'border-color 0.2s',
            fontFamily: 'inherit',
          }}
          onFocus={(e) => e.target.style.borderColor = '#6366f1'}
          onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            padding: '12px 20px',
            background: loading || !input.trim()
              ? '#e2e8f0'
              : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: loading || !input.trim() ? '#94a3b8' : 'white',
            border: 'none',
            borderRadius: '12px',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            fontWeight: 600,
            fontSize: '14px',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {loading ? '...' : '→ Send'}
        </button>
      </form>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}
