# a simple script to download the latest SDK package
import logging
from pathlib import Path
from download_sdk import s3_download
from torchvision import transforms

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


from datasets_object import create_dataset_object,save_dataset_object


def main():
    absolute_path = Path(__file__).parent / "downloaded_datasettt"
    dataset_name = "mnist-mini-v5"

    import time

    start_time = time.time()
    ds = s3_download(
        dataset_name=dataset_name,
        absolute_path=absolute_path,
        token="username_mlops_normal",
        clearml_api_host="http://144.172.105.98:30003",
        user_management_url="http://144.172.105.98:30009",
        s3_endpoint_url="http://144.172.105.98:7000",
        dataset_type="text_generation",
        # version="1.0.1"
    )
    end_time = time.time()
    print(f"Download completed in {end_time - start_time:.2f} seconds.")
    image_transforms = transforms.Compose([
    transforms.Resize((224, 224))
    ])

    print(ds["train"]["messages"][0])

    def preprocess_images(batch):
        """
        Transforms the 'image' column into 'pixel_values'.
        """
        # batch["image"] is a list of PIL Images
        # We convert to RGB to ensure 3 channels (prevents errors with B&W images)
        pixel_values = [
            img 
            for img in batch["messages"]
        ]
        
        # Return the new column
        return {"messages": pixel_values}

    updated_ds = ds.map(
    preprocess_images, 
    batched=True,
    load_from_cache_file=False,
    num_proc=16
    )

    try:
        num_bytes_freed = ds.cleanup_cache_files()
        print(f"Cleanup freed {num_bytes_freed} bytes.")
    except Exception as e:
        # It implies the files are already gone, which is fine
        print(f"Cache cleanup skipped (files likely already removed): {e}")
        num_bytes_freed = 0

    save_path = Path(__file__).parent / "saved_data"

    save_dataset_object(dataset_name,updated_ds,save_path)

    ds = create_dataset_object(
        absolute_path=save_path,
        dataset_name=dataset_name,
        dataset_type="text_generation",
    )

    print(ds)

    print(ds.keys())

    # for i in range(3):
    #     for split in ds.keys():
    #         data = ds[split][i]

    #         # print(data["image"].size,data["label"])
    #         print(data["image"])
    #         # save image in jpg for inspection
    #         img_object = data["image"]

    #         # 2. Just save it directly
    #         img_object.save(Path(__file__).parent / f"image_{split}_{i}.jpg")

    # model_id = "Qwen/Qwen2.5-0.5B-Instruct"

    # print(f"Loading tokenizer for {model_id}...")
    # try:
    #     tokenizer = AutoTokenizer.from_pretrained(model_id)
    # except Exception as e:
    #     print(f"Error loading tokenizer: {e}")
    #     return

    # ---------------------------------------------------------
    # 2. Define function to apply ChatML template
    # ---------------------------------------------------------
    # def apply_chatml(example):
    #     """
    #     Takes the 'messages' list and converts it to a string
    #     formatted with <|im_start|>, <|im_end|>, etc.
    #     """
    #     # We use tokenize=False to get the string back for inspection/debugging
    #     # or if you plan to tokenize later in a data collator.
    #     formatted_text = tokenizer.apply_chat_template(
    #         example["messages"],
    #         tokenize=False,
    #         add_generation_prompt=False
    #     )
    #     return {"text": formatted_text}

    # ds = ds.map(apply_chatml)

    # print(ds["train"][0]["text"])

    # for i in range(15010,15015):
    #     for split in ds.keys():
    #         image = ds[split][i]["image"]
    #         label = ds[split][i]["label"]
    #         label_name = ds[split][i]["label_name"]

    #         print(np.array(image).shape,label,label_name)

    # presigned_urls method

    # url = s3_download(
    # clearml_access_key,
    # clearml_secret_key,
    # s3_access_key,
    # s3_secret_key,
    # s3_endpoint_url,
    # dataset_name,
    # absolute_path,
    # user_name,
    # method="presigned_urls")

    # print("Downloaded SDK package is available at:", url)

    # zip_streaming method

    # zip_data = s3_download_sdk(
    #     clearml_access_key,
    #     clearml_secret_key,
    #     s3_access_key,
    #     s3_secret_key,
    #     s3_endpoint_url,
    #     dataset_name,
    #     absolute_path,
    #     user_name,
    #     method="streaming_zip")

    # print(type(zip_data))
    # if zip_data:
    #     path = Path(__file__).parent / "dataset.zip"
    #     with open(path, "wb") as f:
    #         f.write(zip_data)
    #     print("Successfully saved dataset.zip")


if __name__ == "__main__":
    main()


# import os
# import logging
# from pathlib import Path
# import numpy as np
# from transformers import AutoTokenizer # Import transformers

# # Assuming these are your local modules
# from download_sdk import s3_download
# from torch_datasets import create_text_generation_dataset

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# def main():
#     absolute_path = Path(__file__).parent / "downloaded_datasettt"
#     dataset_name = "datapizza-ai-lab-dnd5e-srd-qa"

#     # ... (Your existing download logic) ...
#     ds = s3_download(
#         dataset_name=dataset_name,
#         absolute_path=absolute_path,
#         token="username_datauser-v1",
#         clearml_api_host="http://144.172.105.98:30003",
#         user_management_url="http://144.172.105.98:30009",
#         s3_endpoint_url="http://144.172.105.98:7000",
#         dataset_type="text_generation",
#         version="1.0.0"
#     )

#     print("Original Dataset Structure:", ds)

#     # ---------------------------------------------------------
#     # 1. Load Qwen 0.5B Tokenizer
#     # ---------------------------------------------------------
#     # Qwen2.5 is the latest, but Qwen1.5 works similarly.
#     # Using 'Instruct' ensures the chat template is properly configured.
#     model_id = "Qwen/Qwen2.5-0.5B-Instruct"

#     print(f"Loading tokenizer for {model_id}...")
#     try:
#         tokenizer = AutoTokenizer.from_pretrained(model_id)
#     except Exception as e:
#         print(f"Error loading tokenizer: {e}")
#         return

#     # ---------------------------------------------------------
#     # 2. Define function to apply ChatML template
#     # ---------------------------------------------------------
#     def apply_chatml(example):
#         """
#         Takes the 'messages' list and converts it to a string
#         formatted with <|im_start|>, <|im_end|>, etc.
#         """
#         # We use tokenize=False to get the string back for inspection/debugging
#         # or if you plan to tokenize later in a data collator.
#         formatted_text = tokenizer.apply_chat_template(
#             example["messages"],
#             tokenize=False,
#             add_generation_prompt=False
#         )
#         return {"text": formatted_text}

#     # ---------------------------------------------------------
#     # 3. Apply to the dataset
#     # ---------------------------------------------------------
#     # check if 'messages' column exists
#     column_names = ds[list(ds.keys())[0]].column_names
#     if "messages" in column_names:
#         print("Applying ChatML template to 'messages' column...")

#         # This creates a new column called 'text' with the formatted string
#         ds = ds.map(apply_chatml)

#         # ---------------------------------------------------------
#         # 4. Inspect Results
#         # ---------------------------------------------------------
#         print("\n--- Sample Formatted Output ---")
#         # Get the first available split (e.g., 'train')
#         first_split = list(ds.keys())[0]
#         sample = ds[first_split][0]

#         print("Raw Messages:", sample['messages'])
#         print("\nFormatted ChatML Text:")
#         print(sample['text'])
#         print("-------------------------------\n")
#     else:
#         print(f"Column 'messages' not found. Available columns: {column_names}")

#     # Optional: Continue with your loop logic using the new format
#     # for i in range(2):
#     #     for split in ds.keys():
#     #         print(f"Split: {split}, Index: {i}")
#     #         print(ds[split][i]['text'])

# if __name__ == "__main__":
#     main()
