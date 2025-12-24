import argparse
import csv
import logging
import random
import shutil
import time
from pathlib import Path


from PIL import Image

# Assuming your project structure allows this import.
# Adjust the path if necessary, e.g., from data.data_ingestion...
from restructure import Restructurer

# Configure logging for the runner script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_dummy_image_dataset(
    base_path: Path, num_images: int, image_size: tuple[int, int] = (64, 64)
) -> None:
    """
    Creates a dummy image classification dataset with the expected structure.

    Args:
        base_path: The directory where the dataset will be created.
        num_images: The total number of images to generate.
        image_size: The (width, height) of the generated images.
    """
    logger.info(
        f"Generating a dummy dataset with {num_images} images at '{base_path}'..."
    )

    # 1. Create directory structure
    images_dir = base_path / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    metadata = []
    headers = ["image_path", "label", "split"]
    labels = ["cat", "dog", "bird", "fish"]
    # Define split distribution: 70% train, 15% validation, 15% test
    split_distribution = ["train"] * 70 + ["validation"] * 15 + ["test"] * 15

    # 2. Generate images and metadata rows
    for i in range(num_images):
        image_name = f"image_{i:05d}.jpg"
        relative_image_path = f"images/{image_name}"
        absolute_image_path = base_path / relative_image_path

        # Create a simple dummy image
        img = Image.new("RGB", image_size, color=(i % 255, (i*5)%255, (i*10)%255))
        img.save(absolute_image_path)

        # Create metadata row
        row = {
            "image_path": relative_image_path,
            "label": random.choice(labels),
            "split": random.choice(split_distribution),
        }
        metadata.append(row)
    
    # 3. Write metadata.csv
    metadata_path = base_path / "metadata.csv"
    with open(metadata_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(metadata)

    logger.info("Dummy dataset generation complete.")


def verify_output(output_path: Path) -> bool:
    """
    Performs a basic check to see if the restructuring was successful.
    """
    logger.info(f"Verifying output at '{output_path}'...")
    if not output_path.is_dir():
        logger.error("Output path is not a directory.")
        return False

    # Check for the Spark success marker
    if not (output_path / "_SUCCESS").exists():
        logger.error("'_SUCCESS' file not found. Spark job may have failed.")
        return False
        
    # Check for split directories
    expected_splits = ["train", "test", "validation"]
    found_splits = [d.name for d in output_path.iterdir() if d.is_dir()]
    
    if not any(split in found_splits for split in expected_splits):
        logger.error(f"No split directories found in output. Found: {found_splits}")
        return False

    logger.info(f"Verification successful. Found splits: {found_splits}")
    return True


def main(args):
    """
    Main execution function.
    """
    # Use a temporary directory that is automatically cleaned up
    # with tempfile.TemporaryDirectory() as temp_dir:
    #     temp_path = Path(temp_dir)
    #     input_data_path = temp_path / "source_dataset"
    #     output_parquet_path = temp_path / "restructured_dataset"

    #     # 1. Build the temporary files
    #     create_dummy_image_dataset(input_data_path, args.num_images)

    #     # 2. Run and time the restructuring process
    #     logger.info("-" * 50)
    #     logger.info(
    #         f"Starting restructuring for 'image_classification' task with {args.num_images} images..."
    #     )
    #     start_time = time.perf_counter()

    #     try:
    #         run_restructuring(
    #             task_type="image_classification",
    #             input_path=input_data_path,
    #             output_path=output_parquet_path,
    #         )
    #     except Exception as e:
    #         logger.error(f"An error occurred during restructuring: {e}", exc_info=True)
    #         return  # Exit early on failure

    #     end_time = time.perf_counter()
    #     duration = end_time - start_time
    #     logger.info(f"Restructuring completed in {duration:.4f} seconds.")
    #     logger.info("-" * 50)

    #     # 3. Verify the output
    #     if not verify_output(output_parquet_path):
    #         logger.error("Restructuring process failed verification.")
    #     else:
    #         logger.info("Restructuring process completed and verified successfully.")

    # logger.info("Temporary directory and its contents have been cleaned up.")
    output_dir = (Path(__file__).parent / "restructure_test_output").resolve()

    # Clean up previous run's output to ensure a fresh start
    if output_dir.exists():
        logger.warning(f"Removing existing output directory: '{output_dir}'")
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(parents=True)
    
    input_data_path = output_dir / "source_dataset2"
    output_parquet_path = output_dir / "restructured_dataset2"

    logger.info(f"input_data_path: {input_data_path}")
    # 1. Build the temporary files
    create_dummy_image_dataset(input_data_path, args.num_images)

    # 2. Run and time the restructuring process
    logger.info("-" * 50)
    logger.info(
        f"Starting restructuring for 'image_classification' task with {args.num_images} images..."
    )
    start_time = time.perf_counter()

    try:
        restructurer = Restructurer(task_type="image_classification")
        summary = restructurer.restructure(
            input_path=input_data_path,
            output_path=output_parquet_path,
        )
    except Exception as e:
        logger.error(f"An error occurred during restructuring: {e}", exc_info=True)
        return  # Exit early on failure

    end_time = time.perf_counter()
    duration = end_time - start_time
    logger.info(f"Restructuring completed in {duration:.4f} seconds.")
    logger.info("-" * 50)

    print(f"summary: {summary}")

    # 3. Verify the output
    # generate_dataset_info(
    #         output_path=output_parquet_path,
    #         source_input_path=input_data_path, # Pass the original source data path
    #         dataset_name="dummy_image_classification",
    #         task_type="image_classification"
    #     )



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test runner for dataset restructuring performance.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=100,
        help="Number of dummy images to generate for the test.",
    )
    
    # You could add more arguments here to test other tasks in the future
    # parser.add_argument(
    #     "--task",
    #     type=str,
    #     default="image_classification",
    #     help="The restructuring task to run."
    # )

    args = parser.parse_args()
    main(args)