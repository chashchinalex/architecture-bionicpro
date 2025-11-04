from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import psycopg2
import os

# Настройки для Keycloak
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "reports-frontend")
KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "http://keycloak:8080/realms/reports-realm")
KEYCLOAK_PUBLIC_KEY = os.getenv("KEYCLOAK_PUBLIC_KEY")

# FastAPI приложение
app = FastAPI(title="Reports API")

# Простая аутентификация через токен (Bearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    """Проверяем JWT, выданный Keycloak"""
    try:
        # У Keycloak публичный ключ публикуется в jwks.json,
        # но для простоты можно зашить вручную через env.
        payload = jwt.decode(
            token,
            f"-----BEGIN PUBLIC KEY-----\n{KEYCLOAK_PUBLIC_KEY}\n-----END PUBLIC KEY-----",
            algorithms=["RS256"],
            audience=KEYCLOAK_CLIENT_ID,
            issuer=KEYCLOAK_ISSUER
        )
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token invalid: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No subject in token")
    return user_id

# Пример соединения с Postgres (OLAP)
def get_pg_connection():
    return psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow"
    )

@app.get("/reports")
def get_user_report(user_id: str, current_user: str = Depends(verify_token)):
    """
    Возвращает данные отчёта по пользователю.
    Пользователь может видеть только свой отчёт.
    """
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Access denied: you can only view your own report")

    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, order_number, total, discount, buyer_id
        FROM sample_table
        WHERE buyer_id = %s;
    """, (user_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"user_id": user_id, "records": data}