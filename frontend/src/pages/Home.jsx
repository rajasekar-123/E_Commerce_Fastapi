import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import ProductCard from '../components/ProductCard';

const SORTS = [
  { value: '', label: '✨ Featured' },
  { value: 'newest', label: '🆕 Newest' },
  { value: 'price_asc', label: '💰 Price: Low → High' },
  { value: 'price_desc', label: '💸 Price: High → Low' },
  { value: 'rating_desc', label: '⭐ Top Rated' },
];

function SkeletonCard() {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div className="skeleton" style={{ paddingBottom: '70%' }} />
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div className="skeleton" style={{ height: '12px', width: '50%' }} />
        <div className="skeleton" style={{ height: '16px', width: '90%' }} />
        <div className="skeleton" style={{ height: '14px', width: '70%' }} />
        <div className="skeleton" style={{ height: '36px', borderRadius: '8px' }} />
      </div>
    </div>
  );
}

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const query = searchParams.get('q') || '';
  const categoryId = searchParams.get('category') || '';
  const sort = searchParams.get('sort') || '';
  const minPrice = searchParams.get('min') || '';
  const maxPrice = searchParams.get('max') || '';

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (query) params.query = query;
      if (categoryId) params.category_id = categoryId;
      if (sort) params.sort = sort;
      if (minPrice) params.min_price = minPrice;
      if (maxPrice) params.max_price = maxPrice;
      params.limit = 40;

      const endpoint = Object.keys(params).length > 1 || query || categoryId ? '/products/search' : '/products';
      const res = await api.get(endpoint, { params, auth: false });
      setProducts(res.data || []);
    } catch (err) {
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  }, [query, categoryId, sort, minPrice, maxPrice]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  useEffect(() => {
    api.get('/categories', { auth: false })
      .then(res => setCategories(res.data || []))
      .catch(() => {});
  }, []);

  const setFilter = (key, value) => {
    setSearchParams(prev => {
      if (value) prev.set(key, value);
      else prev.delete(key);
      return prev;
    });
  };

  return (
    <div>
      {/* Hero Banner */}
      {!query && !categoryId && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.1) 50%, rgba(6,182,212,0.08) 100%)',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '60px 0',
          textAlign: 'center',
        }}>
          <div className="container">
            <div style={{ marginBottom: '12px' }}>
              <span style={{
                display: 'inline-block', padding: '4px 16px',
                background: 'rgba(99,102,241,0.2)', color: 'var(--primary-light)',
                borderRadius: '20px', fontSize: '13px', fontWeight: 600,
              }}>🚀 Premium Shopping Experience</span>
            </div>
            <h1 style={{ fontSize: '52px', fontWeight: 800, lineHeight: 1.15, marginBottom: '16px', letterSpacing: '-0.03em' }}>
              Discover <span className="gradient-text">Amazing</span> Products
            </h1>
            <p style={{ fontSize: '18px', color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto 32px' }}>
              Shop from thousands of products with AI-powered recommendations
            </p>
            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '16px 24px', borderRadius: '16px', textAlign: 'left' }}>
                <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary-light)' }}>10K+</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Products</div>
              </div>
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '16px 24px', borderRadius: '16px', textAlign: 'left' }}>
                <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--success)' }}>Free</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Shipping above ₹999</div>
              </div>
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', padding: '16px 24px', borderRadius: '16px', textAlign: 'left' }}>
                <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--secondary)' }}>AI</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500' }}>Shopping Assistant</div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="container page-wrapper">

        {/* Filters Row */}
        <div style={{
          display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center',
          marginBottom: '28px',
        }}>
          {/* Category */}
          <select
            value={categoryId}
            onChange={e => setFilter('category', e.target.value)}
            className="form-select"
            style={{ width: 'auto', minWidth: '160px' }}
          >
            <option value="">All Categories</option>
            {categories.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sort}
            onChange={e => setFilter('sort', e.target.value)}
            className="form-select"
            style={{ width: 'auto', minWidth: '180px' }}
          >
            {SORTS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          {/* Price Range */}
          <input
            type="number"
            placeholder="Min ₹"
            value={minPrice}
            onChange={e => setFilter('min', e.target.value)}
            className="form-input"
            style={{ width: '100px' }}
          />
          <input
            type="number"
            placeholder="Max ₹"
            value={maxPrice}
            onChange={e => setFilter('max', e.target.value)}
            className="form-input"
            style={{ width: '100px' }}
          />

          {/* Clear Filters */}
          {(query || categoryId || sort || minPrice || maxPrice) && (
            <button onClick={() => setSearchParams({})} className="btn btn-ghost btn-sm">
              ✕ Clear
            </button>
          )}

          {/* Result count */}
          {!loading && (
            <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '14px' }}>
              {products.length} product{products.length !== 1 ? 's' : ''}
              {query && ` for "${query}"`}
            </span>
          )}
        </div>

        {/* Error */}
        {error && <div className="alert alert-error" style={{ marginBottom: '24px' }}>⚠️ {error}</div>}

        {/* Product Grid */}
        <div className="product-grid">
          {loading
            ? Array(8).fill(0).map((_, i) => <SkeletonCard key={i} />)
            : products.length === 0
              ? (
                <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                  <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '8px' }}>No products found</h3>
                  <p style={{ color: 'var(--text-muted)' }}>Try adjusting your filters or search term</p>
                </div>
              )
              : products.map(product => <ProductCard key={product.id} product={product} />)
          }
        </div>
      </div>
    </div>
  );
}
