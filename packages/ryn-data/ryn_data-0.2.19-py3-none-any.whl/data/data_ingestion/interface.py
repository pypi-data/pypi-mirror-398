from .handlers.huggingface_handler import process_huggingface_dataset
from .handlers.kaggle_handler import process_kaggle_dataset
from .handlers.openml_handler import process_openml_dataset
from .handlers.s3_handler import S3Handler

def download_dataset(source: str, **kwargs):
    """
    Download and store a dataset from one of the supported sources.

    Args:
        source (str): One of 'huggingface', 'kaggle', 'openml', or 's3'.

        kwargs:
            Depending on the selected source, the following keyword arguments are required:

    **If source='huggingface'**:
            - `dataset_name` (str): Name of the dataset on HuggingFace.
            - `dataset_config` (str or None): Optional configuration name (can be None).
            - `dataset_name_override` (str): Name to use when storing the dataset.
            - `user_name` (str): Name of the user performing the ingestion.
            - `private` (bool): Whether to store the dataset as private.

    **If source='kaggle':**
                - Required arguments depend on the internal implementation of `process_kaggle_dataset()`.

    **If source='openml':**
                - `dataset_id` (int): OpenML dataset ID.
                - `dataset_name` (str): Name to use when storing the dataset.
                - `user_name` (str): Name of the user performing the ingestion.
                - `private` (bool): Whether to store the dataset as private.

    **If source='s3':**
                - `access_key` (str): AWS or S3-compatible access key.
                - `secret_key` (str): AWS or S3-compatible secret key.
                - `endpoint_url` (str): Endpoint URL of the S3-compatible service.
                - `bucket_name` (str): Name of the S3 bucket.
                - `s3_file_path` (str): Path to the dataset file in the S3 bucket.
                - `dataset_name` (str): Name to use when storing the dataset.
                - `user_name` (str): Name of the user performing the ingestion.
                - `private` (bool): Whether to store the dataset as private.

    Returns:
        dict: Information about the stored dataset, including status, message, dataset_id, and storage path.

    Example:
        from data.data_ingestion import download_dataset

        response = download_dataset(
            source="openml",
            dataset_id=31,
            dataset_name="credit-g",
            user_name="ryn",
            private=False
        )

        # Example response:
        {
            'status': 'success',
            'message': "OpenML dataset 'credit-g' stored.",
            'dataset_id': '534c5fb1-8d33-4ffb-b727-b41db4c242bd',
            'stored_path': '/PV_Datasets/534c5fb1-8d33-4ffb-b727-b41db4c242bd/credit-g.csv'
        }
    """

    if source == "huggingface":
        return process_huggingface_dataset(**kwargs)
    elif source == "kaggle":
        return process_kaggle_dataset(**kwargs)
    elif source == "openml":
        return process_openml_dataset(**kwargs)
    elif source == "s3":
        # Instantiate S3Handler with the required arguments
        s3_handler = S3Handler(
            access_key=kwargs["access_key"],
            secret_key=kwargs["secret_key"],
            endpoint_url=kwargs["endpoint_url"],
            bucket_name=kwargs["bucket_name"]
        )
        
        return s3_handler.process_s3_dataset(
            kwargs["s3_file_path"], kwargs["dataset_name"], kwargs["user_name"], kwargs["private"], kwargs["dataset_tag"]
        )
    else:
        raise ValueError(f"Unsupported source '{source}'. Supported sources are: huggingface, kaggle, openml, s3.")