import os
from midir import midir

def run_ydata_profile():
    cmd = (
        "python -m streamlit run "
        f"'{midir()}/streamlit_app.py'"
    )
    os.system(cmd)
