from setuptools import setup, find_packages

setup(
    name="ryn-data",   # Your project/package name
    version="0.2.19",
    packages=find_packages(include=["data", "data.*"]),
    install_requires=[
        "pydantic",
        "boto3",
        "pandas",
        "datasets",
        "openml",
        "kagglehub",
        "fastapi",
        "opencv-python", #added
        "opencv-python-headless", #added
        "polars",
        "pydicom", #added
        "nibabel", #added
        "librosa", #added
        "pyspark",
        "elasticsearch<9",
        "ecs-logging",
        "clearml",
        "aipmodel==0.2.28"
    ],
    python_requires=">=3.8",
    description="SDK for data ingestion and platform utilities.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)