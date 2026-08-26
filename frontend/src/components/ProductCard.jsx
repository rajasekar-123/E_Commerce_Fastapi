import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

function StarRating({ rating, count }) {
  const stars = Math.round(rating || 0);
  return (
    <div className="star-rating">
      {[1,2,3,4,5].map(s => (
        <span key={s} className="star" style={{ opacity: s <= stars ? 1 : 0.2 }}>★</span>
      ))}
      {count !== undefined && (
        <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '4px' }}>({count})</span>
      )}
    </div>
  );
}

export default function ProductCard({ product }) {
  const { addItem } = useCart();
  const { isAuthenticated } = useAuth();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const effectivePrice = product.discount_price && product.discount_price < product.price
    ? product.discount_price
    : product.price;
  const hasDiscount = product.discount_price && product.discount_price < product.price;
  const discountPct = hasDiscount
    ? Math.round((1 - product.discount_price / product.price) * 100)
    : 0;

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) return;
    setAdding(true);
    try {
      await addItem(product.id, 1);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch {
      // Silently handle
    } finally {
      setAdding(false);
    }
  };

  return (
    <Link to={`/products/${product.id}`} style={{ display: 'block', textDecoration: 'none' }}>
      <div className="card card-hover" style={{ padding: 0, overflow: 'hidden', cursor: 'pointer' }}>

        {/* Product Image */}
        <div style={{
          position: 'relative',
          paddingBottom: '70%',
          background: 'linear-gradient(135deg, #1e1e35, #16213e)',
          overflow: 'hidden',
        }}>
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              style={{
                position: 'absolute', inset: 0, width: '100%', height: '100%',
                objectFit: 'cover', transition: 'transform 0.4s ease',
              }}
              onMouseEnter={e => e.target.style.transform = 'scale(1.05)'}
              onMouseLeave={e => e.target.style.transform = 'scale(1)'}
            />
          ) : (
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '48px', opacity: 0.3,
            }}>🛍️</div>
          )}

          {/* Discount badge */}
          {hasDiscount && (
            <div style={{
              position: 'absolute', top: '12px', left: '12px',
              background: 'linear-gradient(135deg, #ef4444, #dc2626)',
              color: 'white', fontSize: '11px', fontWeight: 700,
              padding: '3px 8px', borderRadius: '6px',
            }}>-{discountPct}%</div>
          )}

          {/* Out of stock */}
          {product.stock === 0 && (
            <div style={{
              position: 'absolute', inset: 0,
              background: 'rgba(0,0,0,0.6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)',
            }}>Out of Stock</div>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: '16px' }}>

          {/* Brand */}
          {product.brand && (
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--primary-light)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {product.brand}
            </div>
          )}

          {/* Name */}
          <h3 style={{
            fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)',
            marginBottom: '8px', lineHeight: '1.4',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>
            {product.name}
          </h3>

          {/* Rating */}
          {product.rating > 0 && (
            <div style={{ marginBottom: '10px' }}>
              <StarRating rating={product.rating} count={product.review_count} />
            </div>
          )}

          {/* Price */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
              ₹{Number(effectivePrice).toLocaleString('en-IN')}
            </span>
            {hasDiscount && (
              <span style={{ fontSize: '13px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>
                ₹{Number(product.price).toLocaleString('en-IN')}
              </span>
            )}
          </div>

          {/* Add to Cart */}
          {isAuthenticated && (
            <button
              onClick={handleAddToCart}
              disabled={adding || product.stock === 0}
              className="btn btn-primary btn-sm btn-full"
              style={{ fontSize: '13px' }}
            >
              {adding ? (
                <><div className="spinner" style={{ width: '14px', height: '14px' }} /> Adding...</>
              ) : added ? (
                <>✅ Added to Cart</>
              ) : product.stock === 0 ? (
                'Out of Stock'
              ) : (
                <>🛒 Add to Cart</>
              )}
            </button>
          )}
          {!isAuthenticated && (
            <Link to="/login" className="btn btn-outline btn-sm btn-full" style={{ fontSize: '13px' }}>
              Login to Buy
            </Link>
          )}
        </div>
      </div>
    </Link>
  );
}
