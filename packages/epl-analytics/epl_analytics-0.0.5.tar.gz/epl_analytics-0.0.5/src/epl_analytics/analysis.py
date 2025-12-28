# src/epl_analytics/analysis.py

"""
Module pour effectuer une analyse statistique sur les données de notes des étudiants de l'EPL.
"""

import pandas as pd
import numpy as np

def calculate_stats_by_group(df, group_by_col):
    """
    Calcule les statistiques descriptives pour les notes, regroupées par une colonne spécifique.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    stats = df.groupby(group_by_col)['note'].agg(
        ['mean', 'median', 'std', 'min', 'max', 'count']
    ).reset_index()

    # Calculer le taux de réussite (note >= 10)
    success_df = df[df['note'] >= 10]
    success_counts = success_df.groupby(group_by_col).size().reset_index(name='passing_grades')

    # Nombre total de notes valides (non NaN)
    total_counts = df.dropna(subset=['note']).groupby(group_by_col).size().reset_index(name='total_grades')

    # Fusionner les statistiques
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
    Calcule les statistiques descriptives par enseignant.

    Cette fonction gère les UE avec plusieurs enseignants en créant une entrée distincte
    pour chaque enseignant.

    Args:
        df (pd.DataFrame): Le DataFrame d'entrée.

    Returns:
        pd.DataFrame: Un DataFrame avec les statistiques pour chaque enseignant.
    """
    if df is None or df.empty or 'enseignants' not in df.columns:
        return pd.DataFrame()

    # Créer une copie pour éviter SettingWithCopyWarning
    df_teacher = df.dropna(subset=['enseignants', 'note']).copy()

    # Diviser la chaîne 'enseignants' en une liste d'enseignants
    df_teacher['enseignants'] = df_teacher['enseignants'].str.split(';')

    # Déployer le DataFrame pour avoir une ligne par enseignant par note d'étudiant
    exploded_df = df_teacher.explode('enseignants')
    exploded_df['enseignants'] = exploded_df['enseignants'].str.strip()

    # Maintenant, calculer les statistiques par enseignant
    teacher_stats = calculate_stats_by_group(exploded_df, group_by_col='enseignants')

    return teacher_stats

def rank_students(df, group_by_col):
    """
    Classe les étudiants en fonction de leur note au sein de chaque groupe.

    Args:
        df (pd.DataFrame): Le DataFrame avec les données de notes.
        group_by_col (str): La colonne à utiliser pour le groupement (ex: 'ue_nom', 'matiere').

    Returns:
        pd.DataFrame: Le DataFrame avec une colonne 'classement'.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df['classement'] = df.groupby(group_by_col)['note'].rank(method='dense', ascending=False)
    return df.sort_values(by=[group_by_col, 'classement'])

def get_admitted_students(df):
    """
    Retourne la liste des étudiants admis, avec leur moyenne générale.

    Un étudiant est considéré comme admis si sa moyenne générale est >= 10.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    student_avg = df.groupby(['student_id', 'nom', 'prénom'])['note'].mean().reset_index()
    admis = student_avg[student_avg['note'] >= 10].copy()
    admis.rename(columns={'note': 'moyenne_generale'}, inplace=True)
    admis['moyenne_generale'] = admis['moyenne_generale'].round(2)
    return admis.sort_values(by='moyenne_generale', ascending=False)

def rank_teachers(df, rank_by='Moyenne'):
    """
    Classe les enseignants en fonction d'une métrique de performance.

    Args:
        df (pd.DataFrame): Le DataFrame avec les données de notes.
        rank_by (str): La colonne à utiliser pour le classement ('Moyenne' or 'Taux de Réussite (%)').

    Returns:
        pd.DataFrame: Un DataFrame classé des statistiques des enseignants.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    teacher_stats = calculate_teacher_stats(df)
    if rank_by not in teacher_stats.columns:
        raise ValueError(f"La colonne de classement '{rank_by}' n'existe pas dans les statistiques des enseignants.")

    return teacher_stats.sort_values(by=rank_by, ascending=False)