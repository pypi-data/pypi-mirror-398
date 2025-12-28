from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.testing import AsyncTestClient

from auth.factories import PermissionFactory


async def test_get_permissions(admin_api_client: AsyncTestClient):
    response = await admin_api_client.get("/api/auth/permissions")
    assert response.status_code == HTTP_200_OK


async def test_create_permission(admin_api_client: AsyncTestClient, permissions_fixture, permission_service):
    prev_items_count = await permission_service.count()

    response = await admin_api_client.post("/api/auth/permissions", json={"name": "allow-edit"})
    assert response.status_code == HTTP_201_CREATED

    items_count = await permission_service.count()
    assert items_count == prev_items_count + 1

    # teardown
    await permission_service.delete(response.json()["id"])


async def test_remove_permission(
    admin_api_client: AsyncTestClient,
    permissions_fixture,
    permission_service,
):
    permissions_count = await permission_service.count()

    permission_to_remove = await permission_service.create(PermissionFactory.build(), auto_commit=True)
    response = await admin_api_client.delete(f"/api/auth/permissions/{permission_to_remove.id}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert permissions_count == await permission_service.count()
