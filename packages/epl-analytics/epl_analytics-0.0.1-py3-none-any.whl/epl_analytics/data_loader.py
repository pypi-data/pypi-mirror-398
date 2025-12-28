# src/epl_analytics/data_loader.py

"""
Module for loading and validating EPL student grade data.
"""

import pandas as pd
import streamlit as st

from .core import EPLAnalytics

@st.cache_data
def load_data(uploaded_file):
    """
    Loads student grade data from a CSV file and returns an EPLAnalytics object.

    This function is designed to work with Streamlit's file uploader.
    It reads the data, performs validation, and returns an EPLAnalytics object.

    Args:
        uploaded_file: A file-like object from st.file_uploader.

    Returns:
        EPLAnalytics: An object containing the validated data, or None if validation fails.
    """
    if uploaded_file is None:
        return None

    try:
        df = pd.read_csv(uploaded_file, sep=';', decimal=',')
    except Exception as e:
        st.error(f"Error reading the CSV file: {e}")
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
            "The uploaded file is missing one or more expected columns. "
            f"Required columns: {', '.join(expected_columns)}"
        )
        return None

    df['note'] = pd.to_numeric(df['note'], errors='coerce')

    st.success("Data loaded and validated successfully!")
    return EPLAnalytics(df)