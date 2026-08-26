import { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';

export default function OrderSuccess() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const navigate = useNavigate();
  
  useEffect(() => {
    // If someone visits this page directly without a session_id, redirect to home
    if (!sessionId) {
      navigate('/');
    }
    // Note: Verification of the payment happens via webhook on the backend.
    // This page is just a "thank you" display.
  }, [sessionId, navigate]);

  if (!sessionId) return null;

  return (
    <div className="container page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <div className="card fade-in" style={{ textAlign: 'center', padding: '48px 32px', maxWidth: '500px', width: '100%' }}>
        <div style={{
          width: '80px', height: '80px',
          background: 'linear-gradient(135deg, var(--success), #059669)',
          borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '40px', margin: '0 auto 24px', color: 'white',
          boxShadow: '0 8px 24px rgba(16,185,129,0.3)'
        }}>
          ✓
        </div>
        
        <h1 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '16px' }}>Payment Successful!</h1>
        
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px', lineHeight: 1.6, marginBottom: '32px' }}>
          Thank you for your purchase. Your order has been placed and is being processed. 
          We'll send you an email confirmation shortly.
        </p>
        
        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
          <Link to="/orders" className="btn btn-primary">
            View Order Status
          </Link>
          <Link to="/" className="btn btn-outline">
            Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
}
