import { Link, useLocation } from 'react-router-dom';
import { productAPI } from '../api';
import { useState } from 'react';

function NavBar({ cartCount, onReset }) {
  const location = useLocation();
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset all products? This will set all stock and order_qty to 0.')) {
      try {
        await productAPI.resetAll();
        alert('All products reset successfully');
        if (onReset) onReset();
      } catch (error) {
        alert('Failed to reset products: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  return (
    <nav style={styles.nav}>
      <div style={styles.container} className="nav-container">
        <Link to="/" style={styles.logo}>
          Inventory PO
        </Link>
        <div style={styles.links} className="nav-links">
          <Link 
            to="/" 
            style={location.pathname === '/' ? styles.activeLink : styles.link}
          >
            Products
          </Link>
          <Link 
            to="/cart" 
            style={location.pathname === '/cart' ? styles.activeLink : styles.link}
          >
            Cart {cartCount > 0 && <span style={styles.badge}>{cartCount}</span>}
          </Link>
          <Link 
            to="/import" 
            style={location.pathname === '/import' ? styles.activeLink : styles.link}
          >
            Import
          </Link>
          <button onClick={handleReset} style={styles.resetButton}>
            Clear All
          </button>
        </div>
      </div>
    </nav>
  );
}

const styles = {
  nav: {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '1rem 0',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  logo: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: 'white',
    textDecoration: 'none',
  },
  links: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  link: {
    color: 'white',
    textDecoration: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
  },
  activeLink: {
    color: 'white',
    textDecoration: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  badge: {
    backgroundColor: '#e74c3c',
    borderRadius: '10px',
    padding: '2px 6px',
    fontSize: '0.8rem',
    marginLeft: '4px',
  },
  resetButton: {
    backgroundColor: '#e74c3c',
    color: 'white',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    transition: 'background-color 0.2s',
  },
};

export default NavBar;

