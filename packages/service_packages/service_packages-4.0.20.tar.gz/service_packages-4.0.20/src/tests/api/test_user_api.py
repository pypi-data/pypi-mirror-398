from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from auth.factories import UserFactory


async def test_get_users(admin_api_client):
    response = await admin_api_client.get("/api/auth/users")
    assert response.status_code == HTTP_200_OK


async def test_create_user(admin_api_client, users_fixture, user_service):
    prev_users_count = await user_service.count()

    user_to_create = {
        "email": "user-to-create@mail.com",
        "password": "superPassword",
        "is_email_verified": False,
        "is_enabled": True,
    }
    response = await admin_api_client.post("/api/auth/users", json=user_to_create)
    assert response.status_code == HTTP_201_CREATED

    users_count = await user_service.count()
    assert users_count == prev_users_count + 1

    # teardown
    await user_service.delete(response.json()["id"])


async def test_remove_user(admin_api_client, users_fixture, user_service):
    users_count = await user_service.count()

    user_to_remove = await user_service.create(UserFactory.build(), auto_commit=True)
    response = await admin_api_client.delete(f"/api/auth/users/{user_to_remove.id}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert users_count == await user_service.count()
