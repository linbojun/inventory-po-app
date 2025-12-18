import { createContext, useContext, useState, useEffect } from 'react';
import { productAPI } from '../api';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cartCount, setCartCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const fetchCartCount = async () => {
    try {
      const response = await productAPI.getCart({ page: 1, page_size: 1 });
      setCartCount(response.data.total);
    } catch (error) {
      console.error('Failed to fetch cart count:', error);
      setCartCount(0);
    } finally {
      setLoading(false);
    }
  };

  const triggerRefresh = () => {
    fetchCartCount();
    // Trigger product list refresh by incrementing refreshTrigger
    setRefreshTrigger(prev => prev + 1);
  };

  useEffect(() => {
    fetchCartCount();
    // Refresh cart count every 30 seconds
    const interval = setInterval(fetchCartCount, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <CartContext.Provider value={{ cartCount, refreshCart: fetchCartCount, triggerRefresh, refreshTrigger, loading }}>
      {children}
    </CartContext.Provider>
  );
};

