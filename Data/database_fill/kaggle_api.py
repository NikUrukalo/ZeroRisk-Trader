##### This file is used to download the dataset from Kaggle using the kagglehub library. 
##### It downloads the latest version of the dataset and reads it into a pandas DataFrame.

# Libraries
import kagglehub
import pandas as pd
import os
import shutil

# 1. Download dataset
path = kagglehub.dataset_download("sunnykusawa/stock-price-dataset-eod")
print("Downloaded to:", path)

# 2. KaggleHub CSV file
source_csv = os.path.join(path, "stock_price_data_eod.csv")

# 3. Your GitHub repo folder
repo_folder = r"C:\Users\nejcz\OneDrive\Dokumenti\FMF Dokumenti\Predmeti\Osnove Podatkovnih Baz\ZeroRisk Trader\Aplikacija-osebne-finance\Data\database_fill"

# 4. Destination inside your repo
destination_csv = os.path.join(repo_folder, "stock_price_data_eod.csv")

# 5. Copy file into your GitHub repo
shutil.copy(source_csv, destination_csv)

print("CSV copied into your GitHub repo:", destination_csv)

# 6. Load and print table
df = pd.read_csv(destination_csv)
print(df.head(40))