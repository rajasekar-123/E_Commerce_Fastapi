/**
 * AuthContext — JWT auth state management.
 *
 * Token stored in localStorage under key 'ecommerce_auth'.
 * Provides: user, token, login, logout, isAdmin helpers.
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const AuthContext = createContext(null);

const STORAGE_KEY = 'ecommerce_auth';

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    } catch {
      return null;
    }
  });

  const login = useCallback((authData) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(authData));
    setAuth(authData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setAuth(null);
  }, []);

  const isAdmin = auth?.role === 'ADMIN';
  const isAuthenticated = !!auth?.token;

  return (
    <AuthContext.Provider value={{ auth, login, logout, isAdmin, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
