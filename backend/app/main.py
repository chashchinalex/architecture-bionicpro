import os
import time
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt


KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
API_AUDIENCE = os.getenv("API_AUDIENCE")  # optional: e.g. reports-api


app = FastAPI(title="BionicPRO Reports API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def _jwks_url() -> str:
    return f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"


def _issuer() -> str:
    return f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"


@lru_cache(maxsize=1)
def get_jwks() -> dict:
    with httpx.Client(timeout=10.0) as client:
        r = client.get(_jwks_url())
        r.raise_for_status()
        return r.json()


def get_public_key(token: str) -> Optional[str]:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    keys = get_jwks().get("keys", [])
    for key in keys:
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    return None


def verify_token_and_get_subject(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]

    public_key = get_public_key(token)
    if public_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to resolve token key")

    options = {"verify_aud": API_AUDIENCE is not None}
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=API_AUDIENCE if API_AUDIENCE else None,
            options=options,
            issuer=_issuer()
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has no subject")
    return subject


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "ts": int(time.time())}


@app.get("/reports")
def get_report(current_user_sub: str = Depends(verify_token_and_get_subject)) -> Response:
    # Временный контент отчета. Далее будет подключение ClickHouse.
    content = (
        f"Report for user {current_user_sub}\n"
        f"Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Data source: OLAP (stub)\n"
    ).encode("utf-8")

    headers = {
        "Content-Disposition": "attachment; filename=report.pdf"
    }
    return Response(content=content, media_type="application/octet-stream", headers=headers)


