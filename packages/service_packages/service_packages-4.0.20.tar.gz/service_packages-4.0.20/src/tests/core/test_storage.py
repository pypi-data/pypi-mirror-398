import uuid

from auth.services.auth_service import AccountCacheDTO, AccountCacheSessionDTO, AccountUserDTO
from core.storage import Storage


async def test_storage(storage: Storage) -> None:
    session_value = AccountCacheDTO(
        user=AccountUserDTO(id=uuid.uuid4(), email="user@mail.com", is_enabled=True, is_email_verified=True, roles=[]),
        sessions=[AccountCacheSessionDTO(session_id=uuid.uuid4(), device="testclient")],
    )

    await storage.save("sessions", str(session_value.user.id), session_value)

    value_from_cache = await storage.get("sessions", str(session_value.user.id), model_type=AccountCacheDTO)
    assert value_from_cache == session_value
