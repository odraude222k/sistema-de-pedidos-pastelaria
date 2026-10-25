import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import get_db
from app.models import Category, Order, OrderStatus, Product
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    OrderRead,
    OrderStatusUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(prefix="/admin", tags=["Administração"])
DbSession = Annotated[Session, Depends(get_db)]


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    if x_admin_key is None or not secrets.compare_digest(
        x_admin_key, settings.admin_api_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso administrativo não autorizado",
        )


Admin = Annotated[None, Depends(require_admin)]


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: DbSession, _: Admin):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.post(
    "/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED
)
def create_category(data: CategoryCreate, db: DbSession, _: Admin):
    category = Category(name=data.name.strip())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Já existe uma categoria com esse nome"
        ) from exc
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession, _: Admin):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    has_products = db.scalar(
        select(Product.id).where(Product.category_id == category_id).limit(1)
    )
    if has_products:
        raise HTTPException(
            status_code=409, detail="Não é possível excluir uma categoria com produtos"
        )
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_category(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise HTTPException(status_code=422, detail="Categoria informada não existe")


@router.get("/products", response_model=list[ProductRead])
def list_products(db: DbSession, _: Admin):
    statement = (
        select(Product).options(selectinload(Product.category)).order_by(Product.name)
    )
    return db.scalars(statement).all()


@router.post(
    "/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED
)
def create_product(data: ProductCreate, db: DbSession, _: Admin):
    _get_category(db, data.category_id)
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate, db: DbSession, _: Admin):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    _get_category(db, data.category_id)
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: DbSession, _: Admin):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/orders", response_model=list[OrderRead])
def list_orders(db: DbSession, _: Admin):
    return db.scalars(select(Order).order_by(Order.created_at.desc())).all()


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int, data: OrderStatusUpdate, db: DbSession, _: Admin
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    allowed = {
        OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.REJECTED},
        OrderStatus.ACCEPTED: {OrderStatus.FINISHED},
        OrderStatus.REJECTED: set(),
        OrderStatus.FINISHED: set(),
    }
    if data.status not in allowed[order.status]:
        raise HTTPException(status_code=409, detail="Transição de status inválida")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
