# ai_data_validator/main.py

import pandas as pd
import difflib
from fuzzywuzzy import fuzz

# Basic validation rules
def validate_row(row, index):
    issues = []

    # Check for negative numbers in key fields
    if 'Total Pay' in row and row['Total Pay'] < 0:
        issues.append("Negative Total Pay")

    # Check for very large hour entries
    if 'Hours Worked' in row and row['Hours Worked'] > 100:
        issues.append("Unrealistic Hours Worked")

    # Check for missing required fields
    required_fields = ['Name', 'Employee ID']
    for field in required_fields:
        if pd.isna(row.get(field, None)):
            issues.append(f"Missing {field}")

    return issues

def find_duplicates(df):
    duplicates = []
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
            all_issues.append({"row": idx + 2, "issues": row_issues})  # +2 for header + 1-based index

    dupes = find_duplicates(df)
    return all_issues, dupes

if __name__ == "__main__":
    import sys
    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_data.xlsx"
    issues, dupes = validate_file(file_path)

    print("Validation Results:\n")
    for issue in issues:
        print(f"Row {issue['row']}: {', '.join(issue['issues'])}")

    if dupes:
        print("\nPotential Duplicates:")
        for d in dupes:
            print(f"Row {d[0]+2} & {d[1]+2}: '{d[2]}' vs '{d[3]}'")
    else:
        print("\nNo potential duplicate names found.")

    # Export issues to CSV
    if issues:
        df_issues = pd.DataFrame(issues)
        df_issues.to_csv("validation_report.csv", index=False)
        print("\nIssues saved to validation_report.csv")
