from typing import Annotated

from fastapi import APIRouter, Cookie

from bionicpro_auth.services.keycloak import KeycloakOpenIdService
from bionicpro_auth.services.reports import ReportService
from bionicpro_auth.services.s3_storage import S3Storage

router = APIRouter(prefix="/reports")


@router.get("/my")
async def get_my_report(
    session_key: Annotated[str | None, Cookie()] = None,
):
    koi_service = KeycloakOpenIdService()
    s3_storage = S3Storage()
    if not session_key:
        raise ValueError

    username = await koi_service.get_username(session_key)

    if not (report_url := s3_storage.find_report(username)):
        with ReportService() as report_service:
            report_data = report_service.load_report(username)
        return s3_storage.load_report(username, report_data)

    return report_url.replace("s3", "localhost")
