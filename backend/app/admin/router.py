from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.admin.models import (
    AdminSession,
    AdminUser,
    Category,
    Order,
    OrderStatus,
    Product,
)
from app.admin.schemas import (
    AdminLogin,
    AdminToken,
    CategoryCreate,
    CategoryRead,
    OrderRead,
    OrderStatusUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    generate_session_token,
    hash_session_token,
    verify_password,
)
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["Administração"])
DbSession = Annotated[Session, Depends(get_db)]
bearer_auth = HTTPBearer(auto_error=False)


def require_admin(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_auth)],
) -> AdminUser:
    admin_session = None
    if credentials is not None and credentials.scheme.lower() == "bearer":
        admin_session = db.scalar(
            select(AdminSession)
            .options(joinedload(AdminSession.admin_user))
            .where(
                AdminSession.token_hash == hash_session_token(credentials.credentials),
                AdminSession.expires_at > datetime.now(UTC),
            )
        )
    if admin_session is None or not admin_session.admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão administrativa inválida ou expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin_session.admin_user


Admin = Annotated[AdminUser, Depends(require_admin)]


@router.post("/login", response_model=AdminToken)
def login(data: AdminLogin, db: DbSession):
    admin = db.scalar(
        select(AdminUser).where(AdminUser.username == data.username.strip().lower())
    )
    password_is_valid = verify_password(
        data.password,
        admin.password_hash if admin is not None else DUMMY_PASSWORD_HASH,
    )
    if admin is None or not admin.is_active or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    token = generate_session_token()
    expires_at = datetime.now(UTC) + timedelta(hours=12)
    db.add(
        AdminSession(
            token_hash=hash_session_token(token),
            admin_user_id=admin.id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return AdminToken(access_token=token, expires_at=expires_at)


@router.get("/me")
def current_admin(admin: Admin):
    return {"id": admin.id, "username": admin.username}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    db: DbSession,
    _: Admin,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_auth)],
):
    admin_session = db.scalar(
        select(AdminSession).where(
            AdminSession.token_hash == hash_session_token(credentials.credentials)
        )
    )
    if admin_session is not None:
        db.delete(admin_session)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
