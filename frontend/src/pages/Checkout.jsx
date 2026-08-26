import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import api from '../services/api';

export default function Checkout() {
  const { cart, fetchCart } = useCart();
  const navigate = useNavigate();
  const [addresses, setAddresses] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  // New Address Form
  const [showNewForm, setShowNewForm] = useState(false);
  const [newAddress, setNewAddress] = useState({
    title: 'Home', address_line1: '', address_line2: '', city: '', state: '', postal_code: '', country: 'India'
  });

  useEffect(() => {
    if (!cart.items || cart.items.length === 0) {
      navigate('/cart');
      return;
    }
    
    api.get('/users/addresses')
      .then(res => {
        setAddresses(res.data);
        if (res.data.length > 0) setSelectedAddress(res.data[0].id);
        else setShowNewForm(true);
      })
      .catch(() => setError('Failed to load addresses'))
      .finally(() => setLoading(false));
  }, [cart, navigate]);

  const handleAddressSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/users/addresses', newAddress);
      setAddresses([...addresses, res.data]);
      setSelectedAddress(res.data.id);
      setShowNewForm(false);
    } catch (err) {
      setError(err.message || 'Failed to save address');
    }
  };

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleRazorpayCheckout = async () => {
    if (!selectedAddress) {
      setError('Please select a delivery address');
      return;
    }
    
    setProcessing(true);
    setError('');
    try {
      const res = await loadRazorpayScript();
      if (!res) {
        throw new Error('Razorpay SDK failed to load. Are you online?');
      }

      // 1. Create Order
      const items = cart.items.map(i => ({ product_id: i.product_id, quantity: i.quantity }));
      const orderRes = await api.post('/orders', { address_id: selectedAddress, items });
      const orderId = orderRes.data.id;

      // 2. Clear Cart (since order was created)
      await api.delete('/cart');
      await fetchCart();

      // 3. Create Razorpay Order
      const rzpOrderRes = await api.post('/payments/create-order', { order_id: orderId });
      
      // 4. Initialize Razorpay Modal
      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID,
        amount: rzpOrderRes.data.amount,
        currency: rzpOrderRes.data.currency,
        name: 'E-Commerce Store',
        description: 'Order Payment',
        order_id: rzpOrderRes.data.id,
        handler: async function (response) {
          try {
            const verifyRes = await api.post('/payments/verify-payment', {
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature,
              order_id: orderId,
            });
            if (verifyRes.data.status === 'success') {
              window.location.href = `/payment/success?session_id=${orderId}`;
            }
          } catch (err) {
            setError(err.response?.data?.detail || 'Payment verification failed');
          }
        },
        theme: {
          color: '#4f46e5'
        }
      };

      const paymentObject = new window.Razorpay(options);
      paymentObject.on('payment.failed', function (response){
        setError(response.error.description);
      });
      paymentObject.open();

    } catch (err) {
      setError(err.message || 'Checkout failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const handleCheckout = async () => {
    if (!selectedAddress) {
      setError('Please select a delivery address');
      return;
    }
    
    setProcessing(true);
    setError('');
    try {
      // 1. Create Order
      const items = cart.items.map(i => ({ product_id: i.product_id, quantity: i.quantity }));
      const orderRes = await api.post('/orders', { address_id: selectedAddress, items });
      const orderId = orderRes.data.id;

      // 2. Clear Cart (since order was created)
      await api.delete('/cart');
      await fetchCart();

      // 3. Create Stripe Checkout Session
      const checkoutRes = await api.post('/payments/checkout', { order_id: orderId });
      
      // 4. Redirect to Stripe
      window.location.href = checkoutRes.data.checkout_url;
      
    } catch (err) {
      setError(err.message || 'Checkout failed. Please try again.');
      setProcessing(false);
    }
  };

  if (loading) return <div className="container page-wrapper"><div className="spinner" /></div>;

  const total = Number(cart.subtotal) + (Number(cart.subtotal) >= 999 ? 0 : 49); // Simple local calc for display

  return (
    <div className="container page-wrapper">
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '32px' }}>Checkout</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '32px', alignItems: 'start' }}>
        
        {/* Left: Address Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {error && <div className="alert alert-error">⚠️ {error}</div>}

          <div className="card">
            <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '20px' }}>Delivery Address</h2>
            
            {addresses.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
                {addresses.map(addr => (
                  <label key={addr.id} style={{
                    display: 'flex', gap: '12px', padding: '16px',
                    border: `1.5px solid ${selectedAddress === addr.id ? 'var(--primary)' : 'var(--border-subtle)'}`,
                    borderRadius: '12px', background: selectedAddress === addr.id ? 'rgba(99,102,241,0.05)' : 'var(--bg-elevated)',
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}>
                    <input
                      type="radio"
                      name="address"
                      value={addr.id}
                      checked={selectedAddress === addr.id}
                      onChange={() => setSelectedAddress(addr.id)}
                      style={{ marginTop: '4px' }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, marginBottom: '4px' }}>{addr.title}</div>
                      <div style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {addr.address_line1}, {addr.address_line2 && `${addr.address_line2}, `}
                        {addr.city}, {addr.state} {addr.postal_code}<br/>
                        {addr.country}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}

            {!showNewForm ? (
              <button onClick={() => setShowNewForm(true)} className="btn btn-outline btn-sm">
                + Add New Address
              </button>
            ) : (
              <form onSubmit={handleAddressSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px', background: 'var(--bg-elevated)', padding: '20px', borderRadius: '12px', border: '1px dashed var(--border)' }}>
                <div className="form-group">
                  <label className="form-label">Address Title (e.g., Home, Work)</label>
                  <input className="form-input" required value={newAddress.title} onChange={e => setNewAddress({...newAddress, title: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Address Line 1</label>
                  <input className="form-input" required value={newAddress.address_line1} onChange={e => setNewAddress({...newAddress, address_line1: e.target.value})} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">City</label>
                    <input className="form-input" required value={newAddress.city} onChange={e => setNewAddress({...newAddress, city: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">State</label>
                    <input className="form-input" required value={newAddress.state} onChange={e => setNewAddress({...newAddress, state: e.target.value})} />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Postal Code</label>
                    <input className="form-input" required value={newAddress.postal_code} onChange={e => setNewAddress({...newAddress, postal_code: e.target.value})} />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                  <button type="submit" className="btn btn-primary btn-sm">Save Address</button>
                  {addresses.length > 0 && (
                    <button type="button" onClick={() => setShowNewForm(false)} className="btn btn-ghost btn-sm">Cancel</button>
                  )}
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Right: Order Summary */}
        <div className="card" style={{ position: 'sticky', top: '100px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '20px' }}>Order Details</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px', maxHeight: '300px', overflowY: 'auto', paddingRight: '8px' }}>
            {cart.items.map(item => (
              <div key={item.id} style={{ display: 'flex', gap: '12px', fontSize: '14px' }}>
                <div style={{ position: 'relative' }}>
                  {item.product_image ? (
                    <img src={item.product_image} alt="" style={{ width: '48px', height: '48px', borderRadius: '8px', objectFit: 'cover' }} />
                  ) : (
                    <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: 'var(--bg-elevated)' }} />
                  )}
                  <span style={{ position: 'absolute', top: '-6px', right: '-6px', background: 'var(--primary)', color: 'white', fontSize: '10px', fontWeight: 700, width: '18px', height: '18px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {item.quantity}
                  </span>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{item.product_name}</div>
                  <div style={{ color: 'var(--text-muted)' }}>₹{Number(item.unit_price).toLocaleString('en-IN')}</div>
                </div>
                <div style={{ fontWeight: 700 }}>₹{Number(item.subtotal).toLocaleString('en-IN')}</div>
              </div>
            ))}
          </div>
          
          <div className="divider" />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Subtotal</span>
              <span>₹{Number(cart.subtotal).toLocaleString('en-IN')}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Shipping</span>
              <span>{Number(cart.subtotal) >= 999 ? <span style={{ color: 'var(--success)' }}>Free</span> : '₹49.00'}</span>
            </div>
            
            <div className="divider" />
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '20px', fontWeight: 800 }}>
              <span>Total</span>
              <span>₹{total.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '24px' }}>
            <button onClick={handleCheckout} disabled={processing || (!selectedAddress && !showNewForm)} className="btn btn-primary btn-full btn-lg">
              {processing ? <div className="spinner" style={{ width: '16px', height: '16px' }} /> : 'Pay with Stripe 💳'}
            </button>
            <button onClick={handleRazorpayCheckout} disabled={processing || (!selectedAddress && !showNewForm)} className="btn btn-outline btn-full btn-lg">
              {processing ? <div className="spinner" style={{ width: '16px', height: '16px' }} /> : 'Pay with Razorpay ⚡'}
            </button>
          </div>
          
          <div style={{ textAlign: 'center', marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
            Secure checkout powered by Stripe
          </div>
        </div>
      </div>
    </div>
  );
}
