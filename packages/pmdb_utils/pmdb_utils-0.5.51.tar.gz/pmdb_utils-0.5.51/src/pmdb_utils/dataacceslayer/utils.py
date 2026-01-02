import polars as pl
from .storageoptions import StorageOptions


def read_minio_data(
    path: str, env: str = None, file_type: str = "delta", **kwargs
) -> pl.DataFrame:
    """Reads data from MinIO storage using Polars.

    This function supports reading Delta and Parquet files from MinIO by automatically
    configuring the necessary storage options based on the environment.

    Args:
        path (str): The path to the file in MinIO.
        env (str, optional): The environment name for storage configuration. Defaults to None.
        file_type (str, optional): The file format to read. Supported: "delta", "parquet". Defaults to "delta".
        **kwargs: Additional keyword arguments passed to the underlying Polars read function
            (pl.read_delta or pl.read_parquet).

    Returns:
        pl.DataFrame: The loaded DataFrame.

    Raises:
        ValueError: If an unsupported file_type is provided.
    """
    storage_options = StorageOptions(env=env).minio
    if file_type == "delta":
        df = pl.read_delta(path, storage_options=storage_options, **kwargs)
        return df
    elif file_type == "parquet":
        df = pl.read_parquet(path, storage_options=storage_options, **kwargs)
        return df
    elif file_type == "csv":
        df = pl.read_csv(path, storage_options=storage_options, **kwargs)
        return df
    elif file_type == "json":
        df = pl.read_json(path, storage_options=storage_options, **kwargs)
        return df
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
