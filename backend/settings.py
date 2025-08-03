from pydantic_settings import BaseSettings


class SettingsAuth(BaseSettings):
    URL_KEYCLOAK: str = "http://keycloak:8080"
    ID_CLIENT: str = "reports-api"
    NAME_REALM: str = "reports-realm"
    SECRET: str = ""

settings_auth = SettingsAuth()