from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List, Dict, Tuple
import os
import shutil
from pathlib import Path
import uuid

from app.database import get_db, engine, Base, settings, ensure_schema_updates
from app.image_similarity import (
    compute_phash,
    extract_orb_features,
    find_best_image_match,
    invalidate_orb_cache,
)
from app.storage import is_r2_enabled, put_image_object, delete_image
from app.models import Product
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    OrderQtyUpdate, ImportSummary, ResetResponse
)
from app.importers import parse_excel, parse_pdf

# Create tables and patch legacy schema
Base.metadata.create_all(bind=engine)
ensure_schema_updates()

app = FastAPI(title="Inventory PO API", version="1.0.0")

# Configure CORS origins:
# - Defaults include common dev servers AND the production Vercel domain.
# - CORS_ALLOW_ORIGINS can override the list (comma separated).
# - CORS_EXTRA_ORIGINS appends values without losing the defaults.
DEFAULT_CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://inventory-po-app.vercel.app",
]


def _split_origins(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part and part.strip()]


def _dedupe(origins: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for origin in origins:
        if origin and origin not in seen:
            deduped.append(origin)
            seen.add(origin)
    return deduped


def _get_cors_allow_origins() -> List[str]:
    configured = _split_origins(os.getenv("CORS_ALLOW_ORIGINS", ""))
    extras = _split_origins(os.getenv("CORS_EXTRA_ORIGINS", ""))

    if not configured:
        origins = list(DEFAULT_CORS_ORIGINS)
    else:
        origins = configured

    if extras:
        origins.extend(extras)

    return _dedupe(origins)


# Allow a regex-based fallback for common hosting providers.
# - ENABLE_VERCEL_PREVIEW_CORS=true (default) keeps *.vercel.app previews working
# - Set CORS_ALLOW_ORIGIN_REGEX to override entirely
def _get_cors_allow_origin_regex() -> Optional[str]:
    explicit_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip()
    if explicit_regex:
        return explicit_regex

    enable_vercel_regex = os.getenv("ENABLE_VERCEL_PREVIEW_CORS", "true").lower() in {"1", "true", "yes"}
    if enable_vercel_regex:
        # Default dev + Vercel deployments (preview + production).
        # - localhost with optional port
        # - any *.vercel.app
        return r"^http://localhost(:\d+)?$|^https://.*\.vercel\.app$"

    return None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_allow_origins(),
    allow_origin_regex=_get_cors_allow_origin_regex(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images (local dev storage)
os.makedirs(settings.image_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.image_dir), name="static")


def _allowed_image_extension(filename: str) -> str:
    file_ext = Path(filename).suffix.lower()
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image format. Allowed: {', '.join(sorted(allowed_extensions))}",
        )
    return file_ext


def save_uploaded_image(file_bytes: bytes, original_filename: str, product_id: str, content_type: Optional[str]) -> Optional[str]:
    """
    Save uploaded image either to filesystem (dev) or R2 (prod) and return the URL/path.
    Returns None if no file was provided.
    """
    if not original_filename:
        return None
    
    # Get file extension
    file_ext = _allowed_image_extension(original_filename)
    
    # Generate unique filename: product_id_timestamp_uuid.ext
    unique_filename = f"{product_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    
    try:
        if is_r2_enabled():
            key = f"images/{unique_filename}"
            return put_image_object(key=key, data=file_bytes or b"", content_type=content_type)

        # Local dev storage
        file_path = os.path.join(settings.image_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes or b"")
        return f"/static/{unique_filename}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

def delete_image_file(image_path: Optional[str]):
    """Delete image from storage if it exists"""
    if not image_path:
        return
    try:
        delete_image(image_path)
    finally:
        invalidate_orb_cache(image_path)


def delete_image_if_orphan(db: Session, image_path: Optional[str], exclude_product_id: Optional[int] = None):
    """Delete image only when no other product references it."""
    if not image_path:
        return

    query = db.query(Product).filter(Product.image_url == image_path)
    if exclude_product_id is not None:
        query = query.filter(Product.id != exclude_product_id)

    if query.first() is None:
        delete_image_file(image_path)


async def process_uploaded_image(
    db: Session,
    image_file: UploadFile,
    product_identifier: str,
    exclude_product_id: Optional[int] = None,
    force_new_image: bool = False,
) -> Tuple[Optional[str], Optional[str], bool]:
    """Process upload with optional similarity deduplication."""
    if not image_file or not image_file.filename:
        return None, None, False

    file_bytes = await image_file.read()
    if file_bytes is None:
        file_bytes = b""
    # Validate extension early
    _allowed_image_extension(image_file.filename)

    candidate_hash = compute_phash(file_bytes)

    if force_new_image:
        saved_path = save_uploaded_image(
            file_bytes=file_bytes,
            original_filename=image_file.filename,
            product_id=product_identifier,
            content_type=image_file.content_type,
        )
        return saved_path, candidate_hash, False

    candidate_descriptors = extract_orb_features(file_bytes)

    matched_product, _, _ = find_best_image_match(
            db,
            candidate_hash,
            candidate_descriptors,
            exclude_product_id=exclude_product_id,
        )
    if matched_product and matched_product.image_url:
        return matched_product.image_url, matched_product.image_hash or candidate_hash, True

    saved_path = save_uploaded_image(
        file_bytes=file_bytes,
        original_filename=image_file.filename,
        product_id=product_identifier,
        content_type=image_file.content_type,
    )
    return saved_path, candidate_hash, False


def normalize_optional_text(value: Optional[str]) -> Optional[str]:
    """Convert empty strings (after trimming) to None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None

@app.get("/")
def root():
    return {"message": "Inventory PO API"}

@app.get("/api/products", response_model=ProductListResponse)
def get_products(
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("product_id"),
    sort_dir: Optional[str] = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated list of products with optional search and sorting"""
    query = db.query(Product)
    
    # Apply search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Product.product_id).like(search_term),
                func.lower(Product.name).like(search_term),
                func.lower(Product.brand).like(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == "stock":
        if sort_dir == "desc":
            query = query.order_by(Product.stock.desc(), Product.product_id.asc())
        else:
            query = query.order_by(Product.stock.asc(), Product.product_id.asc())
    else:  # default to product_id
        if sort_dir == "desc":
            query = query.order_by(Product.product_id.desc())
        else:
            query = query.order_by(Product.product_id.asc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@app.get("/api/products/{id}", response_model=ProductResponse)
def get_product(id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/products", response_model=ProductResponse, status_code=201)
async def create_product(
    request: Request,
    product_id: str = Form(...),
    name: str = Form(...),
    brand: Optional[str] = Form(None),
    price: Optional[float] = Form(0),
    stock: Optional[int] = Form(0),
    order_qty: Optional[int] = Form(0),
    remarks: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    force_new_image: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Create a new product with optional image upload"""
    form_data = await request.form()
    remarks_submitted = "remarks" in form_data
    # Check if product_id already exists
    existing = db.query(Product).filter(Product.product_id == product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with product_id '{product_id}' already exists")
    
    # Handle image upload
    image_path = None
    image_hash = None
    if image:
        image_path, image_hash, _ = await process_uploaded_image(
            db,
            image,
            product_id,
            force_new_image=force_new_image,
        )
    
    # Create product
    db_product = Product(
        product_id=product_id,
        name=name,
        brand=brand,
        price=price or 0,
        stock=stock or 0,
        order_qty=order_qty or 0,
        remarks=normalize_optional_text(
            remarks if remarks is not None else ("" if remarks_submitted else None)
        ),
        image_url=image_path,
        image_hash=image_hash
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.put("/api/products/{id}", response_model=ProductResponse)
async def update_product(
    id: int,
    request: Request,
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    order_qty: Optional[int] = Form(None),
    remarks: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    force_new_image: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Update a product with optional image replacement"""
    form_data = await request.form()
    remarks_submitted = "remarks" in form_data
    db_product = db.query(Product).filter(Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update text fields
    if name is not None:
        db_product.name = name
    if brand is not None:
        db_product.brand = brand
    if price is not None:
        db_product.price = price
    if stock is not None:
        db_product.stock = stock
    if order_qty is not None:
        db_product.order_qty = order_qty
    if remarks is not None:
        db_product.remarks = normalize_optional_text(remarks)
    elif remarks_submitted:
        db_product.remarks = None
    
    # Handle image replacement
    if image:
        previous_image = db_product.image_url
        new_image_path, new_image_hash, _ = await process_uploaded_image(
            db,
            image,
            db_product.product_id,
            exclude_product_id=db_product.id,
            force_new_image=force_new_image,
        )
        if new_image_path:
            db_product.image_url = new_image_path
            db_product.image_hash = new_image_hash
            if previous_image and previous_image != new_image_path:
                delete_image_if_orphan(db, previous_image, exclude_product_id=db_product.id)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/api/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    """Delete a product and its associated image file"""
    db_product = db.query(Product).filter(Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    if db_product.image_url:
        delete_image_if_orphan(db, db_product.image_url, exclude_product_id=db_product.id)

    db.delete(db_product)
    db.commit()

    return {"detail": "Product deleted"}

@app.patch("/api/products/{id}/order-qty", response_model=ProductResponse)
def update_order_qty(id: int, order_update: OrderQtyUpdate, db: Session = Depends(get_db)):
    """Quick update of order quantity"""
    db_product = db.query(Product).filter(Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_product.order_qty = order_update.order_qty
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/api/cart", response_model=ProductListResponse)
def get_cart(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all products with order_qty > 0"""
    query = db.query(Product).filter(Product.order_qty > 0)
    query = query.order_by(Product.product_id.asc())
    
    total = query.count()
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@app.post("/api/products/reset", response_model=ResetResponse)
def reset_all_products(db: Session = Depends(get_db)):
    """Reset all products: set stock=0 and order_qty=0"""
    try:
        result = db.query(Product).update({
            Product.stock: 0,
            Product.order_qty: 0
        })
        db.commit()
        return ResetResponse(
            message="All products reset successfully",
            products_updated=result
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.post("/api/import/excel", response_model=ImportSummary)
def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import products from Excel file"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    file_path = os.path.join(settings.upload_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        products, errors = parse_excel(file_path)
        
        created = 0
        updated = 0
        
        for product_data in products:
            existing = db.query(Product).filter(Product.product_id == product_data.product_id).first()
            if existing:
                # Update existing
                for field, value in product_data.model_dump().items():
                    setattr(existing, field, value)
                updated += 1
            else:
                # Create new
                db_product = Product(**product_data.model_dump())
                db.add(db_product)
                created += 1
        
        db.commit()
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return ImportSummary(
            created=created,
            updated=updated,
            failed=len(errors),
            errors=errors
        )
    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@app.post("/api/import/pdf", response_model=ImportSummary)
def import_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import products from PDF file (best effort)"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    file_path = os.path.join(settings.upload_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        products, errors = parse_pdf(file_path)
        
        if errors and len(products) == 0:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=errors[0].get("error", "Unsupported PDF format"))
        
        created = 0
        updated = 0
        skipped_existing: List[Dict[str, str]] = []
        
        for product_data in products:
            existing = db.query(Product).filter(Product.product_id == product_data.product_id).first()
            if existing:
                skipped_existing.append({
                    "product_id": existing.product_id,
                    "existing_name": existing.name,
                    "incoming_name": product_data.name,
                    "reason": "Product already exists in the database"
                })
                continue
            db_product = Product(**product_data.model_dump())
            db.add(db_product)
            created += 1
        
        db.commit()
        
        os.remove(file_path)
        
        return ImportSummary(
            created=created,
            updated=updated,
            failed=len(errors),
            errors=errors,
            skipped_existing=skipped_existing
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

