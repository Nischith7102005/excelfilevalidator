import pandas as pd
from fuzzywuzzy import fuzz

def validate_row(row, index):
    issues = []
    if 'Total Pay' in row and pd.notna(row['Total Pay']) and row['Total Pay'] < 0:
        issues.append("Negative Total Pay")
    if 'Hours Worked' in row and pd.notna(row['Hours Worked']) and row['Hours Worked'] > 100:
        issues.append("Unrealistic Hours Worked")
    required_fields = ['Name', 'Employee ID']
    for field in required_fields:
        if pd.isna(row.get(field, None)):
            issues.append(f"Missing {field}")
    return issues

def find_duplicates(df):
    duplicates = []
    if 'Name' not in df.columns:
        return duplicates
    for i, name1 in enumerate(df['Name']):
        if pd.isna(name1):
            continue
        for j in range(i + 1, len(df['Name'])):
            name2 = df['Name'][j]
            if pd.isna(name2):
                continue
            if fuzz.ratio(str(name1), str(name2)) > 90:
                duplicates.append((i, j, name1, name2))
    return duplicates

def validate_file(file_path):
    df = pd.read_excel(file_path) if file_path.endswith(".xlsx") else pd.read_csv(file_path)
    all_issues = []
    for idx, row in df.iterrows():
        row_issues = validate_row(row, idx)
        if row_issues:
            all_issues.append({"row": idx + 2, "issues": row_issues})
    dupes = find_duplicates(df)
    return df, all_issues, dupes
