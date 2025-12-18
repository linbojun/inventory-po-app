import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { productAPI } from '../api';

function Import() {
  const navigate = useNavigate();
  const [excelFile, setExcelFile] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showManualForm, setShowManualForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [manualFormData, setManualFormData] = useState({
    product_id: '',
    name: '',
    brand: '',
    price: 0,
    stock: 0,
    order_qty: 0,
    remarks: '',
  });
  const [manualError, setManualError] = useState('');
  const [manualForceNewImage, setManualForceNewImage] = useState(true);
  const emptyProductIdCheck = () => ({
    checking: false,
    duplicate: false,
    message: '',
  });
  const [productIdCheck, setProductIdCheck] = useState(() => emptyProductIdCheck());
  const resetProductIdCheck = () => setProductIdCheck(emptyProductIdCheck());

  useEffect(() => {
    if (!showManualForm) {
      resetProductIdCheck();
      return;
    }

    const trimmed = manualFormData.product_id.trim();
    if (!trimmed) {
      resetProductIdCheck();
      return;
    }

    let cancelled = false;
    setProductIdCheck(prev => ({
      ...prev,
      checking: true,
      message: '',
    }));

    const timeoutId = setTimeout(async () => {
      try {
        const response = await productAPI.getProducts({ search: trimmed, page_size: 1 });
        if (cancelled) return;
        const duplicate = response.data.items.some(
          (p) => (p.product_id || '').toLowerCase() === trimmed.toLowerCase()
        );
        setProductIdCheck({
          checking: false,
          duplicate,
          message: duplicate ? 'Product ID already exists. Please choose another ID.' : '',
        });
      } catch (err) {
        if (cancelled) return;
        setProductIdCheck({
          checking: false,
          duplicate: false,
          message: 'Unable to verify product ID right now.',
        });
      }
    }, 350);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [manualFormData.product_id, showManualForm]);

  const handleExcelChange = (e) => {
    setExcelFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handlePdfChange = (e) => {
    setPdfFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handleExcelImport = async () => {
    if (!excelFile) {
      alert('Please select an Excel file');
      return;
    }

    setImporting(true);
    setError(null);
    setResult(null);

    try {
      const response = await productAPI.importExcel(excelFile);
      setResult(response.data);
      setExcelFile(null);
      // Reset file input
      document.getElementById('excel-file').value = '';
      alert(`Import completed: ${response.data.created} created, ${response.data.updated} updated, ${response.data.failed} failed`);
      if (response.data.failed > 0 && response.data.errors.length > 0) {
        console.error('Import errors:', response.data.errors);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to import Excel file');
      alert('Import failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setImporting(false);
    }
  };

  const handlePdfImport = async () => {
    if (!pdfFile) {
      alert('Please select a PDF file');
      return;
    }

    setImporting(true);
    setError(null);
    setResult(null);

    try {
      const response = await productAPI.importPDF(pdfFile);
      setResult(response.data);
      setPdfFile(null);
      document.getElementById('pdf-file').value = '';
      alert(`Import completed: ${response.data.created} created, ${response.data.updated} updated, ${response.data.failed} failed`);
      if (response.data.failed > 0 && response.data.errors.length > 0) {
        console.error('Import errors:', response.data.errors);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to import PDF file');
      alert('Import failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setImporting(false);
    }
  };

  const handleManualFormChange = (e) => {
    const { name, value } = e.target;
    setManualFormData(prev => ({
      ...prev,
      [name]: name === 'price' || name === 'stock' || name === 'order_qty'
        ? (value === '' ? 0 : parseFloat(value) || 0)
        : value,
    }));
    setManualError('');
  };

  const preventScrollAdjustment = (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.blur();
  };

  const processImageFile = (file) => {
    if (!file) {
      setImageFile(null);
      setManualForceNewImage(true);
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
    setManualForceNewImage(true);
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
      // Also update the file input if it exists
      const fileInput = document.getElementById('product-image-input');
      if (fileInput) {
        // Create a new FileList-like object (we can't directly set files, so we'll just process the dropped file)
        // The file input will be updated when the form is submitted
      }
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    const trimmedProductId = manualFormData.product_id.trim();
    const trimmedName = manualFormData.name.trim();

    if (!trimmedProductId || !trimmedName) {
      const message = 'Product ID and Name are required';
      setManualError(message);
      alert(message);
      return;
    }

    setError(null);
    setManualError('');

    if (productIdCheck.checking) {
      const message = 'Please wait until the product ID check finishes.';
      setManualError(message);
      alert(message);
      return;
    }

    if (productIdCheck.duplicate) {
      const message = 'Product ID already exists. Please use a different ID.';
      setManualError(message);
      alert(message);
      return;
    }

    if (
      !productIdCheck.duplicate &&
      (productIdCheck.message || '').toLowerCase().includes('unable to verify')
    ) {
      const message = 'Unable to verify product ID uniqueness. Please try again.';
      setManualError(message);
      alert(message);
      return;
    }

    try {
      const response = await productAPI.getProducts({ search: trimmedProductId });
      const exists = response.data.items.some(
        (p) => p.product_id.toLowerCase() === trimmedProductId.toLowerCase()
      );
      if (exists) {
        const message = 'Product ID already exists. Please use a different ID.';
        setManualError(message);
        alert(message);
        return;
      }
    } catch (checkErr) {
      const message = 'Unable to verify product ID uniqueness. Please try again.';
      setManualError(message);
      alert(message + ' ' + (checkErr.response?.data?.detail || checkErr.message));
      return;
    }

    setCreating(true);

    const payload = {
      ...manualFormData,
      product_id: trimmedProductId,
      name: trimmedName,
    };
    if (imageFile) {
      payload.force_new_image = manualForceNewImage;
    }

    try {
      await productAPI.createProduct(payload, imageFile);
      alert('Product created successfully!');
      setManualFormData({
        product_id: '',
        name: '',
        brand: '',
        price: 0,
        stock: 0,
        order_qty: 0,
        remarks: '',
      });
      setImageFile(null);
      setManualForceNewImage(true);
      setManualError('');
      resetProductIdCheck();
      // Reset file input
      const fileInput = document.getElementById('product-image-input');
      if (fileInput) fileInput.value = '';
      setShowManualForm(false);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create product');
      setManualError(err.response?.data?.detail || err.message || 'Failed to create product');
      alert('Failed to create product: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Import Products</h1>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Manual Input</h2>
        <p style={styles.description}>
          Create a new product manually by filling out the form below.
        </p>
        {!showManualForm ? (
          <button
            onClick={() => {
              setManualError('');
              setError(null);
              resetProductIdCheck();
              setManualForceNewImage(true);
              setShowManualForm(true);
            }}
            style={styles.toggleButton}
          >
            Show New Product Form
          </button>
        ) : (
          <>
            {manualError && (
              <div style={styles.inlineError}>
                {manualError}
              </div>
            )}
            <form onSubmit={handleManualSubmit} style={styles.manualForm}>
            <div style={styles.formRow}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Product ID *</label>
                <input
                  type="text"
                  name="product_id"
                  value={manualFormData.product_id}
                  onChange={handleManualFormChange}
                  required
                  style={styles.input}
                />
                {productIdCheck.checking && manualFormData.product_id.trim() && (
                  <span style={styles.fieldHint}>Checking availability...</span>
                )}
                {!productIdCheck.checking && productIdCheck.message && (
                  <span
                    style={{
                      ...styles.fieldHint,
                      color: productIdCheck.duplicate ? '#e74c3c' : '#e67e22',
                    }}
                  >
                    {productIdCheck.message}
                  </span>
                )}
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Name *</label>
                <input
                  type="text"
                  name="name"
                  value={manualFormData.name}
                  onChange={handleManualFormChange}
                  required
                  style={styles.input}
                />
              </div>
            </div>
            <div style={styles.formRow}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Brand</label>
                <input
                  type="text"
                  name="brand"
                  value={manualFormData.brand}
                  onChange={handleManualFormChange}
                  style={styles.input}
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Price</label>
                <input
                  type="number"
                  name="price"
                  value={manualFormData.price}
                  onChange={handleManualFormChange}
                  onWheel={preventScrollAdjustment}
                  min="0"
                  step="0.01"
                  style={styles.input}
                />
              </div>
            </div>
            <div style={styles.formRow}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Stock</label>
                <input
                  type="number"
                  name="stock"
                  value={manualFormData.stock}
                  onChange={handleManualFormChange}
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
                  value={manualFormData.order_qty}
                  onChange={handleManualFormChange}
                  onWheel={preventScrollAdjustment}
                  min="0"
                  style={styles.input}
                />
              </div>
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Product Image</label>
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => {
                  if (!imageFile) {
                    const fileInput = document.getElementById('product-image-input');
                    if (fileInput) fileInput.click();
                  }
                }}
                style={{
                  ...styles.dropZone,
                  ...(isDragging ? styles.dropZoneActive : {}),
                }}
              >
                {imageFile ? (
                  <div style={styles.imagePreview}>
                    <p style={styles.imagePreviewText}>Selected: {imageFile.name}</p>
                    <img
                      src={URL.createObjectURL(imageFile)}
                      alt="Preview"
                      style={styles.previewImage}
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setImageFile(null);
                        setManualForceNewImage(true);
                        const fileInput = document.getElementById('product-image-input');
                        if (fileInput) fileInput.value = '';
                      }}
                      style={styles.removeImageButton}
                    >
                      Remove Image
                    </button>
                  </div>
                ) : (
                  <div style={styles.dropZoneContent}>
                    <p style={styles.dropZoneText}>
                      {isDragging ? 'Drop image here' : 'Drag & drop image here or click to browse'}
                    </p>
                    <input
                      id="product-image-input"
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                      onChange={handleImageChange}
                      style={styles.hiddenFileInput}
                    />
                  </div>
                )}
              </div>
              <div style={styles.forceImageWrapper}>
                <label style={styles.forceImageToggle}>
                  <input
                    type="checkbox"
                    checked={manualForceNewImage}
                    onChange={(e) => setManualForceNewImage(e.target.checked)}
                    disabled={!imageFile}
                    style={styles.forceImageCheckbox}
                  />
                  <span>Always save the uploaded file (skip similarity dedupe)</span>
                </label>
                <p style={styles.forceImageHint}>
                  Disable only if you want the server to reuse an existing matching image automatically.
                </p>
              </div>
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Remarks</label>
              <textarea
                name="remarks"
                value={manualFormData.remarks}
                onChange={handleManualFormChange}
                rows="3"
                style={styles.textarea}
                placeholder="Add any notes or comments..."
              />
            </div>
            <div style={styles.formActions}>
              <button
                type="submit"
                disabled={creating || productIdCheck.duplicate || productIdCheck.checking}
                style={{
                  ...styles.submitButton,
                  ...((creating || productIdCheck.duplicate || productIdCheck.checking) ? styles.disabledButton : {}),
                }}
              >
                {creating ? 'Creating...' : 'Create Product'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowManualForm(false);
                  setManualFormData({
                    product_id: '',
                    name: '',
                    brand: '',
                    price: 0,
                    stock: 0,
                    order_qty: 0,
                    remarks: '',
                  });
                  setImageFile(null);
                setManualForceNewImage(true);
                  setManualError('');
                  resetProductIdCheck();
                  const fileInput = document.getElementById('product-image-input');
                  if (fileInput) fileInput.value = '';
                }}
                style={styles.cancelButton}
              >
                Cancel
              </button>
            </div>
            </form>
          </>
        )}
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Excel Import</h2>
        <p style={styles.description}>
          Upload an Excel file with product data. Expected columns: product_id, name, brand, price, stock, order_qty, image_url, remarks
        </p>
        <div style={styles.uploadArea}>
          <input
            id="excel-file"
            type="file"
            accept=".xlsx,.xls"
            onChange={handleExcelChange}
            style={styles.fileInput}
          />
          <button
            onClick={handleExcelImport}
            disabled={!excelFile || importing}
            style={styles.importButton}
          >
            {importing ? 'Importing...' : 'Import Excel'}
          </button>
        </div>
      </div>

      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>PDF Import (Best Effort)</h2>
        <p style={styles.description}>
          Upload a PDF file with product data. Only specific PDF formats are supported. If parsing fails, you'll receive an error message.
        </p>
        <div style={styles.uploadArea}>
          <input
            id="pdf-file"
            type="file"
            accept=".pdf"
            onChange={handlePdfChange}
            style={styles.fileInput}
          />
          <button
            onClick={handlePdfImport}
            disabled={!pdfFile || importing}
            style={styles.importButton}
          >
            {importing ? 'Importing...' : 'Import PDF'}
          </button>
        </div>
      </div>

      {result && (
        <div style={styles.result}>
          <h3>Import Result</h3>
          <p>Created: {result.created}</p>
          <p>Updated: {result.updated}</p>
          <p>Failed: {result.failed}</p>
          {Array.isArray(result.skipped_existing) && result.skipped_existing.length > 0 && (
            <div style={styles.skipped}>
              <h4>Skipped (already existed in DB):</h4>
              <ul style={styles.skippedList}>
                {result.skipped_existing.map((item, idx) => {
                  const details = [];
                  if (item.existing_name) {
                    details.push(`Existing: ${item.existing_name}`);
                  }
                  if (item.incoming_name && item.incoming_name !== item.existing_name) {
                    details.push(`Incoming: ${item.incoming_name}`);
                  }
                  return (
                    <li key={`${item.product_id}-${idx}`} style={styles.skippedListItem}>
                      <div>
                        <strong>{item.product_id}</strong>
                        {details.length > 0 && (
                          <span style={styles.skippedMeta}> – {details.join(' | ')}</span>
                        )}
                      </div>
                      {item.reason && (
                        <div style={styles.skippedReason}>{item.reason}</div>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          {result.errors.length > 0 && (
            <div style={styles.errors}>
              <h4>Errors:</h4>
              <ul>
                {result.errors.map((err, idx) => (
                  <li key={idx}>Row {err.row}: {err.error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={styles.error}>
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      <div style={styles.actions}>
        <button onClick={() => navigate('/')} style={styles.backButton}>
          Back to Products
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '2rem 1rem',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '2rem',
    color: '#2c3e50',
  },
  section: {
    marginBottom: '3rem',
    padding: '1.5rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    backgroundColor: 'white',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    marginBottom: '1rem',
    color: '#34495e',
  },
  description: {
    marginBottom: '1rem',
    color: '#7f8c8d',
    lineHeight: '1.6',
  },
  uploadArea: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  fileInput: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  importButton: {
    padding: '0.75rem 2rem',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#3498db',
    color: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    alignSelf: 'flex-start',
  },
  result: {
    marginTop: '2rem',
    padding: '1.5rem',
    backgroundColor: '#d4edda',
    border: '1px solid #c3e6cb',
    borderRadius: '8px',
  },
  errors: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f8d7da',
    border: '1px solid #f5c6cb',
    borderRadius: '4px',
  },
  skipped: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#fff3cd',
    border: '1px solid #ffeeba',
    borderRadius: '4px',
  },
  skippedList: {
    margin: 0,
    paddingLeft: '1.25rem',
  },
  skippedListItem: {
    marginBottom: '0.35rem',
    color: '#8a6d3b',
  },
  skippedMeta: {
    marginLeft: '0.35rem',
    color: '#6c4a12',
    fontSize: '0.95rem',
  },
  skippedReason: {
    marginLeft: '1.5rem',
    fontSize: '0.9rem',
    color: '#a94442',
  },
  error: {
    marginTop: '2rem',
    padding: '1.5rem',
    backgroundColor: '#f8d7da',
    border: '1px solid #f5c6cb',
    borderRadius: '8px',
    color: '#721c24',
  },
  actions: {
    marginTop: '2rem',
  },
  backButton: {
    padding: '0.75rem 2rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    color: '#555555',
  },
  toggleButton: {
    padding: '0.75rem 2rem',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#3498db',
    color: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
  },
  manualForm: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  inlineError: {
    marginBottom: '1rem',
    padding: '0.75rem 1rem',
    backgroundColor: '#fdecea',
    border: '1px solid #f5c6cb',
    borderRadius: '4px',
    color: '#a94442',
    fontSize: '0.9rem',
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  fieldHint: {
    fontSize: '0.8rem',
    color: '#7f8c8d',
  },
  label: {
    fontSize: '0.9rem',
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
  formActions: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1rem',
  },
  submitButton: {
    padding: '0.75rem 2rem',
    border: 'none',
    borderRadius: '4px',
    backgroundColor: '#27ae60',
    color: 'white',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  cancelButton: {
    padding: '0.75rem 2rem',
    border: '1px solid #2f3640',
    borderRadius: '4px',
    backgroundColor: '#4a4a4a',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    color: 'white',
  },
  dropZone: {
    marginTop: '0.5rem',
    padding: '2rem',
    border: '2px dashed #ddd',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    minHeight: '150px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dropZoneActive: {
    borderColor: '#3498db',
    backgroundColor: '#e8f4f8',
    borderStyle: 'solid',
  },
  dropZoneContent: {
    width: '100%',
  },
  dropZoneText: {
    fontSize: '0.9rem',
    color: '#7f8c8d',
    marginBottom: '0.5rem',
  },
  hiddenFileInput: {
    display: 'none',
  },
  imagePreview: {
    width: '100%',
    textAlign: 'center',
  },
  imagePreviewText: {
    fontSize: '0.85rem',
    color: '#7f8c8d',
    marginBottom: '0.5rem',
  },
  previewImage: {
    maxWidth: '100%',
    maxHeight: '300px',
    borderRadius: '4px',
    objectFit: 'contain',
    backgroundColor: '#f5f5f5',
    marginBottom: '0.5rem',
  },
  removeImageButton: {
    padding: '0.5rem 1rem',
    border: '1px solid #e74c3c',
    borderRadius: '4px',
    backgroundColor: 'white',
    color: '#e74c3c',
    cursor: 'pointer',
    fontSize: '0.85rem',
    transition: 'background-color 0.2s',
  },
  forceImageWrapper: {
    marginTop: '0.5rem',
  },
  forceImageToggle: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
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
};

export default Import;

