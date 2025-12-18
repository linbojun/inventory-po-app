from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    brand = Column(String, index=True, nullable=True)
    price = Column(Numeric(10, 2), default=0)
    stock = Column(Integer, default=0)
    order_qty = Column(Integer, default=0, index=True)
    image_url = Column(String, nullable=True)
    image_hash = Column(String(32), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_brand_name', 'brand', 'name'),
    )

