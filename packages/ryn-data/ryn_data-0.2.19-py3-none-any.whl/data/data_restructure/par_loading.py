import pandas as pd
import numpy as np
from PIL import Image
import io

# Assume 'train/part-00000.parquet' is one of your output files
df = pd.read_parquet('/home/mlops/ramtin/tools/data_platform/ryn/data/data_restructure/restructure_test_output/restructured_dataset/train/part-00000-of-00014.parquet')

# Get the first row of the DataFrame
first_row = df.iloc[6]

# The 'image' column is a dictionary-like object in Pandas
image_data = first_row['image']

# Get the raw bytes from the struct
image_bytes = image_data['bytes']
print(f"Type of image_bytes: {type(image_bytes)}")
print(f"Length of image_bytes: {len(image_bytes)} bytes")

# --- This is the key decoding step ---
# 1. Treat the bytes as an in-memory file
bytes_io = io.BytesIO(image_bytes)

# 2. Open the in-memory file with Pillow
image_pil = Image.open(bytes_io)
print(f"\nPIL Image object created. Mode: {image_pil.mode}, Size: {image_pil.size}")

# 3. Convert the Pillow Image to a NumPy array
image_array = np.array(image_pil)

print("\nConverted to NumPy array.")
print(f"Type of image_array: {type(image_array)}")
print(f"Shape of the array: {image_array.shape}") # e.g., (64, 64, 3)
print(f"Data type of array elements: {image_array.dtype}") # e.g., uint8


segmenation_df = pd.read_parquet('/home/mlops/ramtin/tools/data_platform/ryn/data/data_restructure/segmentation_test_output/restructured_segmentation_dataset/train/part-00000-of-00000.parquet')

first_segmentation_row = segmenation_df.iloc[0]

segmentation_image_data = first_segmentation_row['image']

segmentation_image_bytes = segmentation_image_data['bytes']

segmentation_bytes_io = io.BytesIO(segmentation_image_bytes)

segmentation_image_pil = Image.open(segmentation_bytes_io)

segmentation_image_array = np.array(segmentation_image_pil)

print("\nSegmentation Image converted to NumPy array.")
print(f"Type of segmentation_image_array: {type(segmentation_image_array)}")
print(f"Shape of the segmentation array: {segmentation_image_array.shape}") # e.g
print(f"Data type of segmentation array elements: {segmentation_image_array.dtype}") # e.g., uint8


mask_data = first_segmentation_row['mask']
mask_bytes = mask_data['bytes']
mask_bytes_io = io.BytesIO(mask_bytes)
mask_image_pil = Image.open(mask_bytes_io)
mask_image_array = np.array(mask_image_pil)
print("\nMask Image converted to NumPy array.")
print(f"Type of mask_image_array: {type(mask_image_array)}")
print(f"Shape of the mask array: {mask_image_array.shape}") # e.g
print(f"Data type of mask array elements: {mask_image_array.dtype}") # e.g


# print(image_array)   