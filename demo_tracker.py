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
            # Maintain bold/italic formatting for inner text
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

# Sidebar filters
with st.sidebar:
    st.title("Filters")
    category_filter = st.multiselect("Category", options=sorted(df["Category"].unique()))
    accent_filter = st.multiselect("Accent", options=sorted(df["Accent"].unique()))
    style_filter = st.multiselect("Styles", options=sorted(set(df["Style 1"]).union(df["Style 2"])))
    tag_filter = st.multiselect("Voice123 Tags", options=sorted(set(df["Voice123 Tag 1"]).union(df["Voice123 Tag 2"])))
    search_text = st.text_input("Search by Upload Name or ID")

# Apply filters
filtered_df = df.copy()
if category_filter:
    filtered_df = filtered_df[filtered_df["Category"].isin(category_filter)]
if accent_filter:
    filtered_df = filtered_df[filtered_df["Accent"].isin(accent_filter)]
if style_filter:
    filtered_df = filtered_df[filtered_df["Style 1"].isin(style_filter) | filtered_df["Style 2"].isin(style_filter)]
if tag_filter:
    filtered_df = filtered_df[filtered_df["Voice123 Tag 1"].isin(tag_filter) | filtered_df["Voice123 Tag 2"].isin(tag_filter)]
if search_text:
    filtered_df = filtered_df[
        filtered_df["ID"].str.contains(search_text, case=False, na=False) |
        filtered_df["Voice123 Upload Name"].str.contains(search_text, case=False, na=False)
    ]

# Status update section
st.title("Voice Demo Tracker")

edited_df = st.data_editor(
    filtered_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Script Written": st.column_config.CheckboxColumn("Script Written"),
        "Recorded": st.column_config.CheckboxColumn("Recorded"),
        "Uploaded": st.column_config.CheckboxColumn("Uploaded"),
    },
    hide_index=True
)

# Script preview panel
st.subheader("Script Preview")
selected_id = st.selectbox("Select a script ID to preview:", options=filtered_df["ID"])
script_text = scripts.get(selected_id, "<i>No script found for this ID.</i>")
st.markdown(script_text, unsafe_allow_html=True)
