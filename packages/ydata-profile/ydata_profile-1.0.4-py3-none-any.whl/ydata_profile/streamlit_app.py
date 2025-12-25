import pandas as pd
import streamlit as st
from ydata_profiling import ProfileReport
from streamlit_ydata_profiling import st_profile_report

# Title
st.write("""
# Simple CSV Upload and Pandas Profiling App
Upload your CSV file then the App will return the Profile Report.
""")

# Upload CSV data
uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

# Specify CSV delimiter
delimiter = st.text_input("Specify the CSV delimiter")

if uploaded_file is not None and delimiter:
    df = pd.read_csv(uploaded_file, delimiter=delimiter)
    st.write(df)
    pr = ProfileReport(df, explorative=True)
    st_profile_report(pr)