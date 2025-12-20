import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { productAPI, resolveImageUrl } from '../api';

function ProductCard({ product, onUpdate }) {
  const [orderQty, setOrderQty] = useState(product.order_qty);
  const [stockCount, setStockCount] = useState(product.stock);
  const [isOrderUpdating, setIsOrderUpdating] = useState(false);
  const [isStockUpdating, setIsStockUpdating] = useState(false);

  // Sync local state when product prop changes (e.g., after Clear All)
  useEffect(() => {
    setOrderQty(product.order_qty);
    setStockCount(product.stock);
  }, [product.order_qty, product.stock]);

  const handleOrderQtyChange = async (newQty) => {
    if (newQty < 0) return;
    
    setIsOrderUpdating(true);
    try {
      await productAPI.updateOrderQty(product.id, newQty);
      setOrderQty(newQty);
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update order quantity: ' + (error.response?.data?.detail || error.message));
      setOrderQty(product.order_qty);
    } finally {
      setIsOrderUpdating(false);
    }
  };

  const handleStockChange = async (newStock) => {
    if (newStock < 0) return;

    setIsStockUpdating(true);
    try {
      await productAPI.updateStock(product.id, newStock);
      setStockCount(newStock);
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update stock: ' + (error.response?.data?.detail || error.message));
      setStockCount(product.stock);
    } finally {
      setIsStockUpdating(false);
    }
  };

  const incrementOrder = () => handleOrderQtyChange(orderQty + 1);
  const decrementOrder = () => handleOrderQtyChange(Math.max(0, orderQty - 1));
  const incrementStock = () => handleStockChange(stockCount + 1);
  const decrementStock = () => handleStockChange(Math.max(0, stockCount - 1));

  return (
    <div style={styles.card}>
      <Link to={`/product/${product.id}`} style={styles.imageLink}>
        <img 
          src={resolveImageUrl(product.image_url)} 
          alt={product.name}
          style={styles.image}
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
          }}
        />
      </Link>
      <div style={styles.content}>
        <Link to={`/product/${product.id}`} style={styles.titleLink}>
          <h3 style={styles.name}>{product.name}</h3>
        </Link>
        {product.brand && <p style={styles.brand}>{product.brand}</p>}
        <p style={styles.productId}>ID: {product.product_id}</p>
        <div style={styles.info}>
          <div style={styles.stock}>
            <span style={styles.label}>Stock:</span>
            <div style={styles.qtyControls}>
              <button
                onClick={decrementStock}
                disabled={isStockUpdating || stockCount === 0}
                style={styles.qtyButton}
                title="Decrease stock"
              >
                ↓
              </button>
              <input
                type="number"
                value={stockCount}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  const nextValue = Number.isNaN(val) ? 0 : val;
                  if (nextValue >= 0) handleStockChange(nextValue);
                }}
                style={styles.qtyInput}
                min="0"
                disabled={isStockUpdating}
              />
              <button
                onClick={incrementStock}
                disabled={isStockUpdating}
                style={styles.qtyButton}
                title="Increase stock"
              >
                ↑
              </button>
            </div>
          </div>
          <div style={styles.orderQty}>
            <span style={styles.label}>Order:</span>
            <div style={styles.qtyControls}>
              <button 
                onClick={decrementOrder} 
                disabled={isOrderUpdating || orderQty === 0}
                style={styles.qtyButton}
                title="Decrease order quantity"
              >
                ↓
              </button>
              <input
                type="number"
                value={orderQty}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  const nextValue = Number.isNaN(val) ? 0 : val;
                  if (nextValue >= 0) handleOrderQtyChange(nextValue);
                }}
                style={styles.qtyInput}
                min="0"
                disabled={isOrderUpdating}
              />
              <button 
                onClick={incrementOrder} 
                disabled={isOrderUpdating}
                style={styles.qtyButton}
                title="Increase order quantity"
              >
                ↑
              </button>
            </div>
          </div>
        </div>
        {product.remarks && (
          <p style={styles.remarks} title={product.remarks}>
            💬 {product.remarks.substring(0, 30)}{product.remarks.length > 30 ? '...' : ''}
          </p>
        )}
      </div>
    </div>
  );
}

const styles = {
  card: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    overflow: 'hidden',
    backgroundColor: 'white',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    transition: 'transform 0.2s, box-shadow 0.2s',
    display: 'flex',
    flexDirection: 'column',
  },
  imageLink: {
    display: 'block',
    width: '100%',
    aspectRatio: '4/3',
    overflow: 'hidden',
    backgroundColor: '#f5f5f5',
  },
  image: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    backgroundColor: '#f5f5f5',
  },
  content: {
    padding: '1rem',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  titleLink: {
    textDecoration: 'none',
    color: 'inherit',
  },
  name: {
    margin: '0 0 0.5rem 0',
    fontSize: '1.1rem',
    fontWeight: '600',
    color: '#2c3e50',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  brand: {
    margin: '0 0 0.5rem 0',
    fontSize: '0.9rem',
    color: '#7f8c8d',
  },
  productId: {
    margin: '0 0 1rem 0',
    fontSize: '0.85rem',
    color: '#95a5a6',
  },
  info: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
    marginTop: 'auto',
  },
  stock: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  orderQty: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: '0.9rem',
    color: '#34495e',
    fontWeight: '500',
  },
  qtyControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  qtyButton: {
    width: '28px',
    height: '28px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '1.2rem',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
    color: '#2c3e50',
    lineHeight: '1',
  },
  qtyInput: {
    width: '50px',
    padding: '4px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    textAlign: 'center',
    fontSize: '0.9rem',
  },
  remarks: {
    margin: '0.5rem 0 0 0',
    fontSize: '0.85rem',
    color: '#7f8c8d',
    fontStyle: 'italic',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
};

export default ProductCard;

