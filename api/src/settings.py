class AppSettings:
    # auth
    authorization_url: str = "http://keycloak:8080/realms/reports-realm/protocol/openid-connect/auth"
    token_url: str = "http://keycloak:8080/realms/reports-realm/protocol/openid-connect/token"

    # keycloak
    keycloak_server_url: str = "http://keycloak:8080/"
    keycloak_client_id: str = "reports-backend"
    keycloak_realm: str = "reports-realm"
    keycloak_client_secret: str = "supersecret"


app_settings = AppSettings()
