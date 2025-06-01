import streamlit as st
import pandas as pd
from main import validate_file

st.set_page_config(page_title="AI Data Validator", layout="centered")

st.title("📊 AI-Powered Data Validator")
st.markdown("Upload a CSV or Excel file to detect data quality issues and duplicate names.")

uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx"])

if uploaded_file:
    # Save uploaded file temporarily
    with open("uploaded_file.xlsx", "wb") as f:
        f.write(uploaded_file.read())

    # Validate file
    issues, dupes = validate_file("uploaded_file.xlsx")

    # Show results
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
