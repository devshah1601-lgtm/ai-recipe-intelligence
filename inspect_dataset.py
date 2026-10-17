
import pandas as pd
from pathlib import Path

csv_path = Path("data/raw/IndianFoodDatasetCSV.csv")

df = pd.read_csv(csv_path, low_memory=False)

print("\n===== TOTAL RECIPES =====")
print(len(df))

print("\n===== COLUMN NAMES =====")
print(df.columns.tolist())

print("\n===== FIRST 3 RECIPES =====")
print(df.head(3).to_string(index=False))

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())

if "Course" in df.columns:
    print("\n===== COURSE CATEGORIES =====")
    print(df["Course"].value_counts().head(30))
