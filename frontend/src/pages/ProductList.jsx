import { useState, useEffect, useCallback } from 'react';
import { productAPI } from '../api';
import ProductCard from '../components/ProductCard';
import { useCart } from '../contexts/CartContext';

function ProductList() {
  const { refreshTrigger } = useCart();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('product_id');
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [debounceTimer, setDebounceTimer] = useState(null);
  const [isManualSortChange, setIsManualSortChange] = useState(false);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        page_size: 50,
        sort_by: sortBy,
        sort_dir: sortDir,
      };
      if (search.trim()) {
        params.search = search.trim();
      }
      const response = await productAPI.getProducts(params);
      setProducts(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  }, [page, sortBy, sortDir, search]);

  // Main effect: fetch products when dependencies change
  // Skip if this is a manual sort change (handled directly in handleSortChange)
  useEffect(() => {
    if (!isManualSortChange) {
      fetchProducts();
    } else {
      setIsManualSortChange(false); // Reset flag after skipping
    }
  }, [fetchProducts, isManualSortChange]);

  // Refresh products when refreshTrigger changes (e.g., after Clear All)
  useEffect(() => {
    if (refreshTrigger > 0) {
      fetchProducts();
    }
  }, [refreshTrigger, fetchProducts]);

  useEffect(() => {
    // Debounce search
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    const timer = setTimeout(() => {
      setPage(1);
      // fetchProducts will be called automatically when page changes via main useEffect
    }, 500);
    setDebounceTimer(timer);

    return () => {
      if (timer) clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
  };

  const handleSortChange = async (e) => {
    const value = e.target.value;
    const separatorIndex = value.lastIndexOf('_');

    if (separatorIndex === -1) {
      console.error('Invalid sort value format:', value);
      return;
    }

    const newSortBy = value.slice(0, separatorIndex);
    const newSortDir = value.slice(separatorIndex + 1);
    
    // Ensure we have valid values
    if (!newSortBy || !newSortDir || !['asc', 'desc'].includes(newSortDir)) {
      console.error('Invalid sort value:', { newSortBy, newSortDir, value });
      return;
    }
    
    // Set flag to prevent useEffect from running with stale values
    setIsManualSortChange(true);
    
    // Update state values - React will batch these
    setSortBy(newSortBy);
    setSortDir(newSortDir);
    setPage(1);
    
    // Immediately fetch with the new sort values to ensure correct ordering
    // This bypasses any potential race conditions with useCallback
    try {
      setLoading(true);
      setError(null);
      const params = {
        page: 1,
        page_size: 50,
        sort_by: newSortBy,
        sort_dir: newSortDir,
      };
      if (search.trim()) {
        params.search = search.trim();
      }
      const response = await productAPI.getProducts(params);
      setProducts(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  const getSortDisplayText = () => {
    if (sortBy === 'product_id') {
      return sortDir === 'asc' ? 'Product ID (A-Z ↑)' : 'Product ID (Z-A ↓)';
    } else if (sortBy === 'stock') {
      return sortDir === 'asc' ? 'Stock (Low to High ↑)' : 'Stock (High to Low ↓)';
    }
    return 'Sort by...';
  };

  if (loading && products.length === 0) {
    return <div style={styles.loading}>Loading products...</div>;
  }

  if (error) {
    return <div style={styles.error}>Error: {error}</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Products</h1>
        <div style={styles.controls}>
          <input
            type="text"
            placeholder="Search by ID, name, or brand..."
            value={search}
            onChange={handleSearchChange}
            style={styles.searchInput}
          />
          <div style={styles.sortContainer}>
            <label style={styles.sortLabel}>Sort</label>
            <select value={`${sortBy}_${sortDir}`} onChange={handleSortChange} style={styles.sortSelect}>
              <option value="product_id_asc">Product ID (A-Z ↑)</option>
              <option value="product_id_desc">Product ID (Z-A ↓)</option>
              <option value="stock_asc">Stock (Low to High ↑)</option>
              <option value="stock_desc">Stock (High to Low ↓)</option>
            </select>
          </div>
        </div>
      </div>

      {products.length === 0 ? (
        <div style={styles.empty}>No products found</div>
      ) : (
        <>
          <div style={styles.grid}>
            {products.map((product) => (
              <ProductCard key={product.id} product={product} onUpdate={fetchProducts} />
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
  header: {
    marginBottom: '2rem',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '1rem',
    color: '#2c3e50',
  },
  controls: {
    display: 'flex',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  searchInput: {
    flex: '1',
    minWidth: '200px',
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  sortContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  sortLabel: {
    fontSize: '0.9rem',
    color: '#34495e',
    fontWeight: '500',
  },
  sortSelect: {
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    backgroundColor: 'white',
    minWidth: '200px',
    cursor: 'pointer',
    color: '#555555',
  },
  sortIndicator: {
    fontSize: '0.9rem',
    color: '#7f8c8d',
    fontWeight: '500',
    padding: '0.5rem 0.75rem',
    backgroundColor: '#ecf0f1',
    borderRadius: '4px',
    whiteSpace: 'nowrap',
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

export default ProductList;

