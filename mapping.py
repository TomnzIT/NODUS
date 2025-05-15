import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer, util
from llm_utils import generate_justification_llm

# Seuils de similarité pour les matchs
SIMILARITY_THRESHOLDS = {
    "full": 0.85,
    "partial": 0.65
}

MODEL_NAME = 'all-MiniLM-L6-v2'

@st.cache_resource
def load_model():
    """Charge le modèle BERT (caché entre les redémarrages)"""
    return SentenceTransformer(MODEL_NAME)

@st.cache_resource
def encode_controls(texts):
    """Encode une liste de textes en vecteurs BERT"""
    model = load_model()
    return model.encode(texts, convert_to_tensor=True)

def load_controls(file):
    """Charge et valide un fichier Excel de contrôles"""
    df = pd.read_excel(file)
    df.columns = [col.strip().lower() for col in df.columns]
    required = {'control_id', 'control_category', 'control_subcategory', 'control_requirement'}
    if not required.issubset(df.columns):
        raise ValueError("Excel must contain columns: control_id, control_category, control_subcategory, control_requirement")
    df = df.dropna(subset=['control_id', 'control_requirement']).drop_duplicates(subset='control_id')
    df = df[df['control_requirement'].str.len() > 3]  # Ignore les exigences vides ou trop courtes
    return df

def compute_similarity_matrix(df_source, df_target):
    """Calcule la matrice de similarité cosine entre contrôles source et cible"""
    src_texts = df_source['control_requirement'].fillna('').astype(str).tolist()
    tgt_texts = df_target['control_requirement'].fillna('').astype(str).tolist()
    src_emb = encode_controls(src_texts)
    tgt_emb = encode_controls(tgt_texts)
    return util.cos_sim(src_emb, tgt_emb).cpu().numpy()

def map_controls(df_source, df_target, thresholds=SIMILARITY_THRESHOLDS):
    """Effectue le mapping automatique des exigences"""
    sim_matrix = compute_similarity_matrix(df_source, df_target)
    mapping_results = []
    match_type_counter = {"Full Match": 0, "Partial Match": 0, "No Match": 0}

    for i, src_row in df_source.iterrows():
        src_req = str(src_row['control_requirement'])
        matches = [
            (sim_matrix[i][j], str(tgt_row['control_id']), str(tgt_row['control_requirement']),
             "Full Match" if sim_matrix[i][j] >= thresholds['full'] else "Partial Match")
            for j, tgt_row in df_target.iterrows()
            if sim_matrix[i][j] >= thresholds['partial']
        ]

        if matches:
            top_matches = sorted(matches, reverse=True)[:3]
            avg_score = np.mean([m[0] for m in top_matches])
            match_type = "Full Match" if any(m[3] == "Full Match" for m in top_matches) else "Partial Match"
            match_type_counter[match_type] += 1
            justification = "Click to generate"
            mapping_results.append({
                "Source - Control ID": str(src_row['control_id']),
                "Source - Requirement": src_req,
                "Target - Control ID(s)": ", ".join([m[1] for m in top_matches]),
                "Target - Requirement(s)": "; ".join([m[2] for m in top_matches]),
                "Similarity Score": round(avg_score * 100, 2),
                "Match Type": match_type,
                "Justification": justification
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
    """Regroupe les résultats par catégorie pour résumé visuel"""
    categories = df_ref[['control_id', 'control_category']].dropna().astype(str).set_index('control_id')
    df = df_mapping.copy()
    df['control_id'] = df['Source - Control ID']
    df = df.merge(categories, on='control_id', how='left')
    summary = df.groupby(['control_category', 'Match Type']).size().unstack(fill_value=0)
    summary['Total'] = summary.sum(axis=1)
    summary['Coverage %'] = ((summary.get('Full Match', 0) + summary.get('Partial Match', 0)) / summary['Total']) * 100
    return summary.reset_index()