from keycloak import KeycloakOpenID
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


KEYCLOAK_REALM = "reports-realm"
KEYCLOAK_URL = "http://keycloak:8080"
KEYCLOAK_CLIENT_ID = "reports-frontend"
KEYCLOAK_CLIENT_SECRET = "oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq"

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL, realm_name=KEYCLOAK_REALM, client_id=KEYCLOAK_CLIENT_ID
)

token_scheme = HTTPBearer()


async def verify_bearer_token(
    token: HTTPAuthorizationCredentials = Security(token_scheme),
):
    try:
        payload = keycloak_openid.decode_token(token.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    all_user_roles = payload.get("realm_access", {}).get("roles", [])

    if "prothetic_user" not in all_user_roles:
        raise HTTPException(status_code=403, detail="Access denied.")
