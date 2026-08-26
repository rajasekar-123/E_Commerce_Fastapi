import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Register() {
  const { login } = useAuth();
  const { fetchCart } = useCart();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: '', password: '', first_name: '', last_name: '', phone: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/register', form, { auth: false });
      // Auto login
      const res = await api.post('/auth/login', { email: form.email, password: form.password }, { auth: false });
      login(res.data);
      await fetchCart();
      navigate('/');
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: 'calc(100vh - 72px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '32px 16px',
    }}>
      <div className="fade-in" style={{ width: '100%', maxWidth: '460px' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <div style={{
            width: '64px', height: '64px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            borderRadius: '20px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '28px', margin: '0 auto 20px',
            boxShadow: '0 8px 24px rgba(99,102,241,0.3)',
          }}>✨</div>
          <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>Create Account</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
            Join E-Shop and start shopping
          </p>
        </div>

        <div className="card" style={{ padding: '32px' }}>

          {error && <div className="alert alert-error" style={{ marginBottom: '20px' }}>⚠️ {error}</div>}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">First Name *</label>
                <input className="form-input" type="text" name="first_name" value={form.first_name}
                  onChange={handleChange} placeholder="John" required />
              </div>
              <div className="form-group">
                <label className="form-label">Last Name *</label>
                <input className="form-input" type="text" name="last_name" value={form.last_name}
                  onChange={handleChange} placeholder="Doe" required />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Email Address *</label>
              <input className="form-input" type="email" name="email" value={form.email}
                onChange={handleChange} placeholder="you@example.com" required />
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input className="form-input" type="tel" name="phone" value={form.phone}
                onChange={handleChange} placeholder="+91 98765 43210" />
            </div>

            <div className="form-group">
              <label className="form-label">Password *</label>
              <input className="form-input" type="password" name="password" value={form.password}
                onChange={handleChange} placeholder="Minimum 8 characters" required />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-lg btn-full" style={{ marginTop: '4px' }}>
              {loading ? (
                <><div className="spinner" style={{ width: '16px', height: '16px' }} /> Creating account...</>
              ) : 'Create Account →'}
            </button>
          </form>

          <div style={{ marginTop: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--primary-light)', fontWeight: 600 }}>Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
