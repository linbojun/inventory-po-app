import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

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
    formData.append('product_id', data.product_id);
    formData.append('name', data.name);
    if (data.brand) formData.append('brand', data.brand);
    if (data.price !== undefined) formData.append('price', data.price);
    if (data.stock !== undefined) formData.append('stock', data.stock);
    if (data.order_qty !== undefined) formData.append('order_qty', data.order_qty);
    if (data.remarks) formData.append('remarks', data.remarks);
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
    if (data.name !== undefined) formData.append('name', data.name);
    if (data.brand !== undefined) formData.append('brand', data.brand);
    if (data.price !== undefined) formData.append('price', data.price);
    if (data.stock !== undefined) formData.append('stock', data.stock);
    if (data.order_qty !== undefined) formData.append('order_qty', data.order_qty);
    if (data.remarks !== undefined) formData.append('remarks', data.remarks);
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

