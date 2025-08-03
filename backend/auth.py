from fastapi import HTTPException, Request
from keycloak import KeycloakOpenID


class Auth:

    def __init__(self, url_keycloak: str, id_client: str, name_realm: str, secret: str):
        self.keycloak_openid = KeycloakOpenID(
            server_url=url_keycloak,
            client_id=id_client,
            realm_name=name_realm,
            client_secret_key=secret,
        )
    
    def _get_token_bearer(self, request: Request) -> str:
        auth = request.headers.get("authorization")
        if not auth:
            raise HTTPException(status_code=403, detail="Forbidden")
        return auth.replace("Bearer ", "", 1)
    
    def get_info(self, token_bearer: str):
        return self.keycloak_openid.decode_token(
            token_bearer,
            # algorithms=["RS256"]
        )

    def get_roles(self, request: Request) -> list[str]:
        token_bearer = self._get_token_bearer(request)
        info = self.get_info(token_bearer)
        return info.get('realm_access', {}).get('roles', [])

    
