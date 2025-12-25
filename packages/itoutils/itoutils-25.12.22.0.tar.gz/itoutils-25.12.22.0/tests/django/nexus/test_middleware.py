import pytest
from django.contrib.auth.models import User
from pytest_django.asserts import assertRedirects

from itoutils.django.nexus.token import generate_token
from itoutils.urls import add_url_params
from tests.django.factories import UserFactory


@pytest.fixture(params=[{}, {"filter": "76", "username": "123"}], ids=("no_params", "with_params"))
def params(request):
    return request.param


def test_middleware_for_authenticated_user(db, client, params, caplog):
    expected_url = add_url_params("/path", params)

    user = UserFactory()
    client.force_login(user)

    response = client.get(add_url_params("/path", params | {"auto_login": generate_token(user)}))
    assertRedirects(response, expected_url, fetch_redirect_response=False)
    assert caplog.messages == ["Nexus auto login: user is already logged in"]


def test_middleware_for_wrong_authenticated_user(db, client, params, caplog):
    expected_url = add_url_params("/path", params)

    user = UserFactory()
    # Another user is logged in
    client.force_login(User.objects.create(email="moi@mailinator.com", pk=2))

    response = client.get(add_url_params("/path", params | {"auto_login": generate_token(user)}))
    assertRedirects(
        response,
        add_url_params("/proconnect/authorize", {"email": user.email, "next_url": expected_url}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [
        "Nexus auto login: wrong user is logged in -> logging them out",
        f"Nexus auto login: {user} was found and forwarded to ProConnect",
    ]


def test_middleware_multiple_tokens(db, client, caplog):
    user = UserFactory()
    token = generate_token(user)
    response = client.get(f"/path?auto_login={token}&auto_login={token}")
    assertRedirects(response, "/path", fetch_redirect_response=False)
    assert caplog.messages == [
        "Nexus auto login: Multiple tokens found -> ignored",
    ]


def test_middleware_invalid_token(db, client, caplog):
    params = {"auto_login": "bad jwt"}
    response = client.get(add_url_params("/path", params))
    assertRedirects(response, "/path", fetch_redirect_response=False)
    assert caplog.messages == [
        "Could not decrypt jwt",
        "Invalid auto login token",
        "Nexus auto login: Missing email in token -> ignored",
    ]


def test_middleware_with_no_existing_user(db, client, params, caplog):
    expected_url = add_url_params("/path", params)

    user = UserFactory.build()
    jwt = generate_token(user)
    response = client.get(add_url_params("/path", params | {"auto_login": jwt}))
    assertRedirects(
        response,
        add_url_params("/register", {"email": user.email, "next_url": expected_url}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [f"Nexus auto login: no user found for jwt={jwt}"]


def test_middleware_for_unlogged_user(db, client, params, caplog):
    expected_url = add_url_params("/path", params)

    user = UserFactory()

    response = client.get(add_url_params("/path", params | {"auto_login": generate_token(user)}))
    assertRedirects(
        response,
        add_url_params("/proconnect/authorize", {"email": user.email, "next_url": expected_url}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [f"Nexus auto login: {user} was found and forwarded to ProConnect"]
