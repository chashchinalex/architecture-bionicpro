from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_bearer_token

from models import Report, ReportsResponse
from faker import Faker

app = FastAPI(title="Reports API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fake = Faker()


@app.get("/reports", response_model=ReportsResponse)
def get_reports(_=Depends(verify_bearer_token)):
    """Get a list of reports for the authenticated user with required role."""
    return ReportsResponse(
        reports=[
            Report(
                id=i + 1,
                title=fake.sentence(),
                created_at=fake.date_this_year(),
                summary=fake.paragraph(),
            )
            for i in range(10)
        ]
    )
