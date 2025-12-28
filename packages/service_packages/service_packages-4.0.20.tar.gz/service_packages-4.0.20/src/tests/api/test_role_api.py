from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

from auth.factories import RoleFactory


async def test_get_roles(admin_api_client):
    response = await admin_api_client.get("/api/auth/roles")
    assert response.status_code == HTTP_200_OK


async def test_create_role(admin_api_client, roles_fixture, role_service):
    prev_items_count = await role_service.count()

    response = await admin_api_client.post("/api/auth/roles", json={"name": "superadmin"})
    assert response.status_code == HTTP_201_CREATED

    items_count = await role_service.count()
    assert items_count == prev_items_count + 1

    # teardown
    await role_service.delete(response.json()["id"])


async def test_remove_role(admin_api_client, roles_fixture, role_service):
    roles_count = await role_service.count()

    role_to_remove = await role_service.create(RoleFactory.build(), auto_commit=True)
    response = await admin_api_client.delete(f"/api/auth/roles/{role_to_remove.id}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert roles_count == await role_service.count()
