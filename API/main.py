import os
import time
import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
from jose.utils import base64url_decode

app = FastAPI()
bearer = HTTPBearer()

KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://localhost:8080')
REALM = os.getenv('KEYCLOAK_REALM', 'reports-realm')
CLIENT_ID = 'reports-api'

JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
jwks = requests.get(JWKS_URL).json()

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(401, 'Invalid token header')
    key = next(
        (k for k in jwks['keys'] if k['kid'] == unverified_header['kid']),
        None
    )
    if not key:
        raise HTTPException(401, 'Unknown key ID')
    public_key = jwk.construct(key)
    message, encoded_sig = token.rsplit('.', 1)
    decoded_sig = base64url_decode(encoded_sig.encode())
    if not public_key.verify(message.encode(), decoded_sig):
        raise HTTPException(401, 'Invalid signature')
    claims = jwt.get_unverified_claims(token)
    if claims.get('exp', 0) < time.time():
        raise HTTPException(401, 'Token expired')
    if CLIENT_ID not in claims.get('aud', []):
        raise HTTPException(401, 'Invalid audience')
    roles = claims.get('realm_access', {}).get('roles', [])
    if 'prothetic_user' not in roles:
        raise HTTPException(403, 'Forbidden')
    return claims

@app.get('/reports')
def get_reports(user: dict = Depends(verify_token)):
    # произвольный отчёт
    return {
        'user': user.get('preferred_username'),
        'report': {
            'timestamp': int(time.time()),
            'data': [
                {'metric': 'signal_strength', 'value': 0.87},
                {'metric': 'response_time_ms', 'value': 95}
            ]
        }
    }