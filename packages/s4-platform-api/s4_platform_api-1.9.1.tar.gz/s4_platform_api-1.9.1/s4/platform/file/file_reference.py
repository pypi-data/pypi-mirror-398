from __future__ import annotations

from io import BytesIO
from typing import Optional, BinaryIO, Union

import requests
from marshmallow import fields as marshmallow_fields

from s4.platform.connection import Connection
from s4.platform.internal.base_model import GraphModel, ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema


class FileReference(GraphModel, ConnectedModel):
    def __init__(
        self,
        *,
        connection: Connection = None,
        iri: Optional[str],
        file_name: Optional[str],
        file_reference_type: Optional[str],
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
    ):
        GraphModel.__init__(self, iri)
        ConnectedModel.__init__(self, connection)
        self.file_name = file_name
        self.file_reference_type = file_reference_type
        self.s3_key = s3_key
        self.s3_bucket = s3_bucket

    @staticmethod
    def new_s3(
        connection: Connection,
        filename: Optional[str] = None,
        aws_file_path: Optional[str] = None,
    ) -> "FileReference":
        """
        POST a new s3 fileReference to the API, return an instance of FileReference
        """

        request_body = {"fileName": filename, "fileReferenceType": "AWS_S3"}

        if aws_file_path:
            request_body["s3Key"] = aws_file_path

        data = connection.post_json("/fileReference", request_body)
        schema = FileReferencePostSchema()
        return FileReference._from_json(connection, data, schema)

    @staticmethod
    def from_iri(connection: Connection, iri: str) -> "FileReference":
        """
        GET a fileReference from the API, return an instance of FileReference
        """
        data = connection.fetch_json_from_iri(iri)
        schema = FileReferenceGetSchema()
        return FileReference._from_json(connection, data, schema)

    @staticmethod
    def _from_json(
        connection: Connection, json: dict, schema: ConnectedModelSchema
    ) -> FileReference:
        schema.context["connection"] = connection
        return schema.load(json)

    def get_presigned_get_url(self) -> str:
        """Generate presigned download url for API fileReference"""
        data = self.connection.fetch_json_from_iri(f"{self.iri}/getUrl")
        return data["preSignedUrl"]

    def get_presigned_put_url(self) -> str:
        """Generate presigned upload url for API fileReference"""
        data = self.connection.fetch_json_from_iri(f"{self.iri}/putUrl")
        return data["preSignedUrl"]

    def upload(self, contents: Union[bytes, BinaryIO]) -> None:
        """Upload contents to file, overwriting any existing contents.
        The contents can be raw bytes, or a readable file-like object.
        (The requests library will stream the upload of a file-like object
        automatically.)
        Example usage:

            with open('example.file', 'rb') as file:
                file_reference.upload(file)

        """
        url = self.get_presigned_put_url()
        response = requests.put(url, contents)
        Connection._handle_optional_json_response(response)

    def download(self, file: BinaryIO, chunk_size: int = 64 * 1024) -> None:
        """Download & return file's contents (by writing to the given writable
        file-like object).
        We use a streaming download, and chunk_size indicates the number of bytes
        to download per chunk.
        Example usage:

            with open('example.file', 'wb') as file:
                file_reference.download(file)

        """
        url = self.get_presigned_get_url()
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)


class FileReferencePostSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(FileReference, **kwargs)

    iri = marshmallow_fields.Str()
    file_name = marshmallow_fields.Str()
    file_reference_type = marshmallow_fields.Str()


class FileReferenceGetSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(FileReference, **kwargs)

    iri = marshmallow_fields.Str()
    file_name = marshmallow_fields.Str()
    file_reference_type = marshmallow_fields.Str()
    s3_key = marshmallow_fields.Str()
    s3_bucket = marshmallow_fields.Str()
