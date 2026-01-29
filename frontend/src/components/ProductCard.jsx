import { Link } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { productAPI, resolveImageUrl } from '../api';
import './ProductCard.css';

function ProductCard({ product, onUpdate }) {
  const initialOrderQty = Number.isFinite(product.order_qty) ? product.order_qty : 0;
  const initialStockCount = Number.isFinite(product.stock) ? product.stock : 0;

  const [orderQty, setOrderQty] = useState(initialOrderQty);
  const [stockCount, setStockCount] = useState(initialStockCount);
  const [orderInputValue, setOrderInputValue] = useState(String(initialOrderQty));
  const [stockInputValue, setStockInputValue] = useState(String(initialStockCount));
  const [isOrderUpdating, setIsOrderUpdating] = useState(false);
  const [isStockUpdating, setIsStockUpdating] = useState(false);
  const orderCancelCommitRef = useRef(false);
  const stockCancelCommitRef = useRef(false);

  const normalizeInput = (value) => {
    const parsed = parseInt(value, 10);
    if (Number.isNaN(parsed) || parsed < 0) return 0;
    return parsed;
  };

  // Sync local state when product prop changes (e.g., after Clear All)
  useEffect(() => {
    const nextOrderQty = Number.isFinite(product.order_qty) ? product.order_qty : 0;
    const nextStock = Number.isFinite(product.stock) ? product.stock : 0;
    setOrderQty(nextOrderQty);
    setStockCount(nextStock);
    setOrderInputValue(String(nextOrderQty));
    setStockInputValue(String(nextStock));
  }, [product.order_qty, product.stock]);

  const handleOrderQtyChange = async (newQty) => {
    if (newQty < 0) return;
    const previousOrderQty = orderQty;
    setIsOrderUpdating(true);
    try {
      await productAPI.updateOrderQty(product.id, newQty);
      setOrderQty(newQty);
      setOrderInputValue(String(newQty));
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update order quantity: ' + (error.response?.data?.detail || error.message));
      setOrderQty(previousOrderQty);
      setOrderInputValue(String(previousOrderQty));
    } finally {
      setIsOrderUpdating(false);
    }
  };

  const handleStockChange = async (newStock) => {
    if (newStock < 0) return;
    const previousStock = stockCount;
    setIsStockUpdating(true);
    try {
      await productAPI.updateStock(product.id, newStock);
      setStockCount(newStock);
      setStockInputValue(String(newStock));
      if (onUpdate) onUpdate();
    } catch (error) {
      alert('Failed to update stock: ' + (error.response?.data?.detail || error.message));
      setStockCount(previousStock);
      setStockInputValue(String(previousStock));
    } finally {
      setIsStockUpdating(false);
    }
  };

  const incrementOrder = () => handleOrderQtyChange(orderQty + 1);
  const decrementOrder = () => handleOrderQtyChange(Math.max(0, orderQty - 1));
  const incrementStock = () => handleStockChange(stockCount + 1);
  const decrementStock = () => handleStockChange(Math.max(0, stockCount - 1));

  const handleStockInputBlur = () => {
    if (stockCancelCommitRef.current) {
      stockCancelCommitRef.current = false;
      setStockInputValue(String(stockCount));
      return;
    }
    const normalizedValue = normalizeInput(stockInputValue);
    if (normalizedValue !== stockCount) {
      handleStockChange(normalizedValue);
    } else {
      setStockInputValue(String(stockCount));
    }
  };

  const handleOrderInputBlur = () => {
    if (orderCancelCommitRef.current) {
      orderCancelCommitRef.current = false;
      setOrderInputValue(String(orderQty));
      return;
    }
    const normalizedValue = normalizeInput(orderInputValue);
    if (normalizedValue !== orderQty) {
      handleOrderQtyChange(normalizedValue);
    } else {
      setOrderInputValue(String(orderQty));
    }
  };

  const handleStockInputKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.currentTarget.blur();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      stockCancelCommitRef.current = true;
      setStockInputValue(String(stockCount));
      event.currentTarget.blur();
    }
  };

  const handleOrderInputKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      event.currentTarget.blur();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      orderCancelCommitRef.current = true;
      setOrderInputValue(String(orderQty));
      event.currentTarget.blur();
    }
  };

  return (
    <div className="product-card">
      <Link to={`/product/${product.id}`} className="product-card__imageLink">
        <img
          src={resolveImageUrl(product.image_url)}
          alt={product.name}
          className="product-card__image"
          onError={(e) => {
            e.target.src =
              'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
          }}
        />
      </Link>

      <div className="product-card__content">
        <Link to={`/product/${product.id}`} className="product-card__titleLink">
          <h3 className="product-card__name">{product.name}</h3>
        </Link>
        {product.brand && <p className="product-card__brand">{product.brand}</p>}
        <p className="product-card__productId">ID: {product.product_id}</p>

        <div className="product-card__info">
          <div className="product-card__row">
            <span className="product-card__label">Stock:</span>
            <div className="product-card__qtyControls">
              <button
                onClick={decrementStock}
                disabled={isStockUpdating || stockCount === 0}
                className="product-card__qtyButton"
                title="Decrease stock"
              >
                ↓
              </button>
              <input
                type="number"
                value={stockInputValue}
                onChange={(e) => setStockInputValue(e.target.value)}
                onBlur={handleStockInputBlur}
                onKeyDown={handleStockInputKeyDown}
                className="product-card__qtyInput"
                min="0"
                inputMode="numeric"
                pattern="[0-9]*"
              />
              <button
                onClick={incrementStock}
                disabled={isStockUpdating}
                className="product-card__qtyButton"
                title="Increase stock"
              >
                ↑
              </button>
            </div>
          </div>

          <div className="product-card__row">
            <span className="product-card__label">Order:</span>
            <div className="product-card__qtyControls">
              <button
                onClick={decrementOrder}
                disabled={isOrderUpdating || orderQty === 0}
                className="product-card__qtyButton"
                title="Decrease order quantity"
              >
                ↓
              </button>
              <input
                type="number"
                value={orderInputValue}
                onChange={(e) => setOrderInputValue(e.target.value)}
                onBlur={handleOrderInputBlur}
                onKeyDown={handleOrderInputKeyDown}
                className="product-card__qtyInput"
                min="0"
                inputMode="numeric"
                pattern="[0-9]*"
              />
              <button
                onClick={incrementOrder}
                disabled={isOrderUpdating}
                className="product-card__qtyButton"
                title="Increase order quantity"
              >
                ↑
              </button>
            </div>
          </div>
        </div>

        {product.remarks && (
          <p className="product-card__remarks" title={product.remarks}>
            💬 {product.remarks.substring(0, 30)}{product.remarks.length > 30 ? '...' : ''}
          </p>
        )}
      </div>
    </div>
  );
}

export default ProductCard;
