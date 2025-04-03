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
            scripts[current_heading] += "<p>" + ''.join(html_parts) + "</p>"
    return scripts

df = load_data()
scripts = load_docx("voice_demo_scripts_mock.docx")

# Progress tracker
st.title("Voice Demo Tracker")
total = len(df)
recorded_count = df["Recorded"].sum()
written_count = df["Script Written"].sum()
uploaded_count = df["Uploaded"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Scripts Written", f"{written_count}/{total}")
col2.metric("Recorded", f"{recorded_count}/{total}")
col3.metric("Uploaded", f"{uploaded_count}/{total}")
st.progress(recorded_count / total)

# Persistent view toggle state
if "view_full" not in st.session_state:
    st.session_state.view_full = False
st.session_state.view_full = st.checkbox("Show full spreadsheet", value=st.session_state.view_full)

# Filters
filtered_df = df.copy()
with st.expander("Filter Demos"):
    selected_category = st.multiselect("Category", options=sorted(df["Category"].unique()))
    selected_accent = st.multiselect("Accent", options=sorted(df["Accent"].unique()))
    styles = sorted(set(df["Style 1"]).union(df["Style 2"]))
    selected_styles = st.multiselect("Styles", options=styles)
    selected_tags = st.multiselect("Voice123 Tags", options=sorted(set(df["Voice123 Tag 1"]).union(df["Voice123 Tag 2"])))
    search = st.text_input("Search Upload Name or ID")

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

# Spreadsheet view
if st.session_state.view_full:
    st.subheader("Full Tracker Table (read-only)")
    st.dataframe(df, use_container_width=True)
else:
    st.subheader("Card View (One at a Time)")

    if "card_index" not in st.session_state:
        st.session_state.card_index = 0

    if st.session_state.card_index >= len(filtered_df):
        st.session_state.card_index = 0

    if len(filtered_df) > 0:
        row = filtered_df.iloc[st.session_state.card_index]
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
        df.at[row.name, "Script Written"] = col1.checkbox("Script Written", value=row["Script Written"], key=f"written_{row['ID']}")
        df.at[row.name, "Recorded"] = col2.checkbox("Recorded", value=row["Recorded"], key=f"recorded_{row['ID']}")
        df.at[row.name, "Uploaded"] = col3.checkbox("Uploaded", value=row["Uploaded"], key=f"uploaded_{row['ID']}")

        if row["ID"] in scripts:
            with st.expander("Show Script"):
                st.markdown(scripts[row["ID"]], unsafe_allow_html=True)

        if st.button("Next"):
            st.session_state.card_index += 1
    else:
        st.info("No results match your filters.")
