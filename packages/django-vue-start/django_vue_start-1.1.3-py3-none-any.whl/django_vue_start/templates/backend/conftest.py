import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory fixture to create users."""
    def _create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        **kwargs
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
    return _create_user


@pytest.fixture
def user(create_user):
    """Return a basic test user."""
    return create_user()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an API client authenticated as test user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_user(db):
    """Return an admin/superuser."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Return an API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client
