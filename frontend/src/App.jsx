import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider, useCart } from './contexts/CartContext';
import NavBar from './components/NavBar';
import ProductList from './pages/ProductList';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Import from './pages/Import';
import './App.css';

function AppContent() {
  const { cartCount, triggerRefresh } = useCart();

  return (
    <Router>
      <div className="App">
        <NavBar cartCount={cartCount} onReset={triggerRefresh} />
        <main style={{ minHeight: 'calc(100vh - 80px)' }}>
          <Routes>
            <Route path="/" element={<ProductList />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/import" element={<Import />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function App() {
  return (
    <CartProvider>
      <AppContent />
    </CartProvider>
  );
}

export default App;
