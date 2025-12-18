import axios from 'axios';

// In production set VITE_API_URL (e.g. https://your-backend.onrender.com/api)
// For local dev it falls back to localhost.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const getApiOrigin = () => {
  // If baseURL ends with /api, strip it to get origin.
  // Example: https://example.com/api -> https://example.com
  if (API_BASE_URL.endsWith('/api')) return API_BASE_URL.slice(0, -4);
  return API_BASE_URL;
};

export const resolveImageUrl = (imageUrl) => {
  if (!imageUrl) return '/placeholder-image.png';
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) return imageUrl;
  return `${getApiOrigin()}${imageUrl}`;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const productAPI = {
  // Get products with search, sort, pagination
  getProducts: (params = {}) => {
    return api.get('/products', { params });
  },

  // Get single product
  getProduct: (id) => {
    return api.get(`/products/${id}`);
  },

  // Create product (with optional image file)
  createProduct: (data, imageFile = null) => {
    const formData = new FormData();
    const { force_new_image, ...fields } = data;
    formData.append('product_id', fields.product_id);
    formData.append('name', fields.name);
    if (fields.brand) formData.append('brand', fields.brand);
    if (fields.price !== undefined) formData.append('price', fields.price);
    if (fields.stock !== undefined) formData.append('stock', fields.stock);
    if (fields.order_qty !== undefined) formData.append('order_qty', fields.order_qty);
    if (fields.remarks) formData.append('remarks', fields.remarks);
    if (force_new_image !== undefined) {
      formData.append('force_new_image', force_new_image ? 'true' : 'false');
    }
    if (imageFile) formData.append('image', imageFile);
    
    return api.post('/products', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Update product (with optional image file)
  updateProduct: (id, data, imageFile = null) => {
    const formData = new FormData();
    const { force_new_image, ...fields } = data;
    if (fields.name !== undefined) formData.append('name', fields.name);
    if (fields.brand !== undefined) formData.append('brand', fields.brand);
    if (fields.price !== undefined) formData.append('price', fields.price);
    if (fields.stock !== undefined) formData.append('stock', fields.stock);
    if (fields.order_qty !== undefined) formData.append('order_qty', fields.order_qty);
    if (fields.remarks !== undefined) formData.append('remarks', fields.remarks);
    if (force_new_image !== undefined) {
      formData.append('force_new_image', force_new_image ? 'true' : 'false');
    }
    if (imageFile) formData.append('image', imageFile);
    
    return api.put(`/products/${id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Delete product
  deleteProduct: (id) => {
    return api.delete(`/products/${id}`);
  },

  // Quick update order quantity
  updateOrderQty: (id, orderQty) => {
    return api.patch(`/products/${id}/order-qty`, { order_qty: orderQty });
  },

  // Get cart (products with order_qty > 0)
  getCart: (params = {}) => {
    return api.get('/cart', { params });
  },

  // Reset all products
  resetAll: () => {
    return api.post('/products/reset');
  },

  // Import Excel
  importExcel: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Import PDF
  importPDF: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export default api;

