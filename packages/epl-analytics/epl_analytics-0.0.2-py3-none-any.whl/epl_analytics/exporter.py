# src/epl_analytics/exporter.py

"""
Module for exporting dataframes to various formats, optimized for Streamlit.
"""

import pandas as pd
from io import BytesIO

def convert_df_to_csv_bytes(df):
    """
    Converts a DataFrame to a CSV stored in a bytes object.

    This is the preferred format for Streamlit's st.download_button.

    Args:
        df (pd.DataFrame): The DataFrame to convert.

    Returns:
        bytes: The CSV data as a bytes object.
    """
    if df is None or df.empty:
        return b""

    # Use a standard, portable encoding
    return df.to_csv(index=False, sep=';', decimal=',').encode('utf-8')

def convert_df_to_excel_bytes(df):
    """
    Converts a DataFrame to an Excel file stored in a bytes object.
    This is a user-friendly alternative to CSV for many users.

    Args:
        df (pd.DataFrame): The DataFrame to convert.

    Returns:
        bytes: The Excel data as a bytes object.
    """
    if df is None or df.empty:
        return b""
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Export')
    
    # Get the bytes from the BytesIO object
    processed_data = output.getvalue()
    return processed_data