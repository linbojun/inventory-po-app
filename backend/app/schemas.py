from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    product_id: str
    name: str
    brand: Optional[str] = None
    price: Decimal = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    order_qty: int = Field(default=0, ge=0)
    image_url: Optional[str] = None
    remarks: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_id: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    order_qty: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = None
    remarks: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderQtyUpdate(BaseModel):
    order_qty: int = Field(ge=0)


class StockUpdate(BaseModel):
    stock: int = Field(ge=0)

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ImportSummary(BaseModel):
    created: int
    updated: int
    failed: int
    errors: list[dict] = Field(default_factory=list)
    skipped_existing: list[dict] = Field(default_factory=list)

class ResetResponse(BaseModel):
    message: str
    products_updated: int

