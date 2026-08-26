import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { useState } from 'react';

export default function Cart() {
  const { cart, loading, updateItem, removeItem, fetchCart } = useCart();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  if (loading && !cart.items?.length) {
    return (
      <div className="container page-wrapper" style={{ display: 'flex', justifyContent: 'center', paddingTop: '100px' }}>
        <div className="spinner" style={{ width: '40px', height: '40px' }} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="container page-wrapper" style={{ textAlign: 'center', paddingTop: '80px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🛒</div>
        <h2 style={{ marginBottom: '16px' }}>Sign in to view your cart</h2>
        <Link to="/login" className="btn btn-primary">Sign In</Link>
      </div>
    );
  }

  if (!cart.items || cart.items.length === 0) {
    return (
      <div className="container page-wrapper" style={{ textAlign: 'center', paddingTop: '80px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🛒</div>
        <h2 style={{ marginBottom: '16px' }}>Your cart is empty</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Looks like you haven't added anything yet.</p>
        <Link to="/" className="btn btn-primary">Start Shopping</Link>
      </div>
    );
  }

  const handleCheckout = async () => {
    setCheckoutLoading(true);
    try {
      // First, create the order (assuming address 1 for demo purposes, in real app we'd have a checkout form)
      // Actually, let's redirect to a checkout page where they can select address.
      navigate('/checkout');
    } finally {
      setCheckoutLoading(false);
    }
  };

  return (
    <div className="container page-wrapper">
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '32px' }}>Shopping Cart</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '32px', alignItems: 'start' }}>
        {/* Left: Items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {cart.items.map(item => (
            <div key={item.id} className="card" style={{ display: 'flex', gap: '20px', padding: '20px', alignItems: 'center' }}>
              
              {/* Image */}
              <Link to={`/products/${item.product_id}`} style={{ width: '100px', height: '100px', flexShrink: 0, borderRadius: '12px', overflow: 'hidden', background: 'var(--bg-elevated)', position: 'relative' }}>
                {item.product_image ? (
                  <img src={item.product_image} alt={item.product_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px', opacity: 0.2 }}>🛍️</div>
                )}
              </Link>

              {/* Details */}
              <div style={{ flex: 1 }}>
                {item.product_brand && <div style={{ fontSize: '11px', color: 'var(--primary-light)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>{item.product_brand}</div>}
                <Link to={`/products/${item.product_id}`} style={{ fontSize: '16px', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
                  {item.product_name}
                </Link>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  ₹{Number(item.unit_price).toLocaleString('en-IN')}
                  {item.unit_price < item.original_price && (
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', textDecoration: 'line-through', marginLeft: '8px', fontWeight: 400 }}>
                      ₹{Number(item.original_price).toLocaleString('en-IN')}
                    </span>
                  )}
                </div>
                {!item.in_stock && <div style={{ color: 'var(--error)', fontSize: '12px', marginTop: '4px' }}>Out of Stock</div>}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0', border: '1.5px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
                  <button onClick={() => updateItem(item.id, Math.max(1, item.quantity - 1))}
                    style={{ padding: '6px 12px', background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>−</button>
                  <span style={{ padding: '6px 16px', fontWeight: 600, fontSize: '14px', minWidth: '40px', textAlign: 'center' }}>
                    {item.quantity}
                  </span>
                  <button onClick={() => updateItem(item.id, Math.min(item.available_stock, item.quantity + 1))}
                    style={{ padding: '6px 12px', background: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>+</button>
                </div>
                <button onClick={() => removeItem(item.id)} className="btn btn-ghost btn-sm" style={{ color: '#fca5a5' }}>
                  🗑️ Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Right: Summary */}
        <div className="card" style={{ position: 'sticky', top: '100px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '20px' }}>Order Summary</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Items ({cart.item_count})</span>
              <span>₹{Number(cart.subtotal + cart.total_discount).toLocaleString('en-IN')}</span>
            </div>
            
            {cart.total_discount > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--success)' }}>
                <span>Discount</span>
                <span>−₹{Number(cart.total_discount).toLocaleString('en-IN')}</span>
              </div>
            )}
            
            <div className="divider" />
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: 700 }}>
              <span>Subtotal</span>
              <span>₹{Number(cart.subtotal).toLocaleString('en-IN')}</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'right' }}>
              Taxes and shipping calculated at checkout
            </div>
          </div>

          <button onClick={handleCheckout} disabled={checkoutLoading || cart.items.some(i => !i.in_stock)} className="btn btn-primary btn-full btn-lg" style={{ marginTop: '24px' }}>
            {checkoutLoading ? <div className="spinner" style={{ width: '16px', height: '16px' }} /> : 'Proceed to Checkout →'}
          </button>
          
          {cart.items.some(i => !i.in_stock) && (
            <div style={{ color: 'var(--error)', fontSize: '12px', marginTop: '12px', textAlign: 'center' }}>
              Please remove out-of-stock items to continue.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
