import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

const STATUS_COLORS = {
  PENDING: 'var(--warning)',
  PAYMENT_PENDING: 'var(--warning)',
  CONFIRMED: 'var(--primary-light)',
  PROCESSING: 'var(--accent)',
  SHIPPED: 'var(--secondary)',
  DELIVERED: 'var(--success)',
  CANCELLED: 'var(--error)',
  PAYMENT_FAILED: 'var(--error)',
  REFUNDED: 'var(--error)',
};

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/orders')
      .then(res => setOrders(res.data || []))
      .catch(() => setError('Failed to load orders'))
      .finally(() => setLoading(false));
  }, []);

  const handleCancel = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    try {
      const res = await api.post(`/orders/${orderId}/cancel`, { reason: 'User requested cancellation' });
      setOrders(orders.map(o => o.id === orderId ? res.data : o));
    } catch (err) {
      alert(err.message || 'Failed to cancel order');
    }
  };

  if (loading) return <div className="container page-wrapper"><div className="spinner" /></div>;

  return (
    <div className="container page-wrapper">
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '32px' }}>Your Orders</h1>

      {error && <div className="alert alert-error" style={{ marginBottom: '24px' }}>⚠️ {error}</div>}

      {orders.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📦</div>
          <h2 style={{ marginBottom: '12px' }}>No orders found</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>You haven't placed any orders yet.</p>
          <Link to="/" className="btn btn-primary">Start Shopping</Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {orders.map(order => {
            const canCancel = ['PENDING', 'PAYMENT_PENDING', 'PAYMENT_FAILED'].includes(order.status);
            
            return (
              <div key={order.id} className="card" style={{ padding: '0', overflow: 'hidden' }}>
                
                {/* Header */}
                <div style={{
                  padding: '20px', background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-subtle)',
                  display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'space-between', alignItems: 'center'
                }}>
                  <div style={{ display: 'flex', gap: '32px' }}>
                    <div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Order Placed</div>
                      <div style={{ fontSize: '14px', fontWeight: 500 }}>{new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Total Amount</div>
                      <div style={{ fontSize: '14px', fontWeight: 500 }}>₹{Number(order.total_amount).toLocaleString('en-IN')}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Order ID</div>
                      <div style={{ fontSize: '14px', fontWeight: 500 }}>#{order.id}</div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: '6px',
                      padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 700,
                      background: 'var(--bg-card)', border: `1px solid ${STATUS_COLORS[order.status] || 'var(--text-muted)'}`,
                      color: STATUS_COLORS[order.status] || 'var(--text-muted)'
                    }}>
                      {order.status.replace('_', ' ')}
                    </div>
                    {canCancel && (
                      <button onClick={() => handleCancel(order.id)} className="btn btn-outline btn-sm" style={{ color: 'var(--error)', borderColor: 'var(--error)' }}>
                        Cancel Order
                      </button>
                    )}
                  </div>
                </div>

                {/* Body (Items) */}
                <div style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {order.items.map(item => (
                      <div key={item.product_id} style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <Link to={`/products/${item.product_id}`} style={{ width: '80px', height: '80px', borderRadius: '8px', overflow: 'hidden', background: 'var(--bg-elevated)', position: 'relative' }}>
                          {item.image_url ? (
                            <img src={item.image_url} alt={item.product_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          ) : (
                            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', opacity: 0.2 }}>🛍️</div>
                          )}
                        </Link>
                        <div style={{ flex: 1 }}>
                          <Link to={`/products/${item.product_id}`} style={{ fontWeight: 600, fontSize: '15px' }}>{item.product_name}</Link>
                          <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                            Qty: {item.quantity} × ₹{Number(item.price).toLocaleString('en-IN')}
                          </div>
                        </div>
                        <div style={{ fontWeight: 700, fontSize: '15px' }}>
                          ₹{Number(item.subtotal).toLocaleString('en-IN')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
