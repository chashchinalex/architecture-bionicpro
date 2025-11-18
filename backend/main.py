import os
import uuid
import time
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime, date

import io
import json

import requests
import jwt
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from cryptography.fernet import Fernet

import psycopg2
from psycopg2.extras import RealDictCursor

from minio import Minio
from minio.error import S3Error

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")

OLAP_PG_DSN = os.getenv("OLAP_PG_DSN", "postgresql://airflow:airflow@postgres:5432/sample")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")

CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "sample-client")
CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "sample-secret")

SESSION_SECRET = os.getenv("REFRESH_TOKEN_ENC_KEY", Fernet.generate_key().decode())
SESSION_COOKIE_NAME = "session_id"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
SESSION_CIPHER = Fernet(SESSION_SECRET.encode())

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "user-reports")
S3_SECURE = os.getenv("S3_SECURE", "false").lower() == "true"
CDN_BASE_URL = os.getenv("CDN_BASE_URL", "http://localhost:8082")

OIDC_CONFIG_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"

_OIDC_CONFIG: Optional[dict] = None
_JWKS: Optional[dict] = None
_OLAP_CONN: Optional[psycopg2.extensions.connection] = None

s3_client = Minio(
    S3_ENDPOINT,
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=S3_SECURE,
)

if not s3_client.bucket_exists(S3_BUCKET):
    s3_client.make_bucket(S3_BUCKET)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_oidc_config_with_retry(retries: int = 10, delay: int = 3) -> dict:
    global _OIDC_CONFIG
    if _OIDC_CONFIG is not None:
        return _OIDC_CONFIG
    last_exc: Optional[Exception] = None
    for _ in range(retries):
        try:
            resp = requests.get(OIDC_CONFIG_URL, timeout=5)
            resp.raise_for_status()
            _OIDC_CONFIG = resp.json()
            return _OIDC_CONFIG
        except Exception as e:
            last_exc = e
            time.sleep(delay)
    raise HTTPException(status_code=500, detail=str(last_exc))


def get_token_endpoint() -> str:
    cfg = load_oidc_config_with_retry()
    return cfg["token_endpoint"]


def get_jwks_uri() -> str:
    cfg = load_oidc_config_with_retry()
    return cfg["jwks_uri"]


def get_logout_endpoint() -> Optional[str]:
    cfg = load_oidc_config_with_retry()
    return cfg.get("end_session_endpoint")


def load_jwks_with_retry(retries: int = 10, delay: int = 3) -> dict:
    global _JWKS
    if _JWKS is not None:
        return _JWKS
    jwks_uri = get_jwks_uri()
    last_exc: Optional[Exception] = None
    for _ in range(retries):
        try:
            resp = requests.get(jwks_uri, timeout=5)
            resp.raise_for_status()
            _JWKS = resp.json()
            return _JWKS
        except Exception as e:
            last_exc = e
            time.sleep(delay)
    raise HTTPException(status_code=500, detail=str(last_exc))


def decode_jwt_token(token: str) -> dict:
    jwks = load_jwks_with_retry()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header["kid"]
    key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if key_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=CLIENT_ID,
        options={"verify_exp": True},
    )


def create_session_token(data: dict) -> str:
    raw = jwt.encode(data, SESSION_SECRET, algorithm="HS256")
    return SESSION_CIPHER.encrypt(raw.encode()).decode()


def decode_session_token(token: str) -> dict:
    raw = SESSION_CIPHER.decrypt(token.encode()).decode()
    return jwt.decode(raw, SESSION_SECRET, algorithms=["HS256"])


def get_current_user(request: Request) -> Dict:
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = decode_session_token(cookie)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    exp = payload.get("exp")
    if exp and exp < int(time.time()):
        raise HTTPException(status_code=401, detail="Session expired")
    return payload


def get_olap_conn():
    global _OLAP_CONN
    if _OLAP_CONN is None or _OLAP_CONN.closed:
        _OLAP_CONN = psycopg2.connect(OLAP_PG_DSN)
        _OLAP_CONN.autocommit = True
    return _OLAP_CONN


def get_reports_for_email(email: str):
    query = """
        SELECT
            id,
            user_id,
            user_name,
            email,
            prosthesis_type,
            muscle_group,
            avg_signal_frequency,
            avg_signal_duration,
            avg_signal_amplitude,
            last_signal_time
        FROM sample.olap_table
        WHERE email = %s
        ORDER BY last_signal_time DESC
    """
    conn = get_olap_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (email,))
        return cur.fetchall()


def get_current_report_version() -> str:
    return time.strftime("%Y-%m-%d")


def build_report_key(email: str, version: str) -> str:
    safe_email = email.replace("/", "_")
    return f"reports/{safe_email}/report-{version}.json"


def get_report_from_s3(email: str, version: str) -> tuple[Optional[str], Optional[list]]:
    key = build_report_key(email, version)
    try:
        resp = s3_client.get_object(S3_BUCKET, key)
        data = resp.read()
        resp.close()
        resp.release_conn()
        rows = json.loads(data.decode("utf-8"))
        cdn_url = f"{CDN_BASE_URL}/{S3_BUCKET}/{key}"
        return cdn_url, rows
    except S3Error as e:
        if e.code in ("NoSuchKey", "NoSuchBucket"):
            return None, None
        raise



def json_default(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def save_report_to_s3(email: str, version: str, report_rows) -> str:
    key = build_report_key(email, version)
    data = json.dumps(report_rows, default=json_default).encode("utf-8")
    s3_client.put_object(
        S3_BUCKET,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type="application/json",
    )
    return f"{CDN_BASE_URL}/{S3_BUCKET}/{key}"



@app.get("/auth/login")
def auth_login():
    state = str(uuid.uuid4())
    auth_url = (
        f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"
        f"?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid profile email"
        f"&state={state}"
    )
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
def auth_callback(request: Request, response: Response, code: str, state: str):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }
    token_resp = requests.post(get_token_endpoint(), data=data)
    if token_resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Failed to get tokens")
    tokens = token_resp.json()
    id_token = tokens["id_token"]
    payload = decode_jwt_token(id_token)
    session = create_session_token(
        {
            "email": payload.get("email"),
            "preferred_username": payload.get("preferred_username"),
            "exp": int(time.time()) + SESSION_TTL_SECONDS,
        }
    )
    resp = RedirectResponse(url=FRONTEND_URL)
    resp.set_cookie(
        SESSION_COOKIE_NAME,
        session,
        httponly=True,
        secure=False,
        max_age=SESSION_TTL_SECONDS,
        samesite="Lax",
        path="/",
    )
    return resp


@app.get("/auth/me")
def auth_me(request: Request):
    user = get_current_user(request)
    return {"email": user["email"], "username": user.get("preferred_username")}


@app.get("/auth/logout")
def auth_logout(request: Request, response: Response):
    user = get_current_user(request)
    logout_url = get_logout_endpoint()
    resp = RedirectResponse(FRONTEND_URL)
    resp.delete_cookie(SESSION_COOKIE_NAME)
    if logout_url:
        return RedirectResponse(
            f"{logout_url}"
            f"?post_logout_redirect_uri={FRONTEND_URL}"
            f"&client_id={CLIENT_ID}"
        )
    return resp


@app.get("/reports")
def reports(request: Request):
    user = get_current_user(request)
    email = user["email"]
    version = get_current_report_version()

    cdn_url, rows = get_report_from_s3(email, version)
    if cdn_url is not None and rows is not None:
        return {
            "cdn_url": cdn_url,
            "source": "cache",
            "reports": rows,
        }

    rows = get_reports_for_email(email)
    cdn_url = save_report_to_s3(email, version, rows)

    return {
        "cdn_url": cdn_url,
        "source": "generated",
        "reports": rows,
    }

