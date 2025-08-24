import os
import requests
import json
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
# Возвращаем импорты к исходному виду
from jose import jwt, JWTError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_CERTS_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

def get_keycloak_public_key():
    try:
        response = requests.get(KEYCLOAK_CERTS_URL)
        response.raise_for_status()
        jwks = response.json()
        for key in jwks['keys']:
            # Находим нужный ключ для алгоритма RS256
            if key.get('alg') == 'RS256' and key.get('use') == 'sig':
                # ИЗМЕНЕНИЕ: Просто возвращаем сам словарь с ключом.
                # Библиотека jose сама разберется с этим форматом.
                return key
        raise HTTPException(status_code=500, detail="Public key for RS256 not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

keycloak_public_key = get_keycloak_public_key()
oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="", tokenUrl="")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            keycloak_public_key,
            algorithms=["RS256"],
            options={"verify_signature": True, "verify_aud": False, "exp": True}
        )
        roles = payload.get("realm_access", {}).get("roles", [])
        if "prothetic_user" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return payload
    except JWTError as e:
        # Логируем ошибку для отладки
        print(f"JWT Error: {e}")
        raise auth_exception

@app.get("/reports")
async def get_report(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    report_data = {
        "reportId": "rep-12345",
        "userId": user_id,
        "prosthesisModel": "BionicPRO v3",
        "usageData": [
            {"date": "2025-08-20", "movements": 1500, "battery_cycles": 2},
            {"date": "2025-08-21", "movements": 1750, "battery_cycles": 3},
        ]
    }
    return report_data

@app.get("/")
async def root():
    return {"message": "BionicPRO API is running"}