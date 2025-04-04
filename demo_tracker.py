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
def load_docx(path):
    """Load and parse a DOCX file into a dictionary of script content."""
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

# ---------- Session State Initialization ----------
if "page" not in st.session_state:
    st.session_state.page = "upload"
if "card_index" not in st.session_state:
    st.session_state.card_index = 0
# current_id: last card you worked on.
if "current_id" not in st.session_state:
    st.session_state.current_id = None
# display_id: the card that will be shown on load.
if "display_id" not in st.session_state:
    st.session_state.display_id = None

# ---------- Refresh Function ----------
def refresh():
    st.rerun()

# ---------- Upload Page ----------
if st.session_state.page == "upload":
    st.header("Upload Files")
    # Show "Load Saved Progress" if a non-empty CSV exists.
    if os.path.exists(DATA_FILE):
        try:
            df_test = pd.read_csv(DATA_FILE)
            if not df_test.empty:
                if st.button("Load Saved Progress", key="load_progress"):
                    st.session_state.page = "tracker"
                    # On load saved progress, update display_id from current_id if available.
                    if st.session_state.current_id is not None:
                        st.session_state.display_id = st.session_state.current_id
                    st.rerun()
        except Exception:
            pass

    uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], key="upload_csv")
    uploaded_docx = st.file_uploader("Upload DOCX", type=["docx"], key="upload_docx")
    if uploaded_csv is not None:
        with open(DATA_FILE, "wb") as f:
            f.write(uploaded_csv.read())
        st.success("CSV uploaded and saved.")
    if uploaded_docx is not None:
        with open(DOCX_FILE, "wb") as f:
            f.write(uploaded_docx.read())
        st.success("DOCX uploaded and saved.")

    # Only show "Next" if both files exist.
    if os.path.exists(DATA_FILE) and os.path.exists(DOCX_FILE):
        if st.button("Next", key="next_upload"):
            st.session_state.page = "tracker"
            # On transition, update display_id from current_id if available.
            if st.session_state.current_id is not None:
                st.session_state.display_id = st.session_state.current_id
            st.rerun()
    else:
        st.warning("Please upload both CSV and DOCX files to continue.")

# ---------- Tracker Page ----------
elif st.session_state.page == "tracker":
    if not os.path.exists(DATA_FILE) or not os.path.exists(DOCX_FILE):
        st.error("CSV or DOCX file not found. Please upload files first.")
        st.stop()

    df = pd.read_csv(DATA_FILE)
    # Reload DOCX every time so updates are reflected.
    scripts = load_docx(DOCX_FILE)

    # Initialize current_id if not set.
    if st.session_state.current_id is None:
        st.session_state.current_id = df.iloc[st.session_state.card_index]["ID"]
    # Initialize display_id if not set.
    if st.session_state.display_id is None:
        st.session_state.display_id = st.session_state.current_id

    # Determine the card_index corresponding to display_id.
    matching_rows = df[df["ID"] == st.session_state.display_id]
    if not matching_rows.empty:
        st.session_state.card_index = int(matching_rows.index[0])
    else:
        st.session_state.card_index = 0
        st.session_state.display_id = df.iloc[0]["ID"]
        st.session_state.current_id = df.iloc[0]["ID"]

    # Top Progress Tracker: Show the Recorded counter.
    total = len(df)
    recorded_count = df["Recorded"].sum()
    st.metric("Recorded", f"{recorded_count}/{total}")
    st.progress(recorded_count / total)

    # View Mode selection
    view_mode = st.radio("View Mode", ["Card View", "Spreadsheet View"], index=0, key="tracker_view_mode_unique")

    if view_mode == "Card View":
        # ---------- BEGIN CARD SELECTOR ----------
        if "show_full_table" not in st.session_state:
            st.session_state["show_full_table"] = False
        if not st.session_state["show_full_table"]:
            # Build a list of unique IDs from the CSV.
            id_list = df["ID"].dropna().unique().tolist()
            selected_id = st.selectbox(
                "Jump to card (by ID):",
                id_list,
                index=id_list.index(st.session_state.display_id) if st.session_state.display_id in id_list else 0,
                key="card_selector"
            )
            # If a different ID is chosen, update both current_id and display_id and update card_index.
            if selected_id != st.session_state.display_id:
                new_index = int(df[df["ID"] == selected_id].index[0])
                st.session_state.card_index = new_index
                st.session_state.current_id = selected_id
                st.session_state.display_id = selected_id
                st.rerun()
        # ---------- END CARD SELECTOR ----------

        # ---------- Card View Display ----------
        card_index = st.session_state.card_index
        filtered_df = df  # (Add filtering if desired)
        if card_index >= len(filtered_df):
            card_index = 0
            st.session_state.card_index = 0
            st.session_state.current_id = df.iloc[0]["ID"]
            st.session_state.display_id = df.iloc[0]["ID"]
        row = filtered_df.iloc[card_index]
        st.markdown(f"### {row['Voice123 Upload Name']}")
        st.markdown(
            f"<div class='info-block'><b>Accent:</b> {row['Accent']}<br>"
            f"<b>Styles:</b> {row['Style 1']} + {row['Style 2']}<br>"
            f"<b>Tags:</b> {row['Voice123 Tag 1']}, {row['Voice123 Tag 2']}<br>"
            f"<b>Category:</b> {row['Category']}<br>"
            f"<b>Script File:</b> {row['Script Filename']}</div>",
            unsafe_allow_html=True
        )
        # Update both current_id and display_id to the currently displayed card.
        st.session_state.current_id = row["ID"]
        st.session_state.display_id = row["ID"]

        # Toggle Recorded button.
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
            if card_index > 0:
                if st.button("Previous", key="prev_btn"):
                    st.session_state.card_index = card_index - 1
                    st.session_state.current_id = df.iloc[card_index - 1]["ID"]
                    st.session_state.display_id = df.iloc[card_index - 1]["ID"]
                    st.rerun()
        with nav_right:
            if card_index < len(filtered_df) - 1:
                if st.button("Next", key="next_btn"):
                    st.session_state.card_index = card_index + 1
                    st.session_state.current_id = df.iloc[card_index + 1]["ID"]
                    st.session_state.display_id = df.iloc[card_index + 1]["ID"]
                    st.rerun()
        df.to_csv(DATA_FILE, index=False)

    elif view_mode == "Spreadsheet View":
        st.dataframe(df, use_container_width=True)

    # Download button for CSV at the bottom.
    st.markdown("---")
    st.markdown(download_button(DATA_FILE, "Download CSV"), unsafe_allow_html=True)

    # "Back to Upload" button.
    if st.button("Back to Upload", key="back_upload"):
        st.session_state.page = "upload"
        st.rerun()
