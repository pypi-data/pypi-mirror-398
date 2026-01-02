from __future__ import annotations
from urllib.parse import urlparse


from typing import Mapping, Optional
from minio import Minio
from minio.commonconfig import CopySource


class StorageClient:
    """
    Storage client to read/write tabular data to/from storage backends.

    Parameters
    ----------
    file_path : str, optional
        Default path to read/write if none is provided to .read()/.write().
    file_type : str | None
        Explicit type like 'delta', 'parquet', 'csv'. If None, inferred from file extension.
    storage_options : Mapping[str, str] | None
        Extra options for remote storage backends (e.g., S3 credentials).
    """

    def __init__(
        self,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        storage_options: Optional[Mapping[str, str]] = None,
    ):
        self.file_path = file_path
        self.file_type = file_type.lower() if file_type else None
        self.storage_options = storage_options
        self.client: Minio = None
        self._set_client()

    # ---------------------------
    # client_config
    # ---------------------------
    def _set_client(self):
        # TODO: Must be a better way to do this to handle different venders
        endpoint_url = self.storage_options[
            "endpoint_url"
        ]  # e.g. "https://minio.mycorp.local:9000"
        parsed = urlparse(endpoint_url)

        self.client = Minio(
            parsed.netloc,
            access_key=self.storage_options["aws_access_key_id"],
            secret_key=self.storage_options["aws_secret_access_key"],
            secure=parsed.scheme == "https",
        )

    def fput_object(self, bucket_name: str, object_name: str, file_path: str, **kwargs):
        return self.client.fput_object(bucket_name, object_name, file_path, **kwargs)

    def put_object(
        self, bucket_name: str, object_name: str, data: str, length, **kwargs
    ):
        return self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data,
            length=length,
            **kwargs,
        )

    def list_objects(self, bucket_name: str, prefix: str, recursive: bool):
        return self.client.list_objects(bucket_name, prefix, recursive)

    def get_object(self, bucket_name: str, object_name: str, **kwargs):
        return self.client.get_object(
            bucket_name=bucket_name, object_name=object_name, **kwargs
        )

    def remove_object(self, bucket_name: str, object_name: str, **kwargs):
        return self.client.remove_object(
            bucket_name=bucket_name, object_name=object_name, **kwargs
        )

    def move_object(
        self, bucket_name: str, object_name: str, new_object_name: str, **kwargs
    ):
        source = CopySource(bucket_name, object_name)
        self.client.copy_object(
            bucket_name,
            new_object_name,
            source,
        )
        self.client.remove_object(bucket_name, object_name)

    def move_folder(
        self, bucket_name: str, folder_name: str, new_folder_name: str, **kwargs
    ):
        objects = self.client.list_objects(
            bucket_name, prefix=folder_name, recursive=True
        )
        for obj in objects:
            new_object_name = obj.object_name.replace(folder_name, new_folder_name, 1)
            # Skip if source and destination are the same
            if obj.object_name == new_object_name:
                continue
            source = CopySource(bucket_name, obj.object_name)
            self.client.copy_object(
                bucket_name,
                new_object_name,
                source,
            )
            self.client.remove_object(bucket_name, obj.object_name)
