import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productAPI, resolveImageUrl } from '../api';

function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [isEditingProductId, setIsEditingProductId] = useState(false);
  const [productIdInput, setProductIdInput] = useState('');
  const [productIdChange, setProductIdChange] = useState(null);
  const [showProductIdConfirm, setShowProductIdConfirm] = useState(false);
  const [productIdUpdating, setProductIdUpdating] = useState(false);
  const [formData, setFormData] = useState({
    stock: 0,
    order_qty: 0,
    remarks: '',
    name: '',
    brand: '',
    price: 0,
  });
  const [forceNewImage, setForceNewImage] = useState(true);

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await productAPI.getProduct(id);
        const prod = response.data;
        setProduct(prod);
        setFormData({
          stock: prod.stock,
          order_qty: prod.order_qty,
          remarks: prod.remarks || '',
          name: prod.name,
          brand: prod.brand || '',
          price: prod.price,
        });
        setProductIdInput(prod.product_id || '');
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch product');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'stock' || name === 'order_qty' || name === 'price' 
        ? (value === '' ? 0 : parseFloat(value) || 0)
        : value,
    }));
  };

  const preventScrollAdjustment = (e) => {
    // Prevent scroll wheel from mutating the numeric value before defocusing
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.blur();
  };

  const processImageFile = (file) => {
    if (!file) {
      setImageFile(null);
      setImagePreview(null);
      setForceNewImage(true);
      return;
    }

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('Please select a valid image file (JPEG, PNG, GIF, or WebP)');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Image file size must be less than 5MB');
      return;
    }

    setImageFile(file);
    setForceNewImage(true);
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    processImageFile(file);
    if (!file) {
      e.target.value = '';
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processImageFile(files[0]);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...formData };
      if (imageFile) {
        payload.force_new_image = forceNewImage;
      }
      await productAPI.updateProduct(id, payload, imageFile);
      alert('Product updated successfully');
      navigate('/');
    } catch (err) {
      alert('Failed to update product: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this product permanently? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    try {
      await productAPI.deleteProduct(id);
      alert('Product deleted successfully');
      navigate('/');
    } catch (err) {
      alert('Failed to delete product: ' + (err.response?.data?.detail || err.message));
      setDeleting(false);
    }
  };

  const startProductIdEdit = () => {
    if (!product) return;
    setIsEditingProductId(true);
    setProductIdInput(product.product_id || '');
  };

  const handleProductIdSaveAttempt = () => {
    if (!product) return;
    const trimmed = productIdInput.trim();
    if (!trimmed) {
      alert('Product ID cannot be blank');
      return;
    }
    if (trimmed === product.product_id) {
      alert('Product ID is unchanged');
      return;
    }
    setProductIdChange({
      previous: product.product_id,
      next: trimmed,
    });
    setShowProductIdConfirm(true);
  };

  const handleCancelProductIdEdit = () => {
    setIsEditingProductId(false);
    setProductIdInput(product?.product_id || '');
  };

  const handleCancelProductIdConfirm = () => {
    setShowProductIdConfirm(false);
    setProductIdChange(null);
  };

  const handleConfirmProductIdUpdate = async () => {
    if (!productIdChange?.next) {
      return;
    }
    setProductIdUpdating(true);
    try {
      await productAPI.updateProduct(id, { product_id: productIdChange.next });
      setProduct(prev => (prev ? { ...prev, product_id: productIdChange.next } : prev));
      setProductIdInput(productIdChange.next);
      setIsEditingProductId(false);
      setShowProductIdConfirm(false);
      setProductIdChange(null);
      alert('Product ID updated successfully');
    } catch (err) {
      alert('Failed to update product ID: ' + (err.response?.data?.detail || err.message));
    } finally {
      setProductIdUpdating(false);
    }
  };

  if (loading) {
    return <div style={styles.loading}>Loading product...</div>;
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Error: {error}</div>
        <button onClick={() => navigate('/')} style={styles.backButton}>
          Back to Products
        </button>
      </div>
    );
  }

  if (!product) {
    return <div style={styles.error}>Product not found</div>;
  }

  return (
    <div style={styles.container}>
      <button onClick={() => navigate('/')} style={styles.backButton}>
        ← Back to Products
      </button>

      <div style={styles.content} className="product-detail-content">
        <div style={styles.imageSection}>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => {
              if (!imageFile) {
                const fileInput = document.querySelector('#product-detail-image-input');
                if (fileInput) fileInput.click();
              }
            }}
            style={{
              ...styles.imageDropZone,
              ...(isDragging ? styles.imageDropZoneActive : {}),
              cursor: imageFile ? 'default' : 'pointer',
            }}
          >
            <img
              src={imagePreview || resolveImageUrl(product.image_url)}
              alt={product.name}
              style={styles.image}
              onError={(e) => {
                e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23ddd" width="400" height="400"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="20" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
              }}
            />
            {isDragging && (
              <div style={styles.dragOverlay}>
                <p style={styles.dragOverlayText}>Drop image here to replace</p>
              </div>
            )}
          </div>
          <div style={styles.imageUploadSection}>
            <label style={styles.imageUploadLabel}>
              {imageFile ? 'Image Selected' : 'Replace Image'}
              <input
                id="product-detail-image-input"
                type="file"
                accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                onChange={handleImageChange}
                style={styles.imageFileInput}
              />
            </label>
            {imageFile && (
              <>
                <p style={styles.imageFileInfo}>New image: {imageFile.name}</p>
                <label style={styles.forceImageToggle}>
                  <input
                    type="checkbox"
                    checked={forceNewImage}
                    onChange={(e) => setForceNewImage(e.target.checked)}
                    style={styles.forceImageCheckbox}
                  />
                  <span>
                    Always save this uploaded image (skip similarity dedupe)
                  </span>
                </label>
                <p style={styles.forceImageHint}>
                  Uncheck if you want the app to reuse an existing match automatically.
                </p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setImageFile(null);
                    setImagePreview(null);
                    setForceNewImage(true);
                    const fileInput = document.querySelector('#product-detail-image-input');
                    if (fileInput) fileInput.value = '';
                  }}
                  style={styles.removeImageButton}
                >
                  Cancel Replacement
                </button>
              </>
            )}
            <p style={styles.dragHint}>Or drag & drop an image above</p>
          </div>
        </div>

        <div style={styles.detailsSection}>
          <h1 style={styles.name}>{product.name}</h1>
          <div style={styles.productIdRow}>
            <p style={styles.productId}>Product ID: {product.product_id}</p>
            {!isEditingProductId && (
              <button
                type="button"
                onClick={startProductIdEdit}
                style={styles.productIdButton}
              >
                Update Product ID
              </button>
            )}
          </div>
          {isEditingProductId && (
            <div style={styles.productIdEdit}>
              <input
                type="text"
                value={productIdInput}
                onChange={(e) => setProductIdInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleProductIdSaveAttempt();
                  }
                }}
                style={styles.productIdInput}
                placeholder="Enter new product ID"
              />
              <div style={styles.productIdEditButtons}>
                <button
                  type="button"
                  onClick={handleProductIdSaveAttempt}
                  style={styles.productIdReviewButton}
                >
                  Save New ID
                </button>
                <button
                  type="button"
                  onClick={handleCancelProductIdEdit}
                  style={styles.productIdEditCancelButton}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          {product.brand && <p style={styles.brand}>Brand: {product.brand}</p>}

          <div style={styles.form}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Stock</label>
              <input
                type="number"
                name="stock"
                value={formData.stock}
                onChange={handleChange}
                onWheel={preventScrollAdjustment}
                min="0"
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Order Quantity</label>
              <input
                type="number"
                name="order_qty"
                value={formData.order_qty}
                onChange={handleChange}
                onWheel={preventScrollAdjustment}
                min="0"
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Brand</label>
              <input
                type="text"
                name="brand"
                value={formData.brand}
                onChange={handleChange}
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Price</label>
              <input
                type="number"
                name="price"
                value={formData.price}
                onChange={handleChange}
                onWheel={preventScrollAdjustment}
                min="0"
                step="0.01"
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Remarks</label>
              <textarea
                name="remarks"
                value={formData.remarks}
                onChange={handleChange}
                rows="4"
                style={styles.textarea}
                placeholder="Add any notes or comments..."
              />
            </div>

            <div style={styles.buttonGroup}>
              <button onClick={handleSave} disabled={saving || deleting} style={styles.saveButton}>
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button onClick={() => navigate('/')} style={styles.cancelButton}>
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                style={{
                  ...styles.deleteButton,
                  ...(deleting ? { opacity: 0.7, cursor: 'not-allowed' } : {}),
                }}
              >
                {deleting ? 'Deleting...' : 'Delete Product'}
              </button>
            </div>
          </div>
        </div>
      </div>
      {showProductIdConfirm && productIdChange && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <h3 style={styles.modalTitle}>Confirm Product ID Update</h3>
            <div style={styles.modalIdCompare}>
              <div style={styles.modalIdCard}>
                <p style={styles.modalIdLabel}>Previous ID</p>
                <p style={styles.modalIdValue}>{productIdChange.previous}</p>
              </div>
              <span style={styles.modalArrow}>→</span>
              <div style={styles.modalIdCard}>
                <p style={styles.modalIdLabel}>New ID</p>
                <p style={styles.modalIdValue}>{productIdChange.next}</p>
              </div>
            </div>
            <p style={styles.modalHint}>
              Updating this value changes references to this product everywhere in the app.
            </p>
            <div style={styles.modalButtons}>
              <button
                type="button"
                onClick={handleConfirmProductIdUpdate}
                disabled={productIdUpdating}
                style={{
                  ...styles.modalConfirmButton,
                  ...(productIdUpdating ? { opacity: 0.7, cursor: 'not-allowed' } : {}),
                }}
              >
                {productIdUpdating ? 'Updating...' : 'Confirm Update'}
              </button>
              <button
                type="button"
                onClick={handleCancelProductIdConfirm}
                disabled={productIdUpdating}
                style={styles.modalCancelButton}
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
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
  backButton: {
    marginBottom: '2rem',
    padding: '0.5rem 1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    color: '#555555',
  },
  content: {
    display: 'grid',
    gridTemplateColumns: '1fr 2fr',
    gap: '2rem',
  },
  imageSection: {
    width: '100%',
  },
  imageDropZone: {
    position: 'relative',
    width: '100%',
    borderRadius: '8px',
    overflow: 'hidden',
    transition: 'all 0.3s ease',
  },
  imageDropZoneActive: {
    border: '3px dashed #3498db',
    backgroundColor: '#e8f4f8',
  },
  image: {
    width: '100%',
    aspectRatio: '1',
    objectFit: 'contain',
    borderRadius: '8px',
    backgroundColor: '#f5f5f5',
    display: 'block',
  },
  dragOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(52, 152, 219, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '8px',
    zIndex: 10,
  },
  dragOverlayText: {
    color: 'white',
    fontSize: '1.2rem',
    fontWeight: '600',
    textAlign: 'center',
  },
  imageUploadSection: {
    marginTop: '1rem',
    textAlign: 'center',
  },
  imageUploadLabel: {
    display: 'inline-block',
    padding: '0.5rem 1rem',
    border: '1px solid #3498db',
    borderRadius: '4px',
    backgroundColor: '#3498db',
    color: 'white',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
    transition: 'background-color 0.2s',
  },
  imageFileInput: {
    display: 'none',
  },
  imageFileInfo: {
    marginTop: '0.5rem',
    fontSize: '0.85rem',
    color: '#27ae60',
  },
  forceImageToggle: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginTop: '0.5rem',
    fontSize: '0.85rem',
    color: '#2c3e50',
  },
  forceImageCheckbox: {
    width: '16px',
    height: '16px',
  },
  forceImageHint: {
    marginTop: '0.25rem',
    fontSize: '0.75rem',
    color: '#7f8c8d',
  },
  removeImageButton: {
    marginTop: '0.5rem',
    padding: '0.4rem 0.8rem',
    border: '1px solid #e74c3c',
    borderRadius: '4px',
    backgroundColor: 'white',
    color: '#e74c3c',
    cursor: 'pointer',
    fontSize: '0.85rem',
    transition: 'background-color 0.2s',
  },
  dragHint: {
    marginTop: '0.5rem',
    fontSize: '0.8rem',
    color: '#7f8c8d',
    fontStyle: 'italic',
  },
  detailsSection: {
    display: 'flex',
    flexDirection: 'column',
  },
  name: {
    fontSize: '2rem',
    marginBottom: '0.5rem',
    color: '#2c3e50',
  },
  productId: {
    fontSize: '1rem',
    color: '#7f8c8d',
    marginBottom: '0.5rem',
  },
  productIdRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
    marginBottom: '0.5rem',
  },
  productIdButton: {
    padding: '0.35rem 0.8rem',
    borderRadius: '4px',
    border: '1px solid #2980b9',
    backgroundColor: '#2980b9',
    color: 'white',
    fontSize: '0.9rem',
    cursor: 'pointer',
  },
  productIdEdit: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  productIdInput: {
    padding: '0.6rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  productIdEditButtons: {
    display: 'flex',
    gap: '0.5rem',
  },
  productIdReviewButton: {
    padding: '0.5rem 1rem',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#27ae60',
    color: 'white',
    cursor: 'pointer',
    fontWeight: '600',
  },
  productIdEditCancelButton: {
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    border: '1px solid #ddd',
    backgroundColor: 'white',
    color: '#555555',
    cursor: 'pointer',
  },
  brand: {
    fontSize: '1rem',
    color: '#7f8c8d',
    marginBottom: '2rem',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '1rem',
    fontWeight: '600',
    color: '#34495e',
  },
  input: {
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  textarea: {
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: 'inherit',
    resize: 'vertical',
  },
  buttonGroup: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1rem',
  },
  saveButton: {
    padding: '0.75rem 2rem',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#3498db',
    color: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
  },
  cancelButton: {
    padding: '0.75rem 2rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    color: '#555555',
  },
  deleteButton: {
    padding: '0.75rem 2rem',
    border: '1px solid #e74c3c',
    borderRadius: '4px',
    backgroundColor: '#e74c3c',
    color: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
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
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.45)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem',
    zIndex: 1000,
  },
  modalContent: {
    width: '100%',
    maxWidth: '420px',
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 15px 35px rgba(0,0,0,0.2)',
  },
  modalTitle: {
    margin: 0,
    marginBottom: '0.75rem',
    fontSize: '1.25rem',
    color: '#2c3e50',
  },
  modalText: {
    margin: 0,
    marginBottom: '0.5rem',
    fontSize: '1rem',
    color: '#34495e',
  },
  modalHint: {
    margin: 0,
    marginBottom: '1rem',
    fontSize: '0.9rem',
    color: '#7f8c8d',
  },
  modalIdCompare: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.75rem',
    marginBottom: '1rem',
  },
  modalIdCard: {
    flex: 1,
    padding: '0.75rem',
    borderRadius: '6px',
    border: '1px solid #ecf0f1',
    backgroundColor: '#fefefe',
  },
  modalIdLabel: {
    margin: 0,
    fontSize: '0.75rem',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: '#7f8c8d',
  },
  modalIdValue: {
    margin: '0.25rem 0 0',
    fontSize: '1.1rem',
    fontWeight: '600',
    color: '#2c3e50',
    wordBreak: 'break-word',
  },
  modalArrow: {
    fontSize: '1.4rem',
    color: '#95a5a6',
    fontWeight: '600',
  },
  modalButtons: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '0.75rem',
  },
  modalConfirmButton: {
    padding: '0.6rem 1.2rem',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#27ae60',
    color: 'white',
    fontWeight: '600',
    cursor: 'pointer',
  },
  modalCancelButton: {
    padding: '0.6rem 1.2rem',
    borderRadius: '4px',
    border: '1px solid #ddd',
    backgroundColor: 'white',
    color: '#555555',
    cursor: 'pointer',
  },
};

export default ProductDetail;

