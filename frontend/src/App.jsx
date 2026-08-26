import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Orders from './pages/Orders';
import OrderSuccess from './pages/OrderSuccess';
import AIChat from './pages/AIChat';

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <BrowserRouter>
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            
            {/* Protected User Routes */}
            <Route path="/cart" element={
              <ProtectedRoute><Cart /></ProtectedRoute>
            } />
            <Route path="/checkout" element={
              <ProtectedRoute><Checkout /></ProtectedRoute>
            } />
            <Route path="/orders" element={
              <ProtectedRoute><Orders /></ProtectedRoute>
            } />
            <Route path="/payment/success" element={
              <ProtectedRoute><OrderSuccess /></ProtectedRoute>
            } />
            
            {/* AI Assistant Chat */}
            <Route path="/ai-chat" element={
              <ProtectedRoute><AIChat /></ProtectedRoute>
            } />

            {/* Placeholder for Admin - built later if needed */}
            <Route path="/admin/*" element={
              <ProtectedRoute adminOnly>
                <div className="container page-wrapper" style={{ textAlign: 'center', paddingTop: '100px' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚙️</div>
                  <h2>Admin Dashboard Coming Soon</h2>
                </div>
              </ProtectedRoute>
            } />

            <Route path="*" element={
              <div className="container page-wrapper" style={{ textAlign: 'center', paddingTop: '100px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>404</div>
                <h2>Page Not Found</h2>
              </div>
            } />
          </Routes>
        </BrowserRouter>
      </CartProvider>
    </AuthProvider>
  );
}
