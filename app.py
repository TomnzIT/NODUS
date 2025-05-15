import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import io
from datetime import datetime
from mapping import load_controls, map_controls, summarize_by_category
from export_pdf import generate_pdf
from llm_utils import generate_justification_llm

st.set_page_config(page_title="NODUS", layout="wide")

st.title("🛡️ NODUS")

st.markdown("""
Upload two Excel files with the following columns:
- `control_id`
- `control_category`
- `control_subcategory`
- `control_requirement`
""")

col1, col2 = st.columns(2)
with col1:
    src_file = st.file_uploader("📁 Upload Source Standard", type="xlsx")
with col2:
    tgt_file = st.file_uploader("📁 Upload Target Standard", type="xlsx")

if src_file and tgt_file:
    with st.spinner("🔍 Running analysis..."):
        try:
            df_source = load_controls(src_file)
            df_target = load_controls(tgt_file)

            df_mapping, coverage, match_counter, _ = map_controls(df_source, df_target)

            categories = sorted(df_source['control_category'].dropna().unique().tolist())
            selected_categories = st.multiselect("📂 Filter by Category", categories, default=categories)
            search_text = st.text_input("🔍 Search within requirements")

            def get_category(control_id):
                row = df_source[df_source['control_id'] == control_id]
                return str(row['control_category'].values[0]) if not row.empty else None

            df_mapping['__category'] = df_mapping['Source - Control ID'].map(get_category)
            df_filtered = df_mapping[df_mapping['__category'].isin(selected_categories)].copy()
            if search_text.strip():
                df_filtered = df_filtered[df_filtered["Source - Requirement"].fillna("").str.lower().str.contains(search_text.lower().strip())]
            df_filtered.drop(columns="__category", inplace=True)

            match_counter_filtered = df_filtered["Match Type"].value_counts().to_dict()
            for key in ["Full Match", "Partial Match", "No Match"]:
                match_counter_filtered.setdefault(key, 0)

            filtered_coverage = ((match_counter_filtered["Full Match"] + match_counter_filtered["Partial Match"])
                                 / max(len(df_filtered), 1)) * 100

            # Sidebar summary
            with st.sidebar:
                st.markdown("### ℹ️ Mapping Info")
                st.markdown(f"- **Mapped controls (filtered):** {len(df_filtered)}")
                st.markdown(f"- **Full Matches:** {match_counter_filtered['Full Match']}")
                st.markdown(f"- **Partial Matches:** {match_counter_filtered['Partial Match']}")
                st.markdown(f"- **No Matches:** {match_counter_filtered['No Match']}")
                st.markdown(f"- **Coverage:** `{round(filtered_coverage, 2)}%`")

            if st.button("📦 Generate all missing justifications"):
                for idx, row in df_filtered.iterrows():
                    key = f"justification_{idx}"
                    if st.session_state.get(key) in ["Click to generate", None]:
                        justification = generate_justification_llm(row["Source - Requirement"], [row['Target - Requirement(s)']])
                        st.session_state[key] = justification

            st.subheader("📋 Correspondence Table with On-Demand Justifications")
            for idx, row in df_filtered.iterrows():
                key = f"justification_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = row["Justification"]

                with st.expander(f"🔗 {row['Source - Control ID']} ➝ {row['Target - Control ID(s)']} ({row['Match Type']})"):
                    st.markdown(f"**Source:** {row['Source - Requirement']}")
                    st.markdown(f"**Target(s):** {row['Target - Requirement(s)']}")

                    if st.button(f"🧠 Generate justification", key=f"btn_{idx}"):
                        justification = generate_justification_llm(row["Source - Requirement"], [row['Target - Requirement(s)']])
                        st.session_state[key] = justification

                    st.markdown(f"**Justification + Gap:** {st.session_state[key]}")

            # XLSX export
            buffer = io.BytesIO()
            df_filtered.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button("⬇️ Download Mapping Table (.xlsx)", data=buffer, file_name="mapping_results.xlsx")

            # Donut chart
            st.subheader("🍩 Filtered Coverage Donut")
            fig2, ax2 = plt.subplots()
            ax2.pie(list(match_counter_filtered.values()), labels=list(match_counter_filtered.keys()),
                    startangle=90, counterclock=False, wedgeprops=dict(width=0.4), autopct='%1.1f%%')
            ax2.axis("equal")
            st.pyplot(fig2)

            # Heatmap
            st.subheader("🌡️ Similarity Heatmap by Category")
            df_filtered['Category'] = df_filtered['Source - Control ID'].map(get_category)
            pivot = df_filtered.pivot_table(index="Category", columns="Match Type", values="Similarity Score", aggfunc='mean').fillna(0)
            fig3, ax3 = plt.subplots(figsize=(8, 4))
            sns.heatmap(pivot, annot=True, fmt=".1f", cmap="coolwarm", ax=ax3)
            st.pyplot(fig3)

            # Résumé texte
            st.subheader("🧾 Filtered Summary")
            st.markdown(f"- **Total controls mapped (filtered):** {len(df_filtered)}")
            st.markdown(f"- **Full Matches:** {match_counter_filtered['Full Match']}")
            st.markdown(f"- **Partial Matches:** {match_counter_filtered['Partial Match']}")
            st.markdown(f"- **No Matches:** {match_counter_filtered['No Match']}")
            st.markdown(f"- **Coverage:** `{round(filtered_coverage, 2)}%`")

            # Export PDF
            summary_df_filtered = summarize_by_category(df_filtered, df_source)
            pdf_buffer = generate_pdf(summary_df_filtered, filtered_coverage)
            st.download_button(
                label="🖨️ Export & Download PDF Report",
                data=pdf_buffer,
                file_name=f"mapping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"❌ Error: {e}")
else:
    st.info("Please upload both Excel files to begin analysis.")