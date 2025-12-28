# src/epl_analytics/analysis.py

"""
Module for performing statistical analysis on EPL student grade data.
"""

import pandas as pd
import numpy as np

def calculate_stats_by_group(df, group_by_col):
    """
    Calculates descriptive statistics for notes, grouped by a specific column.

    Args:
        df (pd.DataFrame): The input DataFrame with grade data.
        group_by_col (str or list): The column(s) to group by (e.g., 'ue_code').

    Returns:
        pd.DataFrame: A DataFrame with statistics (mean, median, etc.) for each group.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    stats = df.groupby(group_by_col)['note'].agg(
        ['mean', 'median', 'std', 'min', 'max', 'count']
    ).reset_index()

    # Calculate success rate (grade >= 10)
    success_df = df[df['note'] >= 10]
    success_counts = success_df.groupby(group_by_col).size().reset_index(name='passing_grades')

    # Total valid grades (not NaN)
    total_counts = df.dropna(subset=['note']).groupby(group_by_col).size().reset_index(name='total_grades')

    # Merge stats
    stats = pd.merge(stats, total_counts, on=group_by_col, how='left')
    stats = pd.merge(stats, success_counts, on=group_by_col, how='left')

    stats['passing_grades'] = stats['passing_grades'].fillna(0).astype(int)
    stats['taux_reussite'] = (stats['passing_grades'] / stats['total_grades']) * 100
    stats['taux_reussite'] = stats['taux_reussite'].fillna(0)

    # Formatting
    stats['mean'] = stats['mean'].round(2)
    stats['median'] = stats['median'].round(2)
    stats['std'] = stats['std'].round(2)
    stats['taux_reussite'] = stats['taux_reussite'].round(2)

    return stats.rename(columns={
        'mean': 'Moyenne',
        'median': 'Médiane',
        'std': 'Écart-type',
        'min': 'Note Min',
        'max': 'Note Max',
        'count': 'Nombre de Notes (avec NaN)',
        'total_grades': 'Nombre de Notes Valides',
        'passing_grades': 'Nombre de Notes >= 10',
        'taux_reussite': 'Taux de Réussite (%)'
    })


def calculate_teacher_stats(df):
    """
    Calculates descriptive statistics per teacher.

    This function handles UEs with multiple teachers by creating a separate
    entry for each teacher.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with statistics for each teacher.
    """
    if df is None or df.empty or 'enseignants' not in df.columns:
        return pd.DataFrame()

    # Create a copy to avoid SettingWithCopyWarning
    df_teacher = df.dropna(subset=['enseignants', 'note']).copy()

    # Split the 'enseignants' string into a list of teachers
    df_teacher['enseignants'] = df_teacher['enseignants'].str.split(';')

    # Explode the DataFrame to have one row per teacher per student grade
    exploded_df = df_teacher.explode('enseignants')
    exploded_df['enseignants'] = exploded_df['enseignants'].str.strip()

    # Now, calculate stats by teacher
    teacher_stats = calculate_stats_by_group(exploded_df, group_by_col='enseignants')

    return teacher_stats