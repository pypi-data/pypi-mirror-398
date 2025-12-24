from data.data_restructure.file_convert import DirectoryConverter
from pathlib import Path


if __name__ == "__main__":
    dir_path = Path(__file__).parent.parent/"data_validation"/"landing"
    converter = DirectoryConverter(dir_path)
    
    converted_file = converter.convert_directory()

    # import pandas as pd
    # df = pd.read_parquet(dir_path/"landing"/"large_files"/"huge_user_file.parquet")
    # print(df.shape)
    print(f"Converted file saved at: {converted_file}")