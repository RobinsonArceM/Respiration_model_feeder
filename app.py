import streamlit as st
import json
import os
import plotly.graph_objects as go
import pandas as pd

# Load metadata
with open("output_figures/metadata.json", "r") as f:
    metadata = json.load(f)

st.title("Sleep Stage Classification")

# Initialize annotations if not present
if "annotations" not in st.session_state:
    st.session_state.annotations = {}  # {(file, segment_idx): stage}

# Convert metadata to a user-friendly structure
file_list = list(metadata.keys())

# --- SIDEBAR LAYOUT ---

# 1. File and Segment Selection
st.sidebar.title("File and Segment Selection")
selected_file = st.sidebar.selectbox("Select a File", file_list)

segments_info = metadata[selected_file]["segments"]
num_segments = len(segments_info)
segment_options = list(range(1, num_segments + 1))  # segments numbered from 1
segment_idx = st.sidebar.selectbox("Select Segment", segment_options) - 1

current_annotation_key = (selected_file, segment_idx)

# 2. Classification Buttons in one row (W, N, R, A)
st.sidebar.markdown("### Classify this segment")
col_w, col_n, col_r, col_a = st.sidebar.columns(4)
if col_w.button("W"):
    st.session_state.annotations[current_annotation_key] = "W"
    st.sidebar.success("Segment classified as Wake (W)")
if col_n.button("N"):
    st.session_state.annotations[current_annotation_key] = "N"
    st.sidebar.success("Segment classified as Non-REM (N)")
if col_r.button("R"):
    st.session_state.annotations[current_annotation_key] = "R"
    st.sidebar.success("Segment classified as REM (R)")
if col_a.button("A"):
    st.session_state.annotations[current_annotation_key] = "A"
    st.sidebar.success("Segment classified as Artifact (A)")

# Count how many are classified vs total
classified_segments = sum(stage != "Undefined" for stage in st.session_state.annotations.values())
total_segments = sum(len(metadata[f]["segments"]) for f in file_list)
remaining_segments = total_segments - classified_segments

st.sidebar.markdown(f"**Classification Progress:** {classified_segments} / {total_segments}")
st.sidebar.markdown(f"**Segments Left:** {remaining_segments}")

# 3. Display the classification summary table
annotated_data = [
    (f, idx + 1, st.session_state.annotations.get((f, idx), "Undefined"))
    for f in file_list for idx in range(len(metadata[f]["segments"]))
]
file_summary = pd.DataFrame(annotated_data, columns=["File", "Segment", "Classification"])
st.sidebar.write("Available Files and Segment Counts:")
st.sidebar.dataframe(file_summary, use_container_width=True)

# 4. Upload and Download CSV Buttons at the bottom
uploaded_file = st.sidebar.file_uploader("Upload Annotations CSV", type="csv")
if uploaded_file is not None:
    uploaded_df = pd.read_csv(uploaded_file)
    # Pre-fill annotations from uploaded CSV
    for _, row in uploaded_df.iterrows():
        file_name = row["File"]
        s_idx = row["Segment"] - 1
        classification = row["SleepStage"]
        st.session_state.annotations[(file_name, s_idx)] = classification
    st.sidebar.success("Annotations loaded successfully!")

if st.session_state.annotations:
    ann_list = [(f, idx + 1, stage) for ((f, idx), stage) in st.session_state.annotations.items()]
    ann_df = pd.DataFrame(ann_list, columns=["File", "Segment", "SleepStage"])
    csv_data = ann_df.to_csv(index=False)
    st.sidebar.download_button("Download Annotations", csv_data, "annotations.csv", "text/csv")


# --- MAIN PAGE ---

st.subheader(f"File: {selected_file}, Segment: {segment_idx + 1}")

segment_data = segments_info[segment_idx]
line_fig_files = segment_data["line_figs"]
spectrogram_file = segment_data["spectrogram_fig"]

# Display line plots (single column)
for lf in line_fig_files:
    line_fig_path = os.path.join("output_figures", lf)
    with open(line_fig_path, "r") as f:
        fig_data = json.load(f)
    fig = go.Figure(fig_data)
    st.plotly_chart(fig, use_container_width=True)

# Display spectrogram (single column)
spec_fig_path = os.path.join("output_figures", spectrogram_file)
with open(spec_fig_path, "r") as f:
    spec_data = json.load(f)
spec_fig = go.Figure(spec_data)
st.plotly_chart(spec_fig, use_container_width=True)
