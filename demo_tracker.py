import streamlit as st
import pandas as pd
from docx import Document
import re

st.set_page_config(page_title="Voice Demo Tracker", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("voice_demo_tracker_template.csv")

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

# Load CSV and DOCX
df = load_data()
scripts = load_docx("voice_demo_scripts_mock.docx")

# --- Progress Bar ---
st.title("Voice Demo Tracker")
total = len(df)
recorded_count = df["Recorded"].sum()
written_count = df["Script Written"].sum()
uploaded_count = df["Uploaded"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Scripts Written", f"{written_count}/{total}")
col2.metric("Recorded", f"{recorded_count}/{total}")
col3.metric("Uploaded", f"{uploaded_count}/{total}")

progress = int((recorded_count / total) * 100)
st.progress(progress / 100)

# --- View Toggle ---
view_full = st.checkbox("Show full spreadsheet", value=False)

# --- Filters for Card View ---
if not view_full:
    with st.expander("Filter Cards"):
        selected_category = st.multiselect("Category", options=sorted(df["Category"].unique()))
        selected_accent = st.multiselect("Accent", options=sorted(df["Accent"].unique()))
        styles = sorted(set(df["Style 1"]).union(df["Style 2"]))
        selected_styles = st.multiselect("Styles", options=styles)
        selected_tags = st.multiselect("Voice123 Tags", options=sorted(set(df["Voice123 Tag 1"]).union(df["Voice123 Tag 2"])))
        search = st.text_input("Search Upload Name or ID")

    filtered_df = df.copy()
    if selected_category:
        filtered_df = filtered_df[filtered_df["Category"].isin(selected_category)]
    if selected_accent:
        filtered_df = filtered_df[filtered_df["Accent"].isin(selected_accent)]
    if selected_styles:
        filtered_df = filtered_df[
            filtered_df["Style 1"].isin(selected_styles) | filtered_df["Style 2"].isin(selected_styles)
        ]
    if selected_tags:
        filtered_df = filtered_df[
            filtered_df["Voice123 Tag 1"].isin(selected_tags) | filtered_df["Voice123 Tag 2"].isin(selected_tags)
        ]
    if search:
        filtered_df = filtered_df[
            filtered_df["ID"].str.contains(search, case=False) |
            filtered_df["Voice123 Upload Name"].str.contains(search, case=False)
        ]

    st.subheader("Demo Cards")
    for _, row in filtered_df.iterrows():
        with st.container():
            st.markdown(f"### {row['Voice123 Upload Name']}")
            st.markdown(f"**Accent:** {row['Accent']}  
"
                        f"**Styles:** {row['Style 1']} + {row['Style 2']}  
"
                        f"**Tags:** {row['Voice123 Tag 1']}, {row['Voice123 Tag 2']}  
"
                        f"**Category:** {row['Category']}  
"
                        f"**Script File:** {row['Script Filename']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.checkbox("Script Written", value=row["Script Written"], key=f"written_{row['ID']}", disabled=True)
            with col2:
                st.checkbox("Recorded", value=row["Recorded"], key=f"recorded_{row['ID']}", disabled=True)
            with col3:
                st.checkbox("Uploaded", value=row["Uploaded"], key=f"uploaded_{row['ID']}", disabled=True)
            if row["ID"] in scripts:
                with st.expander("Show Script"):
                    st.markdown(scripts[row["ID"]], unsafe_allow_html=True)
            st.markdown("---")

# --- Spreadsheet View ---
else:
    st.subheader("Full Tracker Table")
    st.dataframe(df, use_container_width=True)
