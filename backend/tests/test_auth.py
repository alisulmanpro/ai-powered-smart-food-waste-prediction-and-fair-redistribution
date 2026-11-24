from app.core.security import create_access_token, create_verification_token
from tests.conftest import PASSWORD, auth_headers, verify_email_for


def register(client, email="donor@example.com", role="donor", password=PASSWORD, verify=True):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "Test", "email": email, "password": password, "role": role},
    )
    if resp.status_code == 201 and verify:
        verify_email_for(client, resp.json()["id"])
    return resp


def test_register_and_login_and_me(client):
    resp = register(client)
    assert resp.status_code == 201
    assert resp.json()["role"] == "donor"
    assert resp.json()["email_verified"] is False  # response captured before verification
    assert "password" not in resp.text

    headers = auth_headers(client, "donor@example.com")
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "donor@example.com"
    assert me.json()["email_verified"] is True


def test_email_is_case_insensitive_and_unique(client):
    assert register(client, "Donor@Example.com").status_code == 201
    assert register(client, "donor@example.com").status_code == 409
    assert auth_headers(client, "DONOR@example.com")


def test_cannot_self_register_as_admin(client):
    resp = register(client, "evil@example.com", role="admin")
    assert resp.status_code == 422


def test_short_password_rejected(client):
    assert register(client, password="short").status_code == 422


def test_wrong_password_and_unknown_user(client):
    register(client)
    bad = client.post(
        "/api/v1/auth/login", data={"username": "donor@example.com", "password": "nope-nope-1"}
    )
    assert bad.status_code == 401
    unknown = client.post(
        "/api/v1/auth/login", data={"username": "nobody@example.com", "password": PASSWORD}
    )
    assert unknown.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/users/me").status_code == 401
    bad = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-token"})
    assert bad.status_code == 401


# ---------- email verification ----------


def test_login_blocked_until_email_verified(client):
    resp = register(client, verify=False)
    assert resp.status_code == 201
    assert resp.json()["email_verified"] is False

    login = client.post(
        "/api/v1/auth/login", data={"username": "donor@example.com", "password": PASSWORD}
    )
    assert login.status_code == 403
    assert "not verified" in login.json()["detail"].lower()


def test_verify_email_flow_unblocks_login(client):
    resp = register(client, verify=False)
    verify_email_for(client, resp.json()["id"])

    login = client.post(
        "/api/v1/auth/login", data={"username": "donor@example.com", "password": PASSWORD}
    )
    assert login.status_code == 200


def test_verify_email_rejects_invalid_token(client):
    resp = client.post("/api/v1/auth/verify-email", json={"token": "not-a-token"})
    assert resp.status_code == 400


def test_verify_email_rejects_access_token(client):
    resp = register(client, verify=False)
    access = create_access_token(resp.json()["id"], "donor")
    resp = client.post("/api/v1/auth/verify-email", json={"token": access})
    assert resp.status_code == 400


def test_verify_email_link_returns_html(client):
    resp = register(client, verify=False)
    token = create_verification_token(resp.json()["id"])
    page = client.get(f"/api/v1/auth/verify-email?token={token}")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "verified" in page.text.lower()


def test_verify_email_link_invalid_token_returns_html(client):
    page = client.get("/api/v1/auth/verify-email?token=bogus")
    assert page.status_code == 400
    assert "text/html" in page.headers["content-type"]


def test_resend_verification_is_generic(client):
    # unknown address -> same generic 200 message (no account enumeration)
    ghost = client.post("/api/v1/auth/resend-verification", json={"email": "ghost@example.com"})
    assert ghost.status_code == 200
    assert ghost.json()["message"]

    register(client, verify=False)
    known = client.post("/api/v1/auth/resend-verification", json={"email": "donor@example.com"})
    assert known.status_code == 200
    assert known.json()["message"] == ghost.json()["message"]


def test_resend_verification_is_noop_when_already_verified(client):
    register(client)
    resp = client.post("/api/v1/auth/resend-verification", json={"email": "donor@example.com"})
    assert resp.status_code == 200
