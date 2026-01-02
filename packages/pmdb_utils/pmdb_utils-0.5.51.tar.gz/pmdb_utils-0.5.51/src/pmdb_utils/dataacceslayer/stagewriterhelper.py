from .storageclient import StorageClient
from .storageoptions import StorageOptions
from datetime import datetime
import io


class StageWriterHelper:
    def __init__(
        self,
        source_system: str,
        table_name: str,
        storage_options=None,
        bucket: str = "lakehouse",
        base_path: str = "landing",
    ):
        self.source_system: str = source_system
        self.table_name: str = table_name
        self.storage_options = storage_options
        self.set_storage_options()
        self.storage_client: StorageClient = StorageClient(
            storage_options=self.storage_options
        )
        self.datetime_int = int(datetime.now().strftime("%Y%m%d%H%M%S"))
        self.bucket = bucket
        self.base_path = base_path
        pass

    @property
    def write_path(self):
        return f"s3://{self.bucket}/{self.base_path}/{self.source_system}/{self.table_name}/{self.datetime_int}/file.parquet"

    def set_storage_options(self):
        if self.storage_options is None:
            self.storage_options = StorageOptions().minio

    def drop_done_file(self):
        object_name: str = f"{self.base_path}/{self.source_system}/done.txt"
        file_content = f"{self.source_system},{self.datetime_int}".encode('utf-8')
        data = io.BytesIO(file_content)
        self.storage_client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=data,
            length=len(file_content),
            content_type="text/plain",
        )
