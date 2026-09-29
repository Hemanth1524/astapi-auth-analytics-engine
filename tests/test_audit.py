import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.core.rate_limit import limiter
from app import models

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    limiter.reset()
    yield
    limiter.reset()

def test_register_and_login_flow():
    reg_res = client.post("/api/v1/auth/register", json={"username": "alice", "password": "password123"})
    assert reg_res.status_code == 200
    assert reg_res.json()["role"] == "user"

    login_res = client.post("/api/v1/auth/login", data={"username": "alice", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "alice"

def test_uniform_401_on_invalid_credentials():
    res = client.post("/api/v1/auth/login", data={"username": "ghost_user", "password": "wrong"})
    assert res.status_code == 401
    assert "www-authenticate" in res.headers

def test_rbac_admin_protection():
    client.post("/api/v1/auth/register", json={"username": "bob", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", data={"username": "bob", "password": "password123"})
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_admin_access_to_analytics_summary():
    db = SessionLocal()
    from app.core.security import get_password_hash
    admin_user = models.User(username="admin", hashed_password=get_password_hash("admin123"), role="admin")
    db.add(admin_user)
    db.commit()
    db.close()

    login_res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_requests" in data
    assert "avg_latency_ms" in data
    assert "error_count" in data

def test_login_rate_limiting():
    payload = {"username": "attacker", "password": "bad"}
    for _ in range(5):
        r = client.post("/api/v1/auth/login", data=payload)
        assert r.status_code == 401
    
    r6 = client.post("/api/v1/auth/login", data=payload)
    assert r6.status_code == 429
    assert any(k.lower() == "retry-after" for k in r6.headers.keys())
