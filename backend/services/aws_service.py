import boto3
import os
import pandas as pd
from botocore.exceptions import ClientError
from io import StringIO

COLUMNS = [
    "id",
    "web_id",
    "title",
    "link",
    "date_posted",
    "summary",
    "source",
    "text",
    "unique_id",
    "created_at",
    "updated_at",
    "is_relevant",
    "collision_location",
    "collision_date",
]


def upload_file_s3(df, file_name) -> None:
    """Upload a dataframe as CSV to an S3 object.

    Errors intentionally propagate so callers never mistake a failed write for success.
    """

    buffer = StringIO()
    df.to_csv(buffer, index=False)

    # Upload the file
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    bucket = os.getenv("S3_BUCKET")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    s3_client.put_object(Bucket=bucket, Key=file_name, Body=buffer.getvalue())


def read_file_s3(file_name) -> pd.DataFrame:
    """Read an S3 CSV object, returning an empty schema only when it is absent.

    Authentication, networking, and service errors intentionally propagate so a
    caller cannot overwrite existing data after mistaking a failed read for an
    empty object.
    """
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    bucket_name = os.getenv("S3_BUCKET")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"NoSuchKey", "404"}:
            return pd.DataFrame(columns=COLUMNS)
        raise

    return pd.read_csv(response["Body"])
