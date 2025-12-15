# merge_summaries.py

import pandas as pd, glob, os

base_dir = "/mnt/dataresults"
files = glob.glob(f'{base_dir}/**/summary.csv', recursive=True)
dfs = []

for f in files:
    try:
        df = pd.read_csv(f)
        if not df.empty:
            dfs.append(df)
    except Exception as e:
        print(f"Skip {f}: {e}")

if dfs:
    merged = pd.concat(dfs, ignore_index=True)
    merged.to_csv(f"{base_dir}/final_summary.csv", index=False)
    print("Merged CSV saved.")
else:
    print("No valid CSVs found.")
