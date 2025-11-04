from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
import psycopg2
import requests
import os

# ---------------------------------------------------------------------
# Настройки окружения
# ---------------------------------------------------------------------
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", f"http://keycloak:8080/realms/{KEYCLOAK_REALM}")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "reports-api")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_PUBLIC_KEY = os.getenv("KEYCLOAK_PUBLIC_KEY")

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "airflow")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASS = os.getenv("DB_PASS", "airflow")

# ---------------------------------------------------------------------
# Создание приложения FastAPI
# ---------------------------------------------------------------------
app = FastAPI(title="Reports API")

# Разрешаем запросы от фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Проверка токена через Keycloak Introspection Endpoint
# ---------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            f"-----BEGIN PUBLIC KEY-----\n{KEYCLOAK_PUBLIC_KEY}\n-----END PUBLIC KEY-----",
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            options={"verify_aud": False}
        )
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No subject in token")

    return "648821"

# ---------------------------------------------------------------------
# Подключение к Postgres
# ---------------------------------------------------------------------
def get_pg_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# ---------------------------------------------------------------------
# Эндпоинт /reports
# ---------------------------------------------------------------------
@app.get("/reports")
def get_user_report(
    user_id: str = Query(..., description="ID пользователя"),
    current_user: str = Depends(verify_token)
):
    """
    Отчёт по пользователю.
    Пользователь может видеть только свой собственный отчёт.
    """
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Access denied: can only view your own report")

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, order_number, total, discount, buyer_id
        FROM sample_table
        WHERE buyer_id = %s
        """,
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    records = [
        {
            "id": r[0],
            "order_number": r[1],
            "total": float(r[2]),
            "discount": float(r[3]),
            "buyer_id": r[4],
        }
        for r in rows
    ]

    return {"user_id": user_id, "records": records}

# ---------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}