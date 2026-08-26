/**
 * CartContext — global cart state.
 *
 * Fetches the cart from the backend on mount (when authenticated).
 * Provides helpers for add/update/remove/clear that sync with the API.
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';

const CartContext = createContext(null);

const EMPTY_CART = { items: [], item_count: 0, subtotal: 0, total: 0, total_discount: 0 };

export function CartProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [cart, setCart] = useState(EMPTY_CART);
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      setLoading(true);
      const res = await api.get('/cart');
      setCart(res.data);
    } catch {
      // Silently fail — cart is optional on some pages
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = useCallback(async (product_id, quantity = 1) => {
    const res = await api.post('/cart/items', { product_id, quantity });
    setCart(res.data);
    return res.data;
  }, []);

  const updateItem = useCallback(async (item_id, quantity) => {
    const res = await api.put(`/cart/items/${item_id}`, { quantity });
    setCart(res.data);
    return res.data;
  }, []);

  const removeItem = useCallback(async (item_id) => {
    const res = await api.delete(`/cart/items/${item_id}`);
    setCart(res.data);
    return res.data;
  }, []);

  const clearCart = useCallback(async () => {
    await api.delete('/cart');
    setCart(EMPTY_CART);
  }, []);

  const resetCart = useCallback(() => setCart(EMPTY_CART), []);

  return (
    <CartContext.Provider value={{ cart, loading, fetchCart, addItem, updateItem, removeItem, clearCart, resetCart }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}
