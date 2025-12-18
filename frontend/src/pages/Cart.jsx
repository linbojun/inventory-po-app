import { useState, useEffect } from 'react';
import { productAPI } from '../api';
import ProductCard from '../components/ProductCard';

function Cart() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchCart = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await productAPI.getCart({ page, page_size: 50 });
      setProducts(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch cart');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, [page]);

  const calculateTotal = () => {
    return products.reduce((sum, product) => {
      return sum + (parseFloat(product.price) || 0) * (product.order_qty || 0);
    }, 0);
  };

  const totalItems = products.reduce((sum, product) => sum + (product.order_qty || 0), 0);

  if (loading && products.length === 0) {
    return <div style={styles.loading}>Loading cart...</div>;
  }

  if (error) {
    return <div style={styles.error}>Error: {error}</div>;
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Shopping Cart / Purchase Order</h1>

      {products.length === 0 ? (
        <div style={styles.empty}>
          <p>Your cart is empty</p>
          <p style={styles.emptySubtext}>Add products to your order by setting order_qty &gt; 0</p>
        </div>
      ) : (
        <>
          <div style={styles.summary}>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Total Items:</span>
              <span style={styles.summaryValue}>{totalItems}</span>
            </div>
            <div style={styles.summaryItem}>
              <span style={styles.summaryLabel}>Total Cost:</span>
              <span style={styles.summaryValue}>${calculateTotal().toFixed(2)}</span>
            </div>
          </div>

          <div style={styles.grid}>
            {products.map((product) => (
              <ProductCard key={product.id} product={product} onUpdate={fetchCart} />
            ))}
          </div>

          {totalPages > 1 && (
            <div style={styles.pagination}>
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                style={styles.pageButton}
              >
                Previous
              </button>
              <span style={styles.pageInfo}>
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                style={styles.pageButton}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '2rem 1rem',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '2rem',
    color: '#2c3e50',
  },
  summary: {
    display: 'flex',
    gap: '2rem',
    marginBottom: '2rem',
    padding: '1.5rem',
    backgroundColor: '#ecf0f1',
    borderRadius: '8px',
    flexWrap: 'wrap',
  },
  summaryItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  summaryLabel: {
    fontSize: '0.9rem',
    color: '#7f8c8d',
  },
  summaryValue: {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: '#2c3e50',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1.5rem',
  },
  loading: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.2rem',
    color: '#7f8c8d',
  },
  error: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.2rem',
    color: '#e74c3c',
  },
  empty: {
    textAlign: 'center',
    padding: '3rem',
    fontSize: '1.2rem',
    color: '#7f8c8d',
  },
  emptySubtext: {
    fontSize: '1rem',
    marginTop: '0.5rem',
    color: '#95a5a6',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '1rem',
    marginTop: '2rem',
  },
  pageButton: {
    padding: '0.5rem 1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
  },
  pageInfo: {
    fontSize: '1rem',
    color: '#34495e',
  },
};

export default Cart;

