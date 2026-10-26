from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.admin.models import AdminUser, Order
from app.core.security import hash_password, verify_password
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with testing_session() as session:
        session.add(
            AdminUser(username="admin", password_hash=hash_password("senha-segura"))
        )
        session.commit()

    def override_db():
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client, testing_session
    app.dependency_overrides.clear()


def test_password_hash_is_verified():
    encoded = hash_password("senha-segura")
    assert verify_password("senha-segura", encoded)
    assert not verify_password("senha-incorreta", encoded)


def admin_headers(test_client):
    response = test_client.post(
        "/admin/login",
        json={"username": "admin", "password": "senha-segura"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_rejects_request_without_credentials(client):
    test_client, _ = client
    response = test_client.get("/admin/products")
    assert response.status_code == 401
    assert response.json()["detail"] == "Sessão administrativa inválida ou expirada"


def test_authenticates_admin_stored_in_database(client):
    test_client, _ = client
    response = test_client.get("/admin/me", headers=admin_headers(test_client))
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_category_and_product_crud(client):
    test_client, _ = client
    headers = admin_headers(test_client)
    category = test_client.post(
        "/admin/categories", json={"name": "Pastéis salgados"}, headers=headers
    )
    assert category.status_code == 201

    product = test_client.post(
        "/admin/products",
        json={
            "name": "Pastel de queijo",
            "description": "Queijo derretido",
            "price": "12.50",
            "category_id": category.json()["id"],
        },
        headers=headers,
    )
    assert product.status_code == 201
    assert product.json()["category"]["name"] == "Pastéis salgados"

    updated = test_client.put(
        f"/admin/products/{product.json()['id']}",
        json={**product.json(), "name": "Pastel de queijo especial"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Pastel de queijo especial"

    blocked = test_client.delete(
        f"/admin/categories/{category.json()['id']}", headers=headers
    )
    assert blocked.status_code == 409
    assert (
        test_client.delete(
            f"/admin/products/{product.json()['id']}", headers=headers
        ).status_code
        == 204
    )
    assert (
        test_client.delete(
            f"/admin/categories/{category.json()['id']}", headers=headers
        ).status_code
        == 204
    )


def test_order_status_flow(client):
    test_client, testing_session = client
    with testing_session() as session:
        order = Order(
            customer_name="Maria",
            customer_phone="11999999999",
            total=Decimal("25.00"),
        )
        session.add(order)
        session.commit()
        order_id = order.id

    headers = admin_headers(test_client)
    accepted = test_client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "aceito"},
        headers=headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "aceito"

    finished = test_client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "finalizado"},
        headers=headers,
    )
    assert finished.status_code == 200

    invalid = test_client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "aceito"},
        headers=headers,
    )
    assert invalid.status_code == 409
