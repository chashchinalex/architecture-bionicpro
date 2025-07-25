from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Keycloak settings (update as needed)
KEYCLOAK_URL = "http://keycloak:8080"
REALM = "reports-realm"
API_AUDIENCE = "reports-api"

# Cache the public key
PUBLIC_KEY = None

def get_public_key():
    global PUBLIC_KEY
    if PUBLIC_KEY is None:
        url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
        resp = requests.get(url)
        jwks = resp.json()
        # Use the first key (for demo; in production, match kid)
        key = jwks['keys'][0]
        from jose import jwk, jwt as jose_jwt
        from jose.utils import base64url_decode
        n = int.from_bytes(base64url_decode(key['n'].encode()), 'big')
        e = int.from_bytes(base64url_decode(key['e'].encode()), 'big')
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        public_numbers = rsa.RSAPublicNumbers(e, n)
        public_key = public_numbers.public_key()
        PUBLIC_KEY = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    return PUBLIC_KEY

def verify_jwt(token: str):
    from jose import jwt as jose_jwt
    public_key = get_public_key()
    try:
        payload = jose_jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=API_AUDIENCE,
            options={"verify_exp": True}
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def require_prothetic_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    payload = verify_jwt(token)
    roles = payload.get('realm_access', {}).get('roles', [])
    if 'prothetic_user' not in roles:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return payload

@app.get("/reports")
def get_reports(user=Depends(require_prothetic_user)):
    # Generate arbitrary data
    return {
        "user": user.get("preferred_username"),
        "reports": [
            {"id": 1, "title": "Report 1", "value": 42},
            {"id": 2, "title": "Report 2", "value": 99}
        ]
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 