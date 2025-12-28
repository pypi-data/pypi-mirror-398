# src/epl_analytics/exporter.py

"""
Module pour exporter les DataFrames vers différents formats, optimisé pour Streamlit.
"""

import pandas as pd
from io import BytesIO

def convert_df_to_csv_bytes(df):
    """
    Convertit un DataFrame en CSV stocké dans un objet bytes.

    C'est le format préféré pour le bouton de téléchargement (st.download_button) de Streamlit.

    Args:
        df (pd.DataFrame): Le DataFrame à convertir.

    Returns:
        bytes: Les données CSV sous forme d'objet bytes.
    """
    if df is None or df.empty:
        return b""

    # Utiliser un encodage standard et portable
    return df.to_csv(index=False, sep=';', decimal=',').encode('utf-8')

def convert_df_to_excel_bytes(df):
    """
    Convertit un DataFrame en un fichier Excel stocké dans un objet bytes.
    C'est une alternative conviviale au CSV pour de nombreux utilisateurs.

    Args:
        df (pd.DataFrame): Le DataFrame à convertir.

    Returns:
        bytes: Les données Excel sous forme d'objet bytes.
    """
    if df is None or df.empty:
        return b""
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Export')
    
    # Obtenir les octets de l'objet BytesIO
    processed_data = output.getvalue()
    return processed_data