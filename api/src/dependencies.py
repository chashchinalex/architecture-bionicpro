import logging

from fastapi import HTTPException, Security
from fastapi.security import OAuth2AuthorizationCodeBearer
from src.settings import app_settings
from starlette import status

from keycloak import KeycloakOpenID

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=app_settings.authorization_url,
    tokenUrl=app_settings.token_url,
)

keycloak_openid = KeycloakOpenID(
    server_url=app_settings.keycloak_server_url,
    client_id=app_settings.keycloak_client_id,
    realm_name=app_settings.keycloak_realm,
    client_secret_key=app_settings.keycloak_client_secret,
)


def get_payload(token: str = Security(oauth2_scheme)) -> dict:
    logger.debug("Starting access check.")

    try:
        payload = keycloak_openid.decode_token(token)
        logger.debug("Payload parsed successfully.")
    except Exception as e:
        logger.error("Token validation error occurred: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("Checking for 'prothetic_user' role.")
    roles = payload.get("realm_access", {}).get("roles", [])
    if "prothetic_user" not in roles:
        logger.warning("User does not have the 'prothetic_user' role.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("User has the 'prothetic_user' role. Access granted.")
    return payload
