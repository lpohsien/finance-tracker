import glob
import csv
import re
import shutil
import os

# 1. Define your regex pattern
# Example: match files that start with 'data', have 3-5 digits, and end in .csv
pattern = os.path.expanduser("~/finance-tracker/data/*/transactions.csv")
files = glob.glob(pattern)

print(files)

for file_path in files:
    
    new_path = file_path + '.bak'
    shutil.copy2(file_path, new_path)
    print(f"Backed up: {file_path} -> {new_path}")
    
    os.remove(file_path)
    with open(new_path, 'r') as f_in, open(file_path, 'w', newline='') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            row['category'] = row['category'].lower()
            writer.writerow(row)