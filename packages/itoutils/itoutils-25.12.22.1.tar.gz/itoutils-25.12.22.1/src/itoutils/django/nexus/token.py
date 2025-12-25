import json
import logging
import time

from django.conf import settings
from jwcrypto import jwk, jwt

logger = logging.getLogger(__name__)

EXPIRY_DELAY = 60  # seconds


# Use a function to easily override the setting in tests
def _get_key():
    return jwk.JWK(**settings.NEXUS_AUTO_LOGIN_KEY) if settings.NEXUS_AUTO_LOGIN_KEY else None


def generate_token(user):
    token = jwt.JWT(
        header={"alg": "A256KW", "enc": "A256CBC-HS512"},
        claims={"email": user.email, "exp": round(time.time()) + EXPIRY_DELAY},
    )
    token.make_encrypted_token(_get_key())
    return token.serialize()


def decode_token(token):
    try:
        claims = json.loads(jwt.JWT(key=_get_key(), jwt=token, expected_type="JWE").claims)
        claims.pop("exp", None)
        return claims
    except Exception as err:
        logger.exception("Could not decrypt jwt")
        raise ValueError from err
