from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST
from litestar.testing import AsyncTestClient

from auth.factories import UserFactory
from auth.services import API_KEY_HEADER, TOKEN_PREFIX, AuthService, LoginRequestDTO, SignUpRequestDTO


async def test_account_signup(http_api_client):
    response = await http_api_client.post(
        "/api/auth/account/signup",
        json={
            "email": "newuser@mail.com",
            "password": "newuserpassword",
        },
    )
    assert response.status_code == HTTP_201_CREATED


async def test_account_login(auth_service: AuthService, http_api_client: AsyncTestClient):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")
    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": user.email, "password": user.password},
    )
    assert login_response.status_code == HTTP_201_CREATED
    login_response_json = login_response.json()
    assert login_response_json["user"]["email"] == user.email
    assert login_response_json["user"]["id"] == str(auth_code.user_id)


async def test_account_login_wrong_email(auth_service: AuthService, http_api_client: AsyncTestClient):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")
    wrong_email = "wrong@email.com"

    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": wrong_email, "password": user.password},
    )
    assert login_response.status_code == HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == f"User with email {wrong_email} not found"


async def test_account_login_wrong_password(auth_service: AuthService, http_api_client: AsyncTestClient):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")

    login_response = await http_api_client.post(
        "/api/auth/account/login",
        json={"email": user.email, "password": "wrong_password"},
    )
    assert login_response.status_code == HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == "Invalid password"


async def test_account_me(http_api_client: AsyncTestClient, auth_service: AuthService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")
    login_data = await auth_service.login(
        LoginRequestDTO(email=user.email, password=user.password, device="testclient")
    )

    account_response = await http_api_client.get(
        "/api/auth/account/me",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}"},
    )
    assert account_response.status_code == HTTP_200_OK
    assert user.email == account_response.json()["user"]["email"]


async def test_account_logout(http_api_client: AsyncTestClient, auth_service: AuthService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")
    login_data = await auth_service.login(
        LoginRequestDTO(email=user.email, password=user.password, device="testclient")
    )
    await http_api_client.post(
        "/api/auth/account/logout",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}"},
    )
    account_response = await http_api_client.get(
        "/api/auth/account/me",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}"},
    )
    assert account_response.status_code == HTTP_401_UNAUTHORIZED


async def test_activate_account(http_api_client: AsyncTestClient, auth_service: AuthService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    activate_response = await http_api_client.post("/api/auth/account/activate", json={"code": auth_code.code})
    assert activate_response.status_code == HTTP_201_CREATED

    login_data = await auth_service.login(
        LoginRequestDTO(
            email=user.email,
            password=user.password,
            device="testclient",
        )
    )

    account_data = await auth_service.get_account(login_data.token)
    assert account_data.user.email == user.email


async def test_not_authorized_with_wrong_tokenkey(http_api_client: AsyncTestClient, auth_service: AuthService):
    user = UserFactory.build()
    auth_code = await auth_service.signup(SignUpRequestDTO(email=user.email, password=user.password))
    await auth_service.activate_user(auth_code.code, "testclient")
    login_data = await auth_service.login(
        LoginRequestDTO(email=user.email, password=user.password, device="testclient")
    )

    account_response = await http_api_client.get(
        "/api/auth/account/me",
        headers={API_KEY_HEADER: f"{TOKEN_PREFIX} {login_data.token}_invalid"},
    )
    assert account_response.status_code == HTTP_401_UNAUTHORIZED
