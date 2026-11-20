from io import BytesIO

import pandas as pd
import pytest
from botocore.exceptions import ClientError

from services import aws_service


class FakeS3Client:
    def __init__(self, get_result=None, get_error=None, put_error=None):
        self.get_result = get_result
        self.get_error = get_error
        self.put_error = put_error

    def get_object(self, **_kwargs):
        if self.get_error:
            raise self.get_error
        return self.get_result

    def put_object(self, **_kwargs):
        if self.put_error:
            raise self.put_error


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "GetObject")


def test_read_file_s3_returns_empty_frame_only_for_missing_object(monkeypatch):
    monkeypatch.setattr(
        aws_service.boto3,
        "client",
        lambda *_args, **_kwargs: FakeS3Client(get_error=client_error("NoSuchKey")),
    )

    result = aws_service.read_file_s3("articles.csv")

    assert result.empty
    assert list(result.columns) == aws_service.COLUMNS


def test_read_file_s3_propagates_unexpected_client_errors(monkeypatch):
    error = client_error("AccessDenied")
    monkeypatch.setattr(
        aws_service.boto3,
        "client",
        lambda *_args, **_kwargs: FakeS3Client(get_error=error),
    )

    with pytest.raises(ClientError) as raised:
        aws_service.read_file_s3("articles.csv")

    assert raised.value is error


def test_read_file_s3_reads_existing_csv(monkeypatch):
    body = BytesIO(b"unique_id,title\nFOX5-1,Example\n")
    monkeypatch.setattr(
        aws_service.boto3,
        "client",
        lambda *_args, **_kwargs: FakeS3Client(get_result={"Body": body}),
    )

    result = aws_service.read_file_s3("articles.csv")

    assert result.to_dict(orient="records") == [
        {"unique_id": "FOX5-1", "title": "Example"}
    ]


def test_upload_file_s3_propagates_failures(monkeypatch):
    error = client_error("AccessDenied")
    monkeypatch.setattr(
        aws_service.boto3,
        "client",
        lambda *_args, **_kwargs: FakeS3Client(put_error=error),
    )

    with pytest.raises(ClientError) as raised:
        aws_service.upload_file_s3(pd.DataFrame([{"id": "1"}]), "articles.csv")

    assert raised.value is error
