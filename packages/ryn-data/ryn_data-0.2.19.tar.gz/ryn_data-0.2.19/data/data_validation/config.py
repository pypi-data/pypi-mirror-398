

validation_config = [
        {
            "name": "Validate User CSVs",
            "path_pattern": "**/*.csv",
            "validator": "tabular",
        },
        {
            "name": "Validate Transaction Parquet Files",
            "path_pattern": "**/*.parquet",
            "validator": "tabular",
        },
        {
            "name": "Validate for Image files",
            "path_pattern": "**/*.jpg",
            "validator": "image",
        },
        {
            "name": "Validate for Image files(png)",
            "path_pattern": "**/*.png",
            "validator": "image",
        },
        {
            "name": "Validate for JSON files",
            "path_pattern": "**/*.json",
            "validator": "json",  # Assuming a JSON validator exists
        },
        {
            "name": "Validate for JSON files(jsonl)",
            "path_pattern": "**/*.jsonl",
            "validator": "json",  # Assuming a JSON validator exists
        },
        {
            "name": "Validate for Audio files",
            "path_pattern": "**/*.wav",
            "validator": "audio",  # Assuming an Audio validator exists
        },
        {
            "name": "Validate for Audio files(mp3)",
            "path_pattern": "**/*.mp3",
            "validator": "audio",  # Assuming an Audio validator exists
        },
        {
            "name": "Validate for Text files",
            "path_pattern": "**/*.txt",
            "validator": "text",  # Assuming a Text validator exists
        },
        {
            "name": "validate for numpy files",
            "path_pattern": "**/*.npy",
            "validator": "numpy",  # Assuming a NPY validator exists
        },
        {
            "name": "validate for npz files",
            "path_pattern": "**/*.npz",
            "validator": "numpy",  # Assuming a NPZ validator exists
        },
        {
            "name": "Validate for Markdown files",
            "path_pattern": "**/*.md",
            "validator": "markdown",  # Using TextValidator for markdown files
        },
        {
            "name": "Validate for DICOM files",
            "path_pattern": "**/*.dcm",
            "validator": "dicom",  # Assuming a DICOM validator exists
        },
        {
            "name": "Validate for nifti files",
            "path_pattern": "**/*.nii",
            "validator": "nifti",  # Assuming a NIfTI validator exists
        },
        {
            "name": "Validate for nifti files(gz)",
            "path_pattern": "**/*.nii.gz",
            "validator": "nifti",  # Assuming a NIfTI validator exists
        },
    ]