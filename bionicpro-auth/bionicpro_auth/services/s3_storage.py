import io

from boto3 import Session
from botocore.exceptions import ClientError


class S3Storage:
    def find_report(self, username: str) -> str | None:
        session = Session(
            aws_access_key_id="reports-access", aws_secret_access_key="reports-secret"
        )
        s3_client = session.client("s3", endpoint_url="http://s3:9000")
        try:
            s3_client.head_object(
                Bucket="reports",
                Key=username + "-report.json",
            )

        except ClientError as e:
            return None

        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": "reports", "Key": username + "-report.json"},
            ExpiresIn=60 * 60 * 24,
        )

    def load_report(self, username: str, report_data: str) -> str:
        session = Session(
            aws_access_key_id="reports-access", aws_secret_access_key="reports-secret"
        )
        s3_client = session.client("s3", endpoint_url="http://s3:9000")

        json_bytes = report_data.encode("utf-8")
        output_buffer = io.BytesIO(json_bytes)

        s3_client.upload_fileobj(
            Fileobj=output_buffer,
            Bucket="reports",
            Key=username + "-report.json",
        )

        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": "reports", "Key": username + "-report.json"},
            ExpiresIn=60 * 60 * 24,
        )
