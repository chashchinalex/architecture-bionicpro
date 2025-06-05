import os
import random
import string
import requests
import logging
from httpx import AsyncClient
import jwt
from jwt.exceptions import PyJWTError
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.cors import CORSMiddleware

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORT_ROLE = "prothetic_user"
APP_KEYCLOAK_URL = os.environ.get("APP_KEYCLOAK_URL", "http://localhost:8080")
APP_KEYCLOAK_REALM = os.environ.get("APP_KEYCLOAK_REALM", "reports-realm")
APP_KEYCLOAK_ISSUER = f"{APP_KEYCLOAK_URL}/realms/{APP_KEYCLOAK_REALM}"
OIDC_DISCOVERY_URL = f"{APP_KEYCLOAK_URL}/realms/{APP_KEYCLOAK_REALM}/.well-known/openid-configuration"

bearer = HTTPBearer()

async def load_public_key():
    logger.info(f"OIDC_DISCOVERY_URL: {OIDC_DISCOVERY_URL}")
    oidc_config = requests.get(OIDC_DISCOVERY_URL).json()

    logger.info(f"oidc_config: {oidc_config}")
    jwks_uri = oidc_config["jwks_uri"]

    logger.info(f"jwks_uri: {jwks_uri}")
    jwks = requests.get(jwks_uri).json()
    keys = jwks.get("keys", [])
    return RSAAlgorithm.from_jwk(keys['keys'][1])


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer)):

    public_key = await load_public_key()

    try:
        payload = jwt.decode(token.credentials, public_key, algorithms=['RS256'])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    roles = payload.get("realm_access", {}).get("roles", [])
    if REPORT_ROLE not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"missing '{REPORT_ROLE}' role")

    return payload


def generate_random_string(length=10):
    """Генерирует случайную строку заданной длины."""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

async def generate_random_data(n, k):
    """Генерирует таблицу с n колонками и k строками."""
    data = []
    for _ in range(k):
        row = [generate_random_string() for _ in range(n)]
        data.append(row)
    return data

@app.get("/reports", dependencies=[Depends(get_current_user)])
async def get_reports() -> dict:

    return await generate_random_data(10, 10)