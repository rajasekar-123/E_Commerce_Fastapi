import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

function StarRating({ rating, count, large }) {
  const stars = Math.round(rating || 0);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      {[1,2,3,4,5].map(s => (
        <span key={s} style={{ fontSize: large ? '20px' : '14px', color: '#f59e0b', opacity: s <= stars ? 1 : 0.2 }}>★</span>
      ))}
      {count !== undefined && (
        <span style={{ fontSize: '13px', color: 'var(--text-muted)', marginLeft: '6px' }}>
          {rating?.toFixed(1)} ({count} reviews)
        </span>
      )}
    </div>
  );
}

export default function ProductDetail() {
  const { id } = useParams();
  const { addItem } = useCart();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/products/${id}`, { auth: false })
      .then(res => setProduct(res.data))
      .catch(() => setError('Product not found'))
      .finally(() => setLoading(false));
  }, [id]);

  const effectivePrice = product?.discount_price && product.discount_price < product.price
    ? product.discount_price
    : product?.price;
  const hasDiscount = product?.discount_price && product.discount_price < product.price;
  const discountPct = hasDiscount ? Math.round((1 - product.discount_price / product.price) * 100) : 0;

  const handleAddToCart = async () => {
    if (!isAuthenticated) { navigate('/login'); return; }
    setAdding(true);
    try {
      await addItem(product.id, quantity);
      setAdded(true);
      setTimeout(() => setAdded(false), 2500);
    } catch (err) {
      setError(err.message || 'Failed to add to cart');
    } finally {
      setAdding(false);
    }
  };

  if (loading) return (
    <div className="container page-wrapper">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '48px' }}>
        <div className="skeleton" style={{ borderRadius: '20px', paddingBottom: '100%' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[180, 100, 60, 40, 200, 56].map((h, i) => (
            <div key={i} className="skeleton" style={{ height: h + 'px', borderRadius: '8px' }} />
          ))}
        </div>
      </div>
    </div>
  );

  if (!product) return (
    <div className="container page-wrapper" style={{ textAlign: 'center' }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
      <h2>Product Not Found</h2>
      <Link to="/" className="btn btn-primary" style={{ marginTop: '20px' }}>Back to Store</Link>
    </div>
  );

  return (
    <div className="container page-wrapper">

      {/* Breadcrumb */}
      <nav style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '32px', fontSize: '14px', color: 'var(--text-muted)' }}>
        <Link to="/" style={{ color: 'var(--primary-light)' }}>Home</Link>
        <span>/</span>
        {product.category_id && <span>{product.category_id}</span>}
        <span>/</span>
        <span style={{ color: 'var(--text-primary)' }}>{product.name}</span>
      </nav>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '48px' }}>

        {/* Left: Image */}
        <div>
          <div style={{
            borderRadius: '20px', overflow: 'hidden',
            background: 'linear-gradient(135deg, var(--bg-card), var(--bg-elevated))',
            border: '1px solid var(--border-subtle)',
            paddingBottom: '100%', position: 'relative',
          }}>
            {product.image_url ? (
              <img src={product.image_url} alt={product.name}
                style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <div style={{
                position: 'absolute', inset: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '80px', opacity: 0.2,
              }}>🛍️</div>
            )}
          </div>
        </div>

        {/* Right: Info */}
        <div className="fade-in">

          {product.brand && (
            <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--primary-light)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
              {product.brand}
            </div>
          )}

          <h1 style={{ fontSize: '28px', fontWeight: 800, lineHeight: 1.3, marginBottom: '16px' }}>
            {product.name}
          </h1>

          {product.rating > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <StarRating rating={product.rating} count={product.review_count} large />
            </div>
          )}

          {/* Price */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <span style={{ fontSize: '36px', fontWeight: 800 }}>
              ₹{Number(effectivePrice).toLocaleString('en-IN')}
            </span>
            {hasDiscount && (
              <>
                <span style={{ fontSize: '20px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>
                  ₹{Number(product.price).toLocaleString('en-IN')}
                </span>
                <span className="badge badge-error" style={{ fontSize: '14px', padding: '4px 10px' }}>
                  {discountPct}% OFF
                </span>
              </>
            )}
          </div>

          {/* Stock */}
          <div style={{ marginBottom: '24px' }}>
            {product.stock > 0 ? (
              <span style={{ color: 'var(--success)', fontSize: '14px', fontWeight: 600 }}>
                ✅ In Stock ({product.stock} available)
              </span>
            ) : (
              <span style={{ color: 'var(--error)', fontSize: '14px', fontWeight: 600 }}>
                ❌ Out of Stock
              </span>
            )}
          </div>

          {/* Description */}
          {product.description && (
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '28px', fontSize: '15px' }}>
              {product.description}
            </p>
          )}

          {/* Quantity + Add to Cart */}
          {product.stock > 0 && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0', border: '1.5px solid var(--border)', borderRadius: '10px', overflow: 'hidden' }}>
                <button onClick={() => setQuantity(q => Math.max(1, q - 1))}
                  style={{ padding: '10px 16px', background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: 'none', cursor: 'pointer', fontSize: '18px' }}>
                  −
                </button>
                <span style={{ padding: '10px 20px', fontWeight: 700, fontSize: '16px', minWidth: '50px', textAlign: 'center' }}>
                  {quantity}
                </span>
                <button onClick={() => setQuantity(q => Math.min(product.stock, q + 1))}
                  style={{ padding: '10px 16px', background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: 'none', cursor: 'pointer', fontSize: '18px' }}>
                  +
                </button>
              </div>

              <button onClick={handleAddToCart} disabled={adding} className="btn btn-primary btn-lg" style={{ flex: 1 }}>
                {adding ? (
                  <><div className="spinner" style={{ width: '16px', height: '16px' }} /> Adding...</>
                ) : added ? (
                  '✅ Added to Cart!'
                ) : '🛒 Add to Cart'}
              </button>
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}

          {added && (
            <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
              <Link to="/cart" className="btn btn-outline btn-full">View Cart →</Link>
              <Link to="/" className="btn btn-ghost btn-full">Continue Shopping</Link>
            </div>
          )}

          {/* Meta */}
          {product.sku && (
            <div style={{ marginTop: '24px', padding: '16px', background: 'var(--bg-elevated)', borderRadius: '12px', fontSize: '13px', color: 'var(--text-muted)' }}>
              SKU: <strong style={{ color: 'var(--text-secondary)' }}>{product.sku}</strong>
            </div>
          )}

          {/* Perks */}
          <div style={{ display: 'flex', gap: '16px', marginTop: '24px', flexWrap: 'wrap' }}>
            {['🚚 Free shipping above ₹999', '↩️ 30-day returns', '🔒 Secure checkout'].map(perk => (
              <div key={perk} style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {perk}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
