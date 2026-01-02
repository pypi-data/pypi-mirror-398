import sys
from pathlib import Path
from typing import Dict, Optional, Any
import logging
import json
from ..metadata.utils import convert_metadata_to_polars_type
import polars as pl
from ..dataacceslayer.storageclient import StorageClient
from ..dataacceslayer.enum_config import TablePathBasic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


class MetadataReaderError(Exception):
    """Custom exception for MetadataReader errors"""

    pass


class MetaDataReader:
    """
    A class to read and process metadata from various storage backends.

    Supports multiple storage clients and provides metadata loading capabilities.
    """

    def __init__(
        self, storage_options, source_system: str = None, table_name: str = None
    ):
        """
        Initialize MetadataReader.

        Args:
            meta_path: Path to metadata file
            storage_options: Storage configuration options
            storage_client: Type of storage client ('minio', 's3', 'local')

        Raises:
            MetadataReaderError: If invalid storage client or missing required options
        """
        self.storage_options = storage_options
        self.source_system: str = source_system
        self.table_name: str = table_name
        self.object_name = (
            TablePathBasic.metadata_path + "/" + self.source_system + ".json"
        )
        self._meta_data: Optional[Dict[str, Any]] = None
        self._meta_data_polars: Dict[str, pl.DataType] = {}
        self.storage_client = StorageClient(storage_options=self.storage_options)
        self.dataset = self.get_table_metadata(self.table_name)

    def load_metadata(self) -> None:
        """
        Load metadata from the specified path.

        Raises:
            MetadataReaderError: If metadata loading fails
        """
        if self.meta_data is None:
            try:
                logger.info(f"Loading metadata from {self.object_name}")
                file_content = self.storage_client.get_object(
                    bucket_name=TablePathBasic.base_path, object_name=self.object_name
                )
                self._meta_data = json.load(file_content)
                if not self._meta_data:
                    raise MetadataReaderError("Loaded metadata is empty")

                self._convert_metadata_to_polars_types()
                logger.info("Metadata loaded and converted successfully")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in metadata file: {e}")
                raise MetadataReaderError(f"Invalid JSON in metadata file: {e}")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                raise MetadataReaderError(f"Failed to load metadata: {e}")

    def _convert_metadata_to_polars_types(self) -> None:
        """Convert metadata to Polars data types."""
        try:
            if self._meta_data is None:
                raise MetadataReaderError(
                    "Metadata not loaded. Call load_metadata() first."
                )

            self._meta_data_polars = convert_metadata_to_polars_type(
                self._meta_data, self.table_name
            )

        except Exception as e:
            logger.error(f"Failed to convert metadata to Polars types: {e}")
            raise MetadataReaderError(f"Failed to convert metadata: {e}")

    @property
    def meta_data(self) -> Optional[Dict[str, Any]]:
        """Get loaded metadata."""
        return self._meta_data

    @property
    def meta_data_polars(self) -> Dict[str, pl.DataType]:
        """Get metadata converted to Polars types."""
        return (
            self._meta_data_polars.copy()
        )  # Return copy to prevent external modification

    @property
    def is_loaded(self) -> bool:
        """Check if metadata has been loaded."""
        return self._meta_data is not None

    @property
    def table_file_type(self):
        self.load_metadata()
        return self.meta_data[0]["file_type"]

    def get_table_metadata(self, dataset_name: str) -> list:
        self.load_metadata()
        dataset = [
            d for d in self.meta_data[0]["datasets"] if d["name"] == dataset_name
        ]
        if dataset == []:
            error_msg: str = "No dataset found"
            logger.error(error_msg)
            raise Exception(error_msg)
        return dataset

    @property
    def table_columns_w_types(self) -> list:
        return self.dataset[0]["columns"]

    @property
    def table_load_type(self) -> list:
        return self.dataset[0]["load_type"]

    @property
    def table_partition_by_list(self) -> list:
        return self.dataset[0].get("partition_by", None)

    @property
    def table_columns_names(self) -> list:
        cols = self.table_columns_w_types(self.table_name)
        return [c["name"] for c in cols]

    @property
    def table_primary_keys_list(self) -> list:
        return self.dataset[0]["primary_keys"]

    @property
    def table_track_changes_columns(self) -> list:
        return self.dataset[0]["track_columns"]
