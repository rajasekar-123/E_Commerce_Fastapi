import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Navbar() {
  const { auth, logout, isAdmin, isAuthenticated } = useAuth();
  const { cart } = useCart();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const itemCount = cart?.item_count || 0;

  return (
    <nav style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: 'rgba(15, 15, 26, 0.85)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(99, 102, 241, 0.12)',
      height: '72px',
    }}>
      <div className="container" style={{ height: '100%', display: 'flex', alignItems: 'center', gap: '24px' }}>

        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <div style={{
            width: '36px', height: '36px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            borderRadius: '10px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '18px',
          }}>🛍️</div>
          <span style={{ fontWeight: 800, fontSize: '18px', letterSpacing: '-0.02em' }}>
            <span className="gradient-text">E-Shop</span>
          </span>
        </Link>

        {/* Search */}
        <form onSubmit={handleSearch} style={{ flex: 1, maxWidth: '480px' }}>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)',
              color: 'var(--text-muted)', fontSize: '16px',
            }}>🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search products, brands..."
              style={{
                width: '100%',
                padding: '10px 16px 10px 42px',
                background: 'var(--bg-elevated)',
                border: '1.5px solid var(--border-subtle)',
                borderRadius: '12px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = 'var(--primary)'}
              onBlur={e => e.target.style.borderColor = 'var(--border-subtle)'}
            />
          </div>
        </form>

        {/* Nav Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>

          {isAdmin && (
            <Link to="/admin" className="btn btn-ghost btn-sm">
              ⚙️ Admin
            </Link>
          )}

          {isAuthenticated ? (
            <>
              {/* Cart */}
              <Link to="/cart" className="btn btn-ghost btn-icon" style={{ position: 'relative' }}>
                <span style={{ fontSize: '20px' }}>🛒</span>
                {itemCount > 0 && (
                  <span style={{
                    position: 'absolute', top: '2px', right: '2px',
                    width: '18px', height: '18px',
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    borderRadius: '50%',
                    fontSize: '10px', fontWeight: 700,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white',
                  }}>{itemCount > 9 ? '9+' : itemCount}</span>
                )}
              </Link>

              {/* Orders */}
              <Link to="/orders" className="btn btn-ghost btn-sm">
                📦 Orders
              </Link>

              {/* AI Chat */}
              <Link to="/ai-chat" className="btn btn-ghost btn-sm">
                🤖 AI
              </Link>

              {/* User Menu */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setMenuOpen(!menuOpen)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    padding: '8px 12px',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '10px',
                    color: 'var(--text-primary)',
                    fontSize: '14px', fontWeight: 500,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{
                    width: '28px', height: '28px',
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '12px', fontWeight: 700, color: 'white',
                  }}>
                    {(auth?.first_name?.[0] || auth?.email?.[0] || 'U').toUpperCase()}
                  </div>
                  <span style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {auth?.first_name || auth?.email}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{menuOpen ? '▲' : '▼'}</span>
                </button>

                {menuOpen && (
                  <div style={{
                    position: 'absolute', right: 0, top: 'calc(100% + 8px)',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: '12px',
                    minWidth: '160px',
                    boxShadow: 'var(--shadow-lg)',
                    overflow: 'hidden',
                    zIndex: 200,
                  }}>
                    <Link to="/profile" onClick={() => setMenuOpen(false)} style={{
                      display: 'flex', alignItems: 'center', gap: '10px',
                      padding: '12px 16px', color: 'var(--text-secondary)',
                      fontSize: '14px', transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.target.style.background = 'var(--bg-card)'}
                    onMouseLeave={e => e.target.style.background = 'transparent'}>
                      👤 Profile
                    </Link>
                    <div style={{ height: '1px', background: 'var(--border-subtle)' }} />
                    <button onClick={handleLogout} style={{
                      width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                      padding: '12px 16px', color: '#fca5a5',
                      fontSize: '14px', background: 'none', border: 'none',
                      cursor: 'pointer', transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.08)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                      🚪 Logout
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost btn-sm">Login</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Sign Up</Link>
            </>
          )}
        </div>

      </div>

      {/* Overlay to close menu */}
      {menuOpen && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 150,
        }} onClick={() => setMenuOpen(false)} />
      )}
    </nav>
  );
}
