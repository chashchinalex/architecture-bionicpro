from uuid import uuid4
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import Auth
from settings import settings_auth


auth = Auth(
    url_keycloak=settings_auth.URL_KEYCLOAK,
    id_client=settings_auth.ID_CLIENT,
    name_realm=settings_auth.NAME_REALM,
    secret=settings_auth.SECRET,
)


app = FastAPI(
    title="BionicPro"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/reports")
def reports(roles = Depends(auth.get_roles)):
    if 'prothetic_user' not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    return JSONResponse([
        dict(
            id=str(uuid4()),
            text=f"Data {ind}",
        ) 
        for ind in range(10)
    ])


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
