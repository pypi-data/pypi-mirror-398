from pathlib import Path
from typing import Generator

import polars as pl
import pytest

# Make sure your file_converter.py is in the same directory or accessible via PYTHONPATH
from data.data_restructure.file_convert import FileConverter

# --- Pytest Fixture for Test Setup ---


@pytest.fixture
def converter_setup(tmp_path: Path) -> Generator:
    """
    Sets up a temporary directory with test files for each test function.

    This fixture provides a clean, isolated environment for each test case,
    ensuring that tests do not interfere with each other.

    Yields:
        A dictionary containing the FileConverter instance and paths to test files.
    """
    # Create a FileConverter instance
    converter = FileConverter()

    # Define paths for dummy files within the temporary directory
    csv_to_replace_path = tmp_path / "data_to_replace.csv"
    csv_to_keep_path = tmp_path / "data_to_keep.csv"
    unsupported_file_path = tmp_path / "notes.txt"
    preexisting_parquet_path = tmp_path / "data_to_replace.parquet"

    # Create dummy file content
    csv_content = "id,name,value\n1,alpha,100\n2,beta,200"
    txt_content = "This file should not be converted."

    # Write the dummy files
    csv_to_replace_path.write_text(csv_content)
    csv_to_keep_path.write_text(csv_content)
    unsupported_file_path.write_text(txt_content)

    # Yield the setup objects to the test function
    yield {
        "converter": converter,
        "csv_replace_path": csv_to_replace_path,
        "csv_keep_path": csv_to_keep_path,
        "unsupported_path": unsupported_file_path,
        "preexisting_parquet_path": preexisting_parquet_path,
        "temp_dir": tmp_path,
    }
    # Teardown (cleaning up the temp dir) is handled automatically by pytest's tmp_path


# --- Test Cases ---


def test_csv_to_parquet_replaces_source_by_default(converter_setup):
    """
    Tests the default conversion behavior: CSV to Parquet, replacing the source.
    """
    converter = converter_setup["converter"]
    source_path = converter_setup["csv_replace_path"]
    expected_dest_path = source_path.with_suffix(".parquet")

    # Act: Perform the conversion
    result_path = converter.convert(source_path)

    # Assert
    assert result_path == expected_dest_path
    assert expected_dest_path.exists(), "Parquet file was not created."
    assert not source_path.exists(), "Source CSV file was not deleted."
    # Verify content
    df = pl.read_parquet(result_path)
    assert df.shape == (2, 3)
    assert df["name"][0] == "alpha"


def test_csv_to_parquet_keeps_source_when_specified(converter_setup):
    """
    Tests that setting `replace_source=False` successfully converts the file
    but leaves the original source file intact.
    """
    converter = converter_setup["converter"]
    source_path = converter_setup["csv_keep_path"]
    expected_dest_path = source_path.with_suffix(".parquet")

    # Act: Perform the conversion without replacing the source
    result_path = converter.convert(source_path, replace_source=False)

    # Assert
    assert result_path == expected_dest_path
    assert expected_dest_path.exists(), "Parquet file was not created."
    assert source_path.exists(), "Source CSV file should not have been deleted."


def test_no_conversion_for_unmapped_file_type(converter_setup):
    """
    Tests that a file with an extension not in CONVERSION_MAP is ignored,
    and the original path is returned.
    """
    converter = converter_setup["converter"]
    source_path = converter_setup["unsupported_path"]

    # Act: Attempt to convert the file
    result_path = converter.convert(source_path)

    # Assert
    assert result_path == source_path, "Path should be unchanged for unsupported files."
    assert source_path.exists(), "Unsupported file should not be deleted."
    # Check that no stray parquet file was created
    assert not source_path.with_suffix(".parquet").exists()


def test_skips_conversion_if_destination_exists(converter_setup):
    """
    Tests that the conversion is skipped if the target file already exists.
    """
    converter = converter_setup["converter"]
    source_path = converter_setup["csv_replace_path"]
    dest_path = converter_setup["preexisting_parquet_path"]

    # Arrange: Create a dummy destination file beforehand
    dest_path.write_text("pre-existing file")
    original_content = dest_path.read_text()

    # Act: Attempt the conversion
    result_path = converter.convert(source_path)

    # Assert
    assert result_path == dest_path
    assert source_path.exists(), (
        "Source file should not be deleted if conversion is skipped."
    )
    assert dest_path.read_text() == original_content, (
        "Pre-existing file should not be modified."
    )


def test_raises_file_not_found_error_for_nonexistent_source(converter_setup):
    """
    Tests that a FileNotFoundError is raised if the source file does not exist.
    """
    converter = converter_setup["converter"]
    non_existent_path = converter_setup["temp_dir"] / "ghost.csv"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        converter.convert(non_existent_path)


def test_raises_not_implemented_error_for_missing_handler(converter_setup, monkeypatch):
    """
    Tests that a NotImplementedError is raised if a conversion is defined in
    the map but has no corresponding handler function.
    """
    converter = converter_setup["converter"]
    source_path = converter_setup["unsupported_path"].with_suffix(".json")
    source_path.write_text("{}")  # create a dummy json file

    # Arrange: Add a new conversion rule without adding a handler for it
    monkeypatch.setitem(converter.CONVERSION_MAP, ".json", ".parquet")

    # Act & Assert
    with pytest.raises(
        NotImplementedError,
        match="No conversion handler implemented for .json -> .parquet",
    ):
        converter.convert(source_path)


def test_conversion_io_error_handling(converter_setup, monkeypatch):
    """
    Tests that an IOError during conversion is properly raised.
    """
    converter = converter_setup["converter"]
    source_path = converter_setup["csv_replace_path"]

    def mock_conversion_fail(*args, **kwargs):
        raise IOError("Simulated conversion failure.")

    monkeypatch.setitem(
        converter._conversion_handlers, (".csv", ".parquet"), mock_conversion_fail
    )

    # Act & Assert
    with pytest.raises(IOError, match="Simulated conversion failure."):
        converter.convert(source_path)
