import os
import random
from datetime import datetime
from typing import List

import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
CLIENT_ID = os.getenv("CLIENT_ID")

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,  
    allow_methods=["*"],     
    allow_headers=["*"],     
)


class Report(BaseModel):
    id: int
    title: str
    date: str
    data: List[int]


def get_public_key():
    """Получение публичного ключа Keycloak."""
    try:
        response = requests.get(f"{KEYCLOAK_URL}/protocol/openid-connect/certs")
        response.raise_for_status()
        keys = response.json().get("keys", [])
        if not keys:
            raise ValueError("No public keys found in Keycloak response.")
        key = keys[0]  # NOTE: выбрать [0] если не подходит [1]
        return f"-----BEGIN CERTIFICATE-----\n{key['x5c'][0]}\n-----END CERTIFICATE-----"
    except Exception as e:
        raise RuntimeError(f"Failed to fetch public key from Keycloak: {e}")


def validate_token(token: str = Depends(oauth2_scheme)):
    """Проверка токена."""
    public_key = get_public_key()
    trick_url = KEYCLOAK_URL.replace('keycloak', 'localhost')
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=trick_url,
        )
        if "exp" in decoded and datetime.utcnow() >= datetime.utcfromtimestamp(decoded["exp"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        return decoded
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


def check_role(token_data: dict, required_role: str):
    """Проверка роли пользователя."""
    roles = token_data.get("realm_access", {}).get("roles", [])
    if required_role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have the required role: {required_role}",
        )


@app.get("/reports", response_model=List[Report])
async def get_reports(token_data: str = Depends(validate_token)):
    check_role(token_data, "prothetic_user")
    reports = [
        Report(
            id=i,
            title=f"Report {i}",
            date=datetime.now().strftime("%Y-%m-%d"),
            data=[random.randint(1, 100) for _ in range(5)]
        )
        for i in range(1, 6)
    ]
    return reports
