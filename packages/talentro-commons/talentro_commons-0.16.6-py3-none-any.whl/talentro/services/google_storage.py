import base64
import os
import traceback

from enum import StrEnum
from http import HTTPStatus

import tempfile

from fastapi import UploadFile
from google.api_core.exceptions import NotFound
from google.cloud import storage
from google.cloud.storage import Bucket, Blob

from talentro.constants import ErrorCode, DisplayMessage
from talentro.exceptions import APIException
from ..general.dataclasses import FileData

from ..util.singleton import SingletonMeta
from ..util.string import render_template_path


class BucketEnum(StrEnum):
    PUBLIC = "talentro-static"
    BILLING = "talentro-billing"
    CANDIDATES = "talentro-candidates"


class FilePathEnum(StrEnum):
    IAM_ORGANIZATION_LOGO = "iam/organizations/{organization_id}/details/logo.{extension}"
    IAM_PROFILE_PICTURE = "iam/users/{user_id}/profile/profile_picture.{extension}"
    CANDIDATES_CANDIDATE_CV_FILE = "organizations/{organization_id}/cand_{candidate_id}/cv/{file_name}"
    CANDIDATES_CANDIDATE_CV_FOLDER = "organizations/{organization_id}/cand_{candidate_id}/cv/"


class GoogleStorage(metaclass=SingletonMeta):

    def __init__(self):
        self._client = storage.Client()

    def upload_base64_to_gcs(self, file: FileData, bucket: BucketEnum, destination: FilePathEnum, path_definitions: dict) -> Blob:
        file_bytes = base64.b64decode(file.data)

        _, ext = os.path.splitext(file.file_name)
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(tmp_fd)

        try:
            blob = self._get_blob(bucket, destination, path_definitions)

            with open(tmp_path, "wb") as f:
                f.write(file_bytes)

            blob.upload_from_filename(
                tmp_path,
                content_type=file.content_type  # handig voor GCS metadata
            )

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            return blob
        except Exception as e:
            print(e)
            traceback.print_exc()

    def _get_bucket(self, bucket: BucketEnum) -> Bucket:
        try:
            bucket = self._client.get_bucket(bucket.value)
        except NotFound:
            print("Bucket not found.")
            bucket = self._client.create_bucket(bucket.value)

        return bucket

    def _get_blob(self, bucket: BucketEnum, destination: FilePathEnum, path_definitions: dict):
        bucket = self._get_bucket(bucket)

        try:
            filled_destination_path = render_template_path(destination, path_definitions)

        except ValueError as e:
            raise APIException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                display_message=DisplayMessage.UNKNOWN_ERROR,
                message=str(e),
                error_code=ErrorCode.UNKNOWN_ERROR
            )

        blob = bucket.blob(filled_destination_path)
        return blob

    def get_blob(self, bucket: BucketEnum, destination: FilePathEnum, path_definitions: dict) -> Blob:
        """Deletes a blob from the bucket."""
        blob = self._get_blob(bucket, destination, path_definitions)
        blob.reload()
        return blob

    def delete_file(self, bucket: BucketEnum, destination: FilePathEnum, path_definitions: dict) -> bool:
        """Deletes a blob from the bucket."""
        try:
            blob = self._get_blob(bucket, destination, path_definitions)
            blob.reload()
            generation_match_precondition = blob.generation
            blob.delete(if_generation_match=generation_match_precondition)
            return True
        except NotFound as e:
            print(e)
            traceback.print_exc()
            return False

    def delete_folder(self, bucket: BucketEnum, destination: FilePathEnum, path_definitions: dict) -> bool:
        """Deletes a blob from the bucket."""
        try:
            bucket = self._get_bucket(bucket)
            filled_destination_path = render_template_path(destination, path_definitions)

            blobs = list(bucket.list_blobs(prefix=filled_destination_path))
            if blobs:
                bucket.delete_blobs(blobs)

            return True
        except NotFound as e:
            print(e)
            traceback.print_exc()
            return False

    def upload_file(self, file: UploadFile, bucket: BucketEnum, destination: FilePathEnum, path_definitions: dict) -> Blob:
        """
        Uploads a file to Google Storage

        :param file: The file you want to upload.
        :param bucket: The bucket you want to upload to.
        :param destination: The file destination you want to upload to.
        :param path_definitions: Key-value pair to declare the dynamic parts of the destination path.
        :return: The public URL of the uploaded file.
        :rtype: str
        """
        # Get the bucket or create it if it doesn't exist.
        blob = self._get_blob(bucket, destination, path_definitions)

        blob.upload_from_file(file.file)

        return blob
