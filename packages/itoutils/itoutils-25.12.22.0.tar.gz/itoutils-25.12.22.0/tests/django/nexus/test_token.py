import datetime

import pytest
from django.utils import timezone
from jwcrypto import jwt

from itoutils.django.nexus.token import EXPIRY_DELAY, decode_token, generate_token
from tests.django.factories import UserFactory


def test_generate_and_decode_token(db, time_machine):
    now = timezone.now()
    time_machine.move_to(now)
    user = UserFactory()
    token = generate_token(user)

    # generated token requires a key to decode
    with pytest.raises(KeyError):
        jwt.JWT(jwt=token).claims  # noqa: B018

    # It contains the user email
    assert decode_token(token) == {"email": user.email}

    # Wait for the JWT to expire, and then extra time for the leeway.
    leeway = 60
    time_machine.move_to(now + datetime.timedelta(seconds=EXPIRY_DELAY + leeway + 1))
    with pytest.raises(ValueError):
        decode_token(token)
