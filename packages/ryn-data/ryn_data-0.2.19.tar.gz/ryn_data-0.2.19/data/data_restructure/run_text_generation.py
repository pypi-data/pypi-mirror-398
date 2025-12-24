import argparse
import csv
import logging
import random
import shutil
import time
import sys
from pathlib import Path
from typing import List

# Check for pandas/pyarrow which are needed for parquet generation
try:
    import pandas as pd
except ImportError:
    print("Error: 'pandas' and 'pyarrow' are required for this test script.")
    print("pip install pandas pyarrow")
    sys.exit(1)

# Assuming your project structure allows these imports.
from restructure import Restructurer 

# Configure logging for the runner script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


import psutil
import os
import functools

def profile_usage(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        start = time.time()
        
        result = func(*args, **kwargs)

        cpu = process.cpu_percent()
        mem = process.memory_info().rss / 1e6
        duration = time.time() - start
        print(f"Time: {duration:.2f}s | CPU: {cpu:.2f}% | RAM: {mem:.2f} MB")

        return result
    return wrapper

def create_dummy_text_dataset(
    base_path: Path, 
    num_samples: int, 
    generate_structure_file: bool = False,
    inject_error: bool = False,
    chatml_format: bool = False
) -> None:
    """
    Creates a dummy text generation dataset.
    
    Args:
        base_path: Output directory.
        num_samples: Number of samples.
        generate_structure_file: Create structure.csv.
        inject_error: Break schema of one file.
        chatml_format: If True, generates data with 'messages' column (Array<Struct>) 
                       instead of instruction/output.
    """
    logger.info(
        f"Generating dataset with {num_samples} samples at '{base_path}'..."
    )
    if chatml_format:
        logger.info("ℹ️  Mode: ChatML (Pre-structured data generation)")

    base_path.mkdir(parents=True, exist_ok=True)
    
    sample_tasks = [
        ("Summarize the text.", "Python is a generic language...", "Python is popular."),
        ("Translate to Spanish.", "Hello world.", "Hola Mundo."),
        ("What is the capital of France?", "", "Paris"),
        ("Write a poem.", "About code.", "Code flows like water..."),
    ]
    
    split_opts = ["train", "validation", "test"]
    weights = [0.7, 0.15, 0.15]

    # Generate all data first
    all_data = []
    for i in range(num_samples):
        instr, inp, outp = random.choice(sample_tasks)
        split_val = random.choices(split_opts, weights=weights)[0]
        
        if chatml_format:
            # Create nested structure: [{"role": "user", ...}, {"role": "assistant", ...}]
            # We combine instruction and input for the user content
            user_content = f"{instr}\n{inp}" if inp else instr
            
            row = {
                "messages": [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": f"{outp} (ID: {i})"}
                ],
                "split": split_val,
                "extra_column": "noise_data"
            }
        else:
            # Standard columns
            row = {
                "instruction": instr,
                "output": f"{outp} (ID: {i})",
                "extra_column": "noise_data", 
                "split": split_val,
            }
            
        all_data.append(row)

    # Split data into chunks
    num_files = 5
    chunk_size = len(all_data) // num_files
    files_created: List[Path] = []

    logger.info(f"Splitting data into {num_files} files.")

    for i in range(num_files):
        # Slice the data
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_files - 1 else len(all_data)
        chunk = all_data[start:end]
        
        if not chunk:
            continue

        df = pd.DataFrame(chunk)
        file_name = f"data_part_{i}"

        # --- ERROR INJECTION ---
        if inject_error and i == num_files - 1:
            logger.warning(f"⚠️  INJECTING ERROR in '{file_name}'")
            if chatml_format:
                # Rename 'messages' to break the structure check
                df = df.rename(columns={"messages": "broken_messages"})
            else:
                # Rename 'instruction'
                df = df.rename(columns={"instruction": "invalid_col"})
        # -----------------------

        # Choose format
        # NOTE: If using ChatML, we avoid CSV because Pandas writes lists as Strings 
        # (e.g. "[{'role':...}]") which Spark reads as StringType, failing the is_structured check.
        valid_formats = ["parquet", "json"] if chatml_format else ["parquet", "csv", "json"]
        file_format = random.choice(valid_formats)
        
        if file_format == "parquet":
            file_path = base_path / "data" / f"{file_name}.parquet"
            # PyArrow handles the nested list of dicts perfectly for Parquet
            df.to_parquet(file_path, index=False)
            logger.info(f"Created Parquet: {file_path.name}")
            
        elif file_format == "csv":
            file_path = base_path / "data" / f"{file_name}.csv"
            df.to_csv(file_path, index=False)
            logger.info(f"Created CSV:     {file_path.name}")
            
        else: # json
            file_path = base_path / "data" / f"{file_name}.json"
            df.to_json(file_path, orient="records", indent=2)
            logger.info(f"Created JSON:    {file_path.name}")
            
        files_created.append(file_path)

    # --- Handling structure.csv ---
    if generate_structure_file:
        structure_path = base_path / "structure.csv"
        with open(structure_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["file_path", "split"])
            for file_path in files_created: # Note: Logic copied from previous, ensures vars exist
                rel_path = file_path.relative_to(base_path)
                override_split = random.choice(["", "train", "test"])
                writer.writerow([rel_path, override_split])
        logger.info(f"Created {structure_path}")

    logger.info("Dummy dataset generation complete.")


def verify_output(output_path: Path) -> bool:
    """Verifies output existence."""
    if not output_path.is_dir(): return False
    expected_splits = ["train", "test", "validation"]
    found_splits = [d.name for d in output_path.iterdir() if d.is_dir()]
    if not any(s in found_splits for s in expected_splits): return False
    if not list(output_path.rglob("*.parquet")): return False
    return True



def main(args):
    output_dir = (Path(__file__).parent / "test_output_text_gen").resolve()
    input_data_path = output_dir / "input_data"
    data_path = input_data_path / "data"
    output_parquet_path = output_dir / "restructured_data"

    if output_dir.exists(): shutil.rmtree(output_dir)
    input_data_path.mkdir(parents=True)
    data_path.mkdir(parents=True)
    
    logger.info(f"Config: StructureFile={args.structure_file}, ErrorInjection={args.inject_error}, ChatML={args.chatml_format}")
    print(args.num_samples)
    # 1. Build Dataset
    create_dummy_text_dataset(
        input_data_path, 
        args.num_samples, 
        generate_structure_file=args.structure_file,
        inject_error=args.inject_error,
        chatml_format=args.chatml_format
    )

    # 2. Run Restructuring
    logger.info("-" * 50)
    logger.info("Starting restructuring...")
    start_time = time.perf_counter()

    try:
        @profile_usage
        def restructure_data():
            restructurer = Restructurer(task_type="text_generation")
            summary = restructurer.restructure(input_path=input_data_path, output_path=output_parquet_path)
            return summary

        summary = restructure_data()
        print("\n--- Restructuring Summary ---")
        print(summary)
        
        if args.inject_error:
            processed_rows = summary.get("num_rows", 0)
            if processed_rows < args.num_samples:
                print(f"\n✅ SUCCESS: Error injection worked. Processed {processed_rows}/{args.num_samples} rows.")
            else:
                print("\n❌ FAILURE: Error injection failed. Rows not dropped.")

    except Exception as e:
        logger.error(f"Restructuring failed: {e}", exc_info=True)
        return

    logger.info(f"Time: {time.perf_counter() - start_time:.4f}s")

    # 3. Verify
    if not verify_output(output_parquet_path):
        logger.error("Verification failed.")
        sys.exit(1)
    else:
        print(f"\n✅ Success! Output: {output_parquet_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--num-samples", type=int, default=5000, help="Number of samples.")
    parser.add_argument("--structure-file", action="store_true", help="Generate structure.csv.")
    parser.add_argument("--inject-error", action="store_true", help="Inject schema error in one file.")
    parser.add_argument("--chatml-format", action="store_true", help="Generate data in ChatML format (messages column).")
    
    args = parser.parse_args()
    main(args)