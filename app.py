import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
from datetime import datetime
from mapping import load_controls, map_controls, summarize_by_category
from export_pdf import generate_pdf
from llm_utils import generate_justification_llm

st.set_page_config(page_title="Cybersecurity Mapping Tool", layout="wide")

st.title("🛡️ Cybersecurity Control Mapping Tool")

with st.sidebar:
    st.markdown("## ⚙️ Matching Settings")
    full_thresh = st.slider("🔒 Full match threshold", 0.75, 0.95, 0.85, 0.01)
    partial_thresh = st.slider("🔓 Partial match threshold", 0.5, full_thresh, 0.65, 0.01)

    st.markdown("## 📊 Analysis Overview")
    st.session_state.setdefault("summary_data", None)
    if st.session_state["summary_data"]:
        st.markdown(st.session_state["summary_data"])

tabs = st.tabs(["📁 Upload", "🔍 Matching", "📈 Visualisation", "🖨️ Export"])

with tabs[0]:
    st.markdown("Upload two Excel files with the following columns:")
    st.code("control_id, control_category, control_subcategory, control_requirement")

    col1, col2 = st.columns(2)
    with col1:
        src_file = st.file_uploader("📥 Upload Source Standard", type="xlsx", key="src")
    with col2:
        tgt_file = st.file_uploader("📤 Upload Target Standard", type="xlsx", key="tgt")

    if src_file and tgt_file:
        try:
            df_source = load_controls(src_file)
            df_target = load_controls(tgt_file)

            st.success("✅ Files loaded and validated.")
            st.markdown("### 👁️ Preview Source")
            st.dataframe(df_source.head())

            st.markdown("### 👁️ Preview Target")
            st.dataframe(df_target.head())

        except Exception as e:
            st.error(f"❌ File validation failed: {e}")

with tabs[1]:
    if "df_source" in locals() and "df_target" in locals():
        with st.spinner("🔍 Running analysis..."):
            df_mapping, coverage, match_counter, _ = map_controls(df_source, df_target, thresholds={"full": full_thresh, "partial": partial_thresh})
            summary_df = summarize_by_category(df_mapping, df_source)

            st.session_state["summary_data"] = f"""
            - **Total Controls**: {len(df_source)}  
            - **Full Matches**: {match_counter['Full Match']}  
            - **Partial Matches**: {match_counter['Partial Match']}  
            - **No Matches**: {match_counter['No Match']}  
            - **Coverage**: {coverage:.2f}%
            """

            categories = df_source['control_category'].dropna().unique().tolist()
            selected_categories = st.multiselect("📂 Filter by Category", categories, default=categories)
            search_text = st.text_input("🔍 Search within requirements")

            def get_category(control_id):
                row = df_source[df_source['control_id'] == control_id]
                return str(row['control_category'].values[0]) if not row.empty else None

            df_mapping['__category'] = df_mapping['Source - Control ID'].map(get_category)
            df_filtered = df_mapping[df_mapping['__category'].isin(selected_categories)]
            if search_text:
                df_filtered = df_filtered[df_filtered['Source - Requirement'].str.lower().str.contains(search_text.lower())]
            df_filtered.drop(columns="__category", inplace=True)

            st.subheader("📋 Matching Table")
            for idx, row in df_filtered.iterrows():
                with st.expander(f"🔗 {row['Source - Control ID']} → {row['Target - Control ID(s)']} ({row['Match Type']})"):
                    st.markdown(f"**Source Requirement:** {row['Source - Requirement']}")
                    st.markdown(f"**Target Requirement(s):** {row['Target - Requirement(s)']}")
                    if st.button(f"🧠 Generate justification for {row['Source - Control ID']}", key=idx):
                        justification = generate_justification_llm(row['Source - Requirement'], [row['Target - Requirement(s)']])
                        df_filtered.at[idx, "Justification"] = justification
                        st.markdown(f"**Justification + Gap:** {justification}")
                    else:
                        st.markdown(f"**Justification + Gap:** {row['Justification']}")

with tabs[2]:
    if "df_filtered" in locals():
        st.subheader("🍩 Coverage Donut")
        donut_labels = df_filtered["Match Type"].value_counts().index.tolist()
        donut_sizes = df_filtered["Match Type"].value_counts().tolist()
        fig2, ax2 = plt.subplots()
        ax2.pie(donut_sizes, labels=donut_labels, startangle=90, counterclock=False, wedgeprops=dict(width=0.4))
        ax2.axis("equal")
        st.pyplot(fig2)

        st.subheader("📊 Summary by Category")
        st.dataframe(summary_df)

with tabs[3]:
    if "df_filtered" in locals():
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button("⬇️ Download Mapping Table (.xlsx)", data=buffer, file_name="mapping_results.xlsx")

        if st.button("🖨️ Generate PDF Report"):
            filename = f"mapping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            generate_pdf(summary_df, coverage, filename)
            with open(filename, "rb") as f:
                st.download_button("⬇️ Download PDF Report", data=f, file_name=filename)