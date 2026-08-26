/**
 * Floating AI Chat Button — accessible from all pages.
 *
 * Shows a pulsing robot button in the bottom-right corner.
 * Opens the /ai-chat page on click.
 */

import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function AIChatButton() {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState(false);

  return (
    <button
      id="ai-chat-button"
      onClick={() => navigate('/ai-chat')}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      title="Chat with AI Shopping Assistant"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 1000,
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        border: 'none',
        cursor: 'pointer',
        background: hovered
          ? 'linear-gradient(135deg, #4f46e5, #7c3aed)'
          : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        color: 'white',
        fontSize: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: hovered
          ? '0 8px 30px rgba(99, 102, 241, 0.6)'
          : '0 4px 20px rgba(99, 102, 241, 0.4)',
        transform: hovered ? 'scale(1.1)' : 'scale(1)',
        transition: 'all 0.2s ease',
        animation: 'pulse-ring 2s infinite',
      }}
    >
      🤖
      <style>{`
        @keyframes pulse-ring {
          0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
          70% { box-shadow: 0 0 0 12px rgba(99, 102, 241, 0); }
          100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
        }
      `}</style>
    </button>
  );
}
