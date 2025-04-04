import streamlit as st
import pandas as pd
from docx import Document
import os
import base64

st.set_page_config(page_title="Voice Demo Tracker", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
<style>
:root {
  --primary-color: #008080;
  --primary-hover: #007070;
  --background-color: #fdfdfd;
  --text-color: #222222;
  --card-background: #ffffff;
  --card-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
  --border-radius: 10px;
  --font-family: 'Avenir', sans-serif;
  --accent-color: #ff9900;
}
body {
  background-color: var(--background-color);
  font-family: var(--font-family);
  color: var(--text-color);
}
div.stButton > button {
  background-color: var(--primary-color);
  color: #ffffff;
  border: none;
  padding: 0.75em 1.25em;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s;
}
div.stButton > button:hover {
  background-color: var(--primary-hover);
  transform: translateY(-2px);
}
.download-button {
  background-color: var(--primary-color);
  color: #ffffff !important;
  border: none;
  padding: 0.75em 1.25em;
  border-radius: var(--border-radius);
  cursor: pointer;
  text-decoration: none !important;
  font-weight: 500;
  display: inline-block;
  transition: background-color 0.3s ease, transform 0.2s;
  margin-right: 10px;
}
.download-button:hover {
  background-color: var(--primary-hover);
  transform: translateY(-2px);
}
.metric-small div {
  font-size: 0.8rem !important;
}
.info-block {
  line-height: 1.6;
  margin-bottom: 0.5rem;
}
.script-box {
  padding: 0.75rem;
  margin: 0.5rem 0 1rem 0;
  border: 1px solid #ccc;
  background-color: #f9f9f9;
}
.nav-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- Helper Functions ----------
@st.cache_data
def load_docx(path):
    doc = Document(path)
    scripts = {}
    current_heading = None
    for para in doc.paragraphs:
        if para.style.name.startswith("Heading"):
            current_heading = para.text.strip()
            scripts[current_heading] = ""
        elif current_heading:
            html_parts = []
            for run in para.runs:
                text = run.text.replace("<", "&lt;").replace(">", "&gt;")
                if run.bold:
                    text = f"<b>{text}</b>"
                if run.italic:
                    text = f"<i>{text}</i>"
                html_parts.append(text)
            scripts[current_heading] += "<p>" + "".join(html_parts) + "</p>"
    return scripts

def download_button(file_path, label):
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}" class="download-button">{label}</a>'

# ---------- File Paths ----------
DATA_FILE = "voice_demo_tracker_template.csv"
DOCX_FILE = "voice_demo_scripts_mock.docx"

# ---------- Session State for Navigation ----------
if "page" not in st.session_state:
    st.session_state.page = "upload"

# ---------- Refresh Function ----------
def refresh():
    st.rerun()

# ---------- Upload Page ----------
# ---------- File Upload Page ----------
st.title("Upload Your Files")

# File upload
uploaded_csv = st.file_uploader("Upload your voice demo tracker CSV", type="csv", key="csv_upload")
uploaded_docx = st.file_uploader("Upload your voice demo scripts DOCX", type="docx", key="docx_upload")

# Load progress save button only if saved file exists
if os.path.exists("saved_progress.csv"):
    if st.button("Load Saved Progress"):
        st.session_state["df"] = pd.read_csv("saved_progress.csv")
        st.success("Progress loaded successfully!")
        st.session_state["page"] = "Tracker"
        st.rerun()

# Upload and process files
if uploaded_csv and uploaded_docx:
    # Save uploaded files
    with open("uploaded_data.csv", "wb") as f:
        f.write(uploaded_csv.read())
    with open("uploaded_scripts.docx", "wb") as f:
        f.write(uploaded_docx.read())

    # Clear session state to ensure fresh reload
    for key in ["df", "script_data", "filtered_cards", "card_index"]:
        if key in st.session_state:
            del st.session_state[key]

    # Set flags and rerun
    st.session_state["uploaded_csv"] = "uploaded_data.csv"
    st.session_state["uploaded_docx"] = "uploaded_scripts.docx"
    st.session_state["page"] = "Tracker"
    st.success("Files uploaded! Click 'Next' to continue.")
    st.rerun()
else:
    st.warning("Please upload both a CSV and DOCX file to continue.")

# ---------- Tracker Page ----------
elif st.session_state.page == "tracker":
    if not os.path.exists(DATA_FILE) or not os.path.exists(DOCX_FILE):
        st.error("CSV or DOCX file not found. Please upload files first.")
        st.stop()
    
    df = pd.read_csv(DATA_FILE)
    scripts = load_docx(DOCX_FILE)
    
    # Top Progress Tracker: Only show the Recorded counter now.
    total = len(df)
    recorded_count = df["Recorded"].sum()
    st.metric("Recorded", f"{recorded_count}/{total}")
    st.progress(recorded_count / total)
    
    # View Mode selection with unique key
    view_mode = st.radio("View Mode", ["Card View", "Spreadsheet View"], index=0, key="tracker_view_mode_unique")
    
    if view_mode == "Spreadsheet View":
        st.dataframe(df, use_container_width=True)
    else:
        if "card_index" not in st.session_state:
            st.session_state.card_index = 0
        filtered_df = df  # (Add filtering if desired)
        if st.session_state.card_index >= len(filtered_df):
            st.session_state.card_index = 0
        row = filtered_df.iloc[st.session_state.card_index]
        st.markdown(f"### {row['Voice123 Upload Name']}")
        st.markdown(
            f"<div class='info-block'><b>Accent:</b> {row['Accent']}<br>"
            f"<b>Styles:</b> {row['Style 1']} + {row['Style 2']}<br>"
            f"<b>Tags:</b> {row['Voice123 Tag 1']}, {row['Voice123 Tag 2']}<br>"
            f"<b>Category:</b> {row['Category']}<br>"
            f"<b>Script File:</b> {row['Script Filename']}</div>",
            unsafe_allow_html=True
        )
        # Toggle Recorded button
        if not row["Recorded"]:
            if st.button("Mark as Recorded", key=f"record_btn_{row.name}"):
                df.at[row.name, "Recorded"] = True
                df.to_csv(DATA_FILE, index=False)
                refresh()
        else:
            if st.button("Mark as Not Recorded", key=f"unrecord_btn_{row.name}"):
                df.at[row.name, "Recorded"] = False
                df.to_csv(DATA_FILE, index=False)
                refresh()
    
        st.markdown(
            f"<div class='script-box'>{scripts.get(row['Script Filename'], '<i>Script not found.</i>')}</div>",
            unsafe_allow_html=True
        )
    
        nav_left, nav_right = st.columns(2)
        with nav_left:
            if st.session_state.card_index > 0:
                if st.button("Previous", key="prev_btn"):
                    st.session_state.card_index -= 1
                    st.rerun()
        with nav_right:
            if st.session_state.card_index < len(filtered_df) - 1:
                if st.button("Next", key="next_btn"):
                    st.session_state.card_index += 1
                    st.rerun()
        df.to_csv(DATA_FILE, index=False)
    
    # Download button for CSV only (styled as a button) at the bottom
    st.markdown("---")
    st.markdown(download_button(DATA_FILE, "Download CSV"), unsafe_allow_html=True)
    
    # "Back to Upload" button
    if st.button("Back to Upload", key="back_upload"):
        st.session_state.page = "upload"
        st.rerun()
