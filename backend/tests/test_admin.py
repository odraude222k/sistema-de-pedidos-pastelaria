from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Order


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_db():
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    settings.admin_api_key = "segredo"
    with TestClient(app) as test_client:
        yield test_client, testing_session
    app.dependency_overrides.clear()


def test_rejects_request_without_admin_key(client):
    test_client, _ = client
    response = test_client.get("/admin/products")
    assert response.status_code == 401
    assert response.json()["detail"] == "Acesso administrativo não autorizado"


def test_category_and_product_crud(client):
    test_client, _ = client
    headers = {"X-Admin-Key": "segredo"}
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

    headers = {"X-Admin-Key": "segredo"}
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
