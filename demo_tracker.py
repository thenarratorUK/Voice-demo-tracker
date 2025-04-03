
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
  background-color: var(--accent-color);
  color: white;
  padding: 0.5em 1em;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  border-radius: var(--border-radius);
  font-weight: bold;
  margin-right: 10px;
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
            scripts[current_heading] += "<p>" + ''.join(html_parts) + "</p>"
    return scripts

def download_button(file_path, label):
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}" class="download-button">{label}</a>'

# ---------- File Paths ----------
DATA_FILE = "voice_demo_tracker_template.csv"
DOCX_FILE = "voice_demo_scripts_mock.docx"

if "page" not in st.session_state:
    st.session_state.page = "upload"

# ---------- Upload Page ----------
if st.session_state.page == "upload":
    if st.button("Load Saved Progress"):
        st.session_state.clear()
        st.rerun()
    st.header("Upload Files")
    uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])
    uploaded_docx = st.file_uploader("Upload DOCX", type=["docx"])

    if uploaded_csv:
        with open(DATA_FILE, "wb") as f:
            f.write(uploaded_csv.read())
        st.success("CSV uploaded and saved.")

    if uploaded_docx:
        with open(DOCX_FILE, "wb") as f:
            f.write(uploaded_docx.read())
        st.success("DOCX uploaded and saved.")

    if st.button("Next"):
        st.session_state.page = "tracker"
        st.rerun()

# ---------- Tracker Page ----------
elif st.session_state.page == "tracker":
    if not os.path.exists(DATA_FILE) or not os.path.exists(DOCX_FILE):
        st.error("CSV or DOCX file not found.")
        st.stop()

    df = pd.read_csv(DATA_FILE)
    scripts = load_docx(DOCX_FILE)

    total = len(df)
    recorded_count = df["Recorded"].sum()
    written_count = df["Script Written"].sum()
    view_mode = st.radio("View Mode", ["Card View", "Spreadsheet View"], index=0, key="tracker_view_mode_toggle")

    total = len(df)

    if view_mode == "Card View" and "card_index" in st.session_state:
        recorded_count = df["Recorded"].sum()
        written_count = df["Script Written"].sum()
        uploaded_count = df["Uploaded"].sum()
    else:
        recorded_count = df["Recorded"].sum()
        written_count = df["Script Written"].sum()
        uploaded_count = df["Uploaded"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Scripts Written", f"{written_count}/{total}")
    col2.metric("Recorded", f"{recorded_count}/{total}")
    col3.metric("Uploaded", f"{uploaded_count}/{total}")
    st.progress(recorded_count / total)

    col1, col2, col3 = st.columns(3)
    col1.metric("Scripts Written", f"{written_count}/{total}")
    col2.metric("Recorded", f"{recorded_count}/{total}")
    col3.metric("Uploaded", f"{uploaded_count}/{total}")
    st.progress(recorded_count / total)

    view_mode = st.radio("View Mode", ["Card View", "Spreadsheet View"], index=0, key="tracker_view_mode_toggle")

    if view_mode == "Spreadsheet View":
        st.dataframe(df, use_container_width=True)
    else:
        if "card_index" not in st.session_state:
            st.session_state.card_index = 0
        filtered_df = df

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

        col1, col2, col3 = st.columns(3)
        df.at[row.name, "Script Written"] = col1.checkbox("Script Written", row["Script Written"], key=f"sw_{row.name}")
        df.at[row.name, "Recorded"] = col2.checkbox("Recorded", row["Recorded"], key=f"rec_{row.name}")
        df.at[row.name, "Uploaded"] = col3.checkbox("Uploaded", row["Uploaded"], key=f"up_{row.name}")

        st.markdown(f"<div class='script-box'>{scripts.get(row['ID'], '<i>Script not found.</i>')}</div>", unsafe_allow_html=True)

        nav1, nav2 = st.columns(2)
        with nav1:
            if st.session_state.card_index > 0:
                if st.button("Previous"):
                    st.session_state.card_index -= 1
        with nav2:
            if st.session_state.card_index < len(filtered_df) - 1:
                if st.button("Next"):
                    st.session_state.card_index += 1

        df.to_csv(DATA_FILE, index=False)

    st.markdown("---")
    colA, colB = st.columns([1, 1])
    with colA:
        if os.path.exists(DATA_FILE):
            st.markdown(download_button(DATA_FILE, "Download CSV"), unsafe_allow_html=True)
    with colB:
        if os.path.exists(DOCX_FILE):
            st.markdown(download_button(DOCX_FILE, "Download DOCX"), unsafe_allow_html=True)
