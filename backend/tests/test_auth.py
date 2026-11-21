from tests.conftest import PASSWORD, auth_headers


def register(client, email="donor@example.com", role="donor", password=PASSWORD):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "Test", "email": email, "password": password, "role": role},
    )


def test_register_and_login_and_me(client):
    resp = register(client)
    assert resp.status_code == 201
    assert resp.json()["role"] == "donor"
    assert "password" not in resp.text

    headers = auth_headers(client, "donor@example.com")
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "donor@example.com"


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
