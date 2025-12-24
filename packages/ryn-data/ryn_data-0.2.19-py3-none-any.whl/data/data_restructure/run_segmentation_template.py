import argparse
import csv
import logging
import random
import shutil
import time
from pathlib import Path

from PIL import Image

from data.data_restructure.restructure import Restructurer


# Configure logging for the runner script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_dummy_segmentation_dataset(
    base_path: Path, num_samples: int, image_size: tuple[int, int] = (128, 128)
) -> None:
    """
    Creates a dummy Image Segmentation dataset with the expected structure
    (images/, masks/, metadata.csv).

    Args:
        base_path: The directory where the dataset will be created.
        num_samples: The total number of image/mask pairs to generate.
        image_size: The (width, height) of the generated images.
    """
    logger.info(
        f"Generating a dummy segmentation dataset with {num_samples} samples at '{base_path}'..."
    )

    # 1. Create directory structure
    images_dir = base_path / "images"
    masks_dir = base_path / "masks"
    images_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)

    metadata = []
    headers = ["image_path", "mask_path", "split"]

    # Define split distribution: 70% train, 15% validation, 15% test
    split_distribution = ["train"] * 70 + ["validation"] * 15 + ["test"] * 15

    # 2. Generate images, masks, and metadata rows
    for i in range(num_samples):
        # Image details
        scene_name = f"scene_{i:05d}"
        image_name = f"{scene_name}.jpg"
        relative_image_path = f"images/{image_name}"
        absolute_image_path = images_dir / image_name

        # Mask details
        mask_name = f"{scene_name}_mask.png"
        relative_mask_path = f"masks/{mask_name}"
        absolute_mask_path = masks_dir / mask_name

        # --- Create Dummy Files ---
        # 1. Image (RGB)
        img = Image.new("RGB", image_size, color=(100 + i % 100, 50, 150))
        # Draw a simple shape to make it slightly non-uniform
        for x in range(image_size[0] // 4):
            for y in range(image_size[1] // 4):
                img.putpixel((x, y), (255, 0, 0))
        img.save(absolute_image_path)

        # 2. Mask (L mode - Grayscale, common for masks)
        mask = Image.new("L", image_size, color=0) # Black background
        # Draw a white square segment (value 255)
        for x in range(image_size[0] // 2, image_size[0]):
            for y in range(image_size[1] // 2, image_size[1]):
                mask.putpixel((x, y), 255)
        mask.save(absolute_mask_path)
        
        # 3. Create metadata row
        split = random.choice(split_distribution)
        row = {
            "image_path": relative_image_path,
            # For the test set, occasionally simulate missing mask data
            "mask_path": relative_mask_path if split != "test" or random.random() > 0.1 else "",
            "split": split,
        }
        metadata.append(row)

    # 3. Write metadata.csv
    metadata_path = base_path / "metadata.csv"
    with open(metadata_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(metadata)

    logger.info("Dummy segmentation dataset generation complete.")


def verify_output(output_path: Path) -> bool:
    """
    Performs a basic check to see if the restructuring was successful.
    """
    logger.info(f"Verifying output at '{output_path}'...")
    if not output_path.is_dir():
        logger.error("Output path is not a directory.")
        return False

    # Check for split directories
    expected_splits = ["train", "test", "validation"]
    found_splits = [d.name for d in output_path.iterdir() if d.is_dir()]
    
    if not any(split in found_splits for split in expected_splits):
        logger.error(f"No split directories found in output. Found: {found_splits}")
        return False
        
    # Check for the Spark success marker in the main output path
    if not (output_path / "train" / "_SUCCESS").exists():
        logger.error("'_SUCCESS' file not found in 'train' split. Spark job may have failed.")
        return False


    logger.info(f"Verification successful. Found splits: {found_splits}")
    return True


def main(args):
    """
    Main execution function.
    """
    
    output_dir = (Path(__file__).parent / "segmentation_test_output").resolve()

    # Clean up previous run's output to ensure a fresh start
    if output_dir.exists():
        logger.warning(f"Removing existing output directory: '{output_dir}'")
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(parents=True)
    
    input_data_path = output_dir / "source_segmentation_dataset"
    output_parquet_path = output_dir / "restructured_segmentation_dataset"

    logger.info(f"input_data_path: {input_data_path}")
    
    # 1. Build the temporary files
    create_dummy_segmentation_dataset(input_data_path, args.num_samples)

    # 2. Run and time the restructuring process
    logger.info("-" * 50)
    logger.info(
        f"Starting restructuring for 'image_segmentation' task with {args.num_samples} samples..."
    )
    start_time = time.perf_counter()

    try:
        # Crucial change: using the correct task type
        restructurer = Restructurer(task_type="image_segmentation")
        restructurer.restructure(
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

    # 3. Verify the output
    # generate_dataset_info(
    #         output_path=output_parquet_path,
    #         source_input_path=input_data_path, # Pass the original source data path
    #         dataset_name="dummy_image_classification",
    #         task_type="image_segmentation"
    #     )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test runner for dataset restructuring performance (Image Segmentation).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=100,
        help="Number of dummy image/mask pairs to generate for the test.",
    )
    
    args = parser.parse_args()
    main(args)