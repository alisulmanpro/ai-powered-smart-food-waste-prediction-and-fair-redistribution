from tests.conftest import PASSWORD, auth_headers, verify_email_for

RECIPIENT_PROFILE = {
    "organisation_name": "Helping Hands",
    "capacity_units": 100,
    "storage_types": ["ambient", "chilled"],
    "accepted_categories": ["bakery"],
    "need_level": 4,
}


def register(client, email, role):
    resp = client.post(
        "/api/v1/auth/register",
        json={"name": "T", "email": email, "password": PASSWORD, "role": role},
    )
    assert resp.status_code == 201
    verify_email_for(client, resp.json()["id"])
    return resp.json()


def test_donor_cannot_use_admin_endpoints(client):
    register(client, "donor@example.com", "donor")
    headers = auth_headers(client, "donor@example.com")
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403


def test_recipient_cannot_use_donor_profile_endpoint(client):
    register(client, "rec@example.com", "recipient")
    headers = auth_headers(client, "rec@example.com")
    resp = client.put(
        "/api/v1/users/me/donor-profile", json={"business_name": "x"}, headers=headers
    )
    assert resp.status_code == 403


def test_recipient_verification_flow(client, admin_headers):
    rec = register(client, "rec@example.com", "recipient")
    rec_headers = auth_headers(client, "rec@example.com")

    # verifying before the profile exists is rejected
    early = client.post(f"/api/v1/admin/users/{rec['id']}/verify", headers=admin_headers)
    assert early.status_code == 409

    put = client.put(
        "/api/v1/users/me/recipient-profile", json=RECIPIENT_PROFILE, headers=rec_headers
    )
    assert put.status_code == 200
    assert put.json()["verified"] is False

    ok = client.post(f"/api/v1/admin/users/{rec['id']}/verify", headers=admin_headers)
    assert ok.status_code == 200

    me = client.get("/api/v1/users/me", headers=rec_headers).json()
    assert me["recipient_profile"]["verified"] is True


def test_recipient_cannot_self_verify(client):
    register(client, "rec@example.com", "recipient")
    headers = auth_headers(client, "rec@example.com")
    client.put(
        "/api/v1/users/me/recipient-profile",
        json={**RECIPIENT_PROFILE, "verified": True},  # must be ignored
        headers=headers,
    )
    me = client.get("/api/v1/users/me", headers=headers).json()
    assert me["recipient_profile"]["verified"] is False


def test_admin_creates_admin_and_deactivates_user(client, admin_headers):
    created = client.post(
        "/api/v1/admin/admins",
        json={"name": "Second", "email": "second@example.com", "password": PASSWORD},
        headers=admin_headers,
    )
    assert created.status_code == 201
    assert created.json()["role"] == "admin"
    assert auth_headers(client, "second@example.com")

    donor = register(client, "donor@example.com", "donor")
    resp = client.patch(
        f"/api/v1/admin/users/{donor['id']}/active",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    login = client.post(
        "/api/v1/auth/login", data={"username": "donor@example.com", "password": PASSWORD}
    )
    assert login.status_code == 403


def test_admin_cannot_deactivate_self(client, admin_headers):
    me = client.get("/api/v1/users/me", headers=admin_headers).json()
    resp = client.patch(
        f"/api/v1/admin/users/{me['id']}/active", json={"is_active": False}, headers=admin_headers
    )
    assert resp.status_code == 400
