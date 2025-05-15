import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer, util

SIMILARITY_THRESHOLDS = {
    "full": 0.85,
    "partial": 0.65
}

MODEL_NAME = 'all-MiniLM-L6-v2'

@st.cache_resource
def get_model():
    return SentenceTransformer(MODEL_NAME)

@st.cache_resource
def encode_text_list(texts):
    model = get_model()
    return model.encode(texts, convert_to_tensor=True)

def load_controls(file):
    df = pd.read_excel(file)
    df.columns = [col.strip().lower() for col in df.columns]
    required = {'control_id', 'control_category', 'control_subcategory', 'control_requirement'}
    if not required.issubset(df.columns):
        raise ValueError("Excel must contain: control_id, control_category, control_subcategory, control_requirement")
    return df.dropna(subset=['control_id', 'control_requirement']).drop_duplicates(subset='control_id')

def compute_similarity_matrix(df_source, df_target):
    df_source = df_source.copy()
    df_target = df_target.copy()
    df_source['control_requirement'] = df_source['control_requirement'].fillna('').astype(str)
    df_target['control_requirement'] = df_target['control_requirement'].fillna('').astype(str)

    src_emb = encode_text_list(df_source['control_requirement'].tolist())
    tgt_emb = encode_text_list(df_target['control_requirement'].tolist())
    return util.cos_sim(src_emb, tgt_emb).cpu().numpy()

def map_controls(df_source, df_target):
    sim_matrix = compute_similarity_matrix(df_source, df_target)
    mapping_results = []
    match_type_counter = {"Full Match": 0, "Partial Match": 0, "No Match": 0}

    for i, src_row in df_source.iterrows():
        src_req = str(src_row['control_requirement'])

        matches = []
        for j, tgt_row in df_target.iterrows():
            score = sim_matrix[i][j]
            if score >= SIMILARITY_THRESHOLDS['partial']:
                match_type = "Full Match" if score >= SIMILARITY_THRESHOLDS['full'] else "Partial Match"
                matches.append((score, str(tgt_row['control_id']), str(tgt_row['control_requirement']), match_type))

        if matches:
            top_matches = sorted(matches, key=lambda x: x[0], reverse=True)[:3]
            avg_score = np.mean([m[0] for m in top_matches])
            match_type = "Full Match" if any(m[3] == "Full Match" for m in top_matches) else "Partial Match"
            match_type_counter[match_type] += 1
            mapping_results.append({
                "Source - Control ID": str(src_row['control_id']),
                "Source - Requirement": src_req,
                "Target - Control ID(s)": ", ".join([m[1] for m in top_matches]),
                "Target - Requirement(s)": "; ".join([m[2] for m in top_matches]),
                "Similarity Score": round(avg_score * 100, 2),
                "Match Type": match_type,
                "Justification": "Click to generate"
            })
        else:
            match_type_counter["No Match"] += 1
            mapping_results.append({
                "Source - Control ID": str(src_row['control_id']),
                "Source - Requirement": src_req,
                "Target - Control ID(s)": "—",
                "Target - Requirement(s)": "—",
                "Similarity Score": 0.0,
                "Match Type": "No Match",
                "Justification": "No sufficiently similar control identified."
            })

    coverage = ((match_type_counter['Full Match'] + match_type_counter['Partial Match']) / len(df_source)) * 100
    return pd.DataFrame(mapping_results), round(coverage, 2), match_type_counter, sim_matrix

def summarize_by_category(df_mapping, df_ref):
    categories = df_ref[['control_id', 'control_category']].dropna().astype(str).set_index('control_id')
    df = df_mapping.copy()
    df['control_id'] = df['Source - Control ID']
    df = df.merge(categories, on='control_id', how='left')
    df = df[df['control_category'].notna()]

    summary = df.groupby(['control_category', 'Match Type']).size().unstack(fill_value=0)

    for col in ['Full Match', 'Partial Match', 'No Match']:
        if col not in summary.columns:
            summary[col] = 0

    summary['Total'] = summary[['Full Match', 'Partial Match', 'No Match']].sum(axis=1)
    summary['Coverage %'] = (
        (summary['Full Match'] + summary['Partial Match']) / summary['Total'].replace(0, np.nan)
    ) * 100
    summary['Coverage %'] = summary['Coverage %'].fillna(0)

    for col in ['Full Match', 'Partial Match', 'No Match', 'Total']:
        summary[col] = summary[col].fillna(0).astype(int)

    return summary.reset_index()