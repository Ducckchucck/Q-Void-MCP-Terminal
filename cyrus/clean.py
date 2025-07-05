import os
import pandas as pd

INPUT_PATH = "datasets/piyush/SQL/SQLiV3.csv"
OUTPUT_PATH = "datasets/piyush/SQL/SQLiV3.csv"

print(f"📂 Reading dataset: {INPUT_PATH}")
df = pd.read_csv(INPUT_PATH, low_memory=False)

# Strip all column names
df.columns = [col.strip() for col in df.columns]

# Auto-detect label column
label_col = None
for col in df.columns:
    if col.lower() in ['label', 'class', 'target']:
        label_col = col
        break

if not label_col:
    raise ValueError("❌ No label column found.")

print(f"🏷️ Using '{label_col}' as label column")

# Drop duplicates
df.drop_duplicates(inplace=True)

# Drop flow-related junk columns (if present)
junk_cols = ['Flow ID', 'FlowID', 'Source IP', 'Destination IP', 'Timestamp', 'Src IP', 'Dst IP']
df.drop(columns=[col for col in junk_cols if col in df.columns], errors='ignore', inplace=True)

# Drop columns that are all NaNs
df.dropna(axis=1, how="all", inplace=True)

# Drop rows without labels
df = df[df[label_col].notna()]

# Convert all non-label columns to numeric
for col in df.columns:
    if col != label_col:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows where all features are NaN
df.dropna(axis=0, how="all", inplace=True)

# Fill missing values with 0
df.fillna(0, inplace=True)

# Save cleaned dataset
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ Cleaned dataset saved to: {OUTPUT_PATH}")
