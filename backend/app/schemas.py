from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import OrderStatus


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class CategoryRead(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: CategoryRead


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    customer_phone: str
    status: OrderStatus
    total: Decimal
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
