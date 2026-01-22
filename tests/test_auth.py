def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data

def test_login(client):
    """Test user login."""
    # First register a user
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Then login
    response = client.post(
        "/auth/token",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user(client):
    """Test getting current user info."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    login_response = client.post(
        "/auth/token",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
