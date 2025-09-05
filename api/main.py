from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
from jwt import PyJWKClient
import requests
from datetime import datetime, timedelta
import json
import random
from typing import Dict, Any, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

KEYCLOAK_URL = "http://keycloak:8080"
REALM = "reports-realm"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"

jwks_client = PyJWKClient(JWKS_URL)

def verify_token(request: Request):
    print(f"=== TOKEN VERIFICATION START ===")
    print(f"Request headers: {dict(request.headers)}")
    
    authorization = request.headers.get("Authorization")
    if not authorization:
        print("ERROR: No Authorization header found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        print(f"ERROR: Invalid Authorization format: {authorization[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format"
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    print(f"Token received (first 50 chars): {token[:50]}...")
    
    try:
        # First try to decode without verification to see the content
        print("Attempting to decode token without verification...")
        unverified = jwt.decode(token, options={"verify_signature": False})
        print(f"Unverified token content: {unverified}")
        
        # Now verify with signature
        print("Getting signing key...")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print("Signing key obtained, decoding with verification...")
        
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": False, "verify_aud": False}  # Temporarily disable exp check
        )
        print(f"Token decoded successfully: {decoded_token.get('preferred_username', 'unknown')}")
        return decoded_token
    except jwt.InvalidTokenError as e:
        print(f"JWT Invalid Token Error: {str(e)}")
        print(f"Full exception: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        print(f"Token validation exception: {str(e)}")
        print(f"Full exception: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )

def check_prothetic_user_role(token_data: Dict[str, Any]):
    realm_access = token_data.get("realm_access", {})
    roles = realm_access.get("roles", [])
    
    if "prothetic_user" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Prothetic user role required."
        )
    
    return token_data

def generate_sample_report_data():
    current_time = datetime.now()
    
    users_data = []
    for i in range(random.randint(10, 50)):
        user_id = f"user_{i:03d}"
        sessions_count = random.randint(1, 20)
        total_time = random.randint(30, 3600)  # 30 seconds to 1 hour
        
        users_data.append({
            "user_id": user_id,
            "sessions_count": sessions_count,
            "total_usage_time_seconds": total_time,
            "average_session_duration": round(total_time / sessions_count, 2),
            "last_activity": (current_time - timedelta(days=random.randint(0, 30))).isoformat()
        })
    
    summary_stats = {
        "total_users": len(users_data),
        "total_sessions": sum(user["sessions_count"] for user in users_data),
        "total_usage_hours": round(sum(user["total_usage_time_seconds"] for user in users_data) / 3600, 2),
        "average_sessions_per_user": round(sum(user["sessions_count"] for user in users_data) / len(users_data), 2),
        "report_generated_at": current_time.isoformat(),
        "report_period": {
            "start_date": (current_time - timedelta(days=30)).isoformat(),
            "end_date": current_time.isoformat()
        }
    }
    
    return {
        "summary": summary_stats,
        "users": users_data
    }

@app.get("/")
async def root():
    return {"message": "Reports API"}

@app.get("/reports")
async def get_reports(request: Request):
    print("=== REPORTS ENDPOINT CALLED ===")
    try:
        print(f"Request headers: {dict(request.headers)}")
        token_data = verify_token(request)
        check_prothetic_user_role(token_data)
        
        report_data = generate_sample_report_data()
        
        return {
            "status": "success",
            "data": report_data,
            "requested_by": {
                "username": token_data.get("preferred_username"),
                "email": token_data.get("email"),
                "roles": token_data.get("realm_access", {}).get("roles", [])
            }
        }
    except Exception as e:
        print(f"Error in reports endpoint: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)