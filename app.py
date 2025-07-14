import streamlit as st
import pandas as pd
import os
from main import validate_file

st.set_page_config(page_title="AI Data Validator", layout="centered")

st.title("📊 AI-Powered Data Validator")
st.markdown("Upload a CSV or Excel file to detect data quality issues and duplicate names.")

uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx"])

if uploaded_file:
    file_ext = os.path.splitext(uploaded_file.name)[1]
    temp_path = f"uploaded_file{file_ext}"

    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    try:
        df, issues, dupes = validate_file(temp_path)

        st.subheader("🔍 Validation Issues")
        if issues:
            issues_df = pd.DataFrame(issues)
            st.dataframe(issues_df)
            st.download_button(
                "Download Issues Report (CSV)",
                issues_df.to_csv(index=False).encode('utf-8'),
                file_name="validation_issues.csv",
                mime="text/csv"
            )
        else:
            st.success("✅ No major validation issues found!")

        st.subheader("🧠 Potential Duplicates")
        if dupes:
            for d in dupes:
                st.markdown(f"• Row {d[0]+2} & {d[1]+2}: **'{d[2]}'** vs **'{d[3]}'**")
        else:
            st.success("✅ No potential duplicate names found.")

        issue_rows = [i["row"] - 2 for i in issues]
        df_cleaned = df.drop(issue_rows)
        st.subheader("✅ Cleaned Data")
        st.download_button(
            "Download Cleaned Data (CSV)",
            df_cleaned.to_csv(index=False).encode('utf-8'),
            file_name="cleaned_data.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
