# src/epl_analytics/data_loader.py

"""
Module pour charger et valider les données de notes des étudiants de l'EPL.
"""

import pandas as pd
import streamlit as st

from .core import EPLAnalytics

@st.cache_data
def load_data(uploaded_file):
    """
    Charge les données de notes des étudiants à partir d'un fichier CSV et retourne un objet EPLAnalytics.

    Cette fonction est conçue pour fonctionner avec l'outil de téléchargement de fichiers de Streamlit.
    Elle lit les données, effectue la validation et retourne un objet EPLAnalytics.

    Args:
        uploaded_file: Un objet de type fichier de st.file_uploader.

    Returns:
        EPLAnalytics: Un objet contenant les données validées, ou None si la validation échoue.
    """
    if uploaded_file is None:
        return None

    try:
        df = pd.read_csv(uploaded_file, sep=';', decimal=',')
    except Exception as e:
        st.error(f"Erreur de lecture du fichier CSV: {e}")
        return None

    expected_columns = [
        "student_id",
        "departement_code",
        "departement_nom",
        "ue_code",
        "ue_nom",
        "note",
        "enseignants"
    ]

    if not all(col in df.columns for col in expected_columns):
        st.error(
            "Le fichier téléversé ne contient pas toutes les colonnes attendues. "
            f"Colonnes requises : {', '.join(expected_columns)}"
        )
        return None

    df['note'] = pd.to_numeric(df['note'], errors='coerce')

    st.success("Données chargées et validées avec succès !")
    return EPLAnalytics(df)