# src/epl_analytics/visualization.py

"""
Module pour créer des visualisations des données de notes analysées.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# --- Configuration du style Seaborn ---
sns.set_theme(style="whitegrid")

def plot_grade_distribution(df, title="Distribution des Notes"):
    """
    Trace un histogramme de la distribution des notes.

    Args:
        df (pd.DataFrame): DataFrame contenant la colonne 'note'.
        title (str): Le titre du graphique.

    Returns:
        matplotlib.figure.Figure: L'objet figure pour le graphique.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df['note'].dropna(), bins=20, kde=True, ax=ax)
    
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Note / 20", fontsize=12)
    ax.set_ylabel("Nombre d'étudiants", fontsize=12)
    ax.set_xlim(0, 20)
    
    return fig

def plot_stats_comparison(stats_df, x_col, y_col, title):
    """
    Crée un diagramme à barres pour comparer une statistique entre différents groupes.

    Args:
        stats_df (pd.DataFrame): DataFrame contenant les statistiques calculées.
        x_col (str): La colonne à utiliser pour l'axe des x (par exemple, 'ue_code').
        y_col (str): La colonne à utiliser pour l'axe des y (par exemple, 'Moyenne').
        title (str): Le titre du graphique.

    Returns:
        matplotlib.figure.Figure: L'objet figure pour le graphique.
    """
    if stats_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée à afficher.", ha='center', va='center')
        return fig

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(data=stats_df.sort_values(y_col, ascending=False), x=x_col, y=y_col, ax=ax, palette="viridis")

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("")
    ax.set_ylabel(y_col, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout() # Ajuster la mise en page pour laisser de la place aux étiquettes pivotées

    # Ajouter des étiquettes au-dessus des barres
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', fontsize=10)

    return fig

def plot_grade_boxplot(df, x_col, title):
    """
    Crée un boxplot pour visualiser les distributions de notes entre différents groupes.

    Args:
        df (pd.DataFrame): Le DataFrame avec les données de notes brutes.
        x_col (str): La colonne à grouper sur l'axe des x (par exemple, 'ue_code').
        title (str): Le titre du graphique.

    Returns:
        matplotlib.figure.Figure: L'objet figure pour le graphique.
    """
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée à afficher.", ha='center', va='center')
        return fig
        
    fig, ax = plt.subplots(figsize=(12, 7))
    order = df.groupby(x_col)['note'].median().sort_values(ascending=False).index
    sns.boxplot(data=df, x=x_col, y='note', ax=ax, order=order, palette="coolwarm")

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("")
    ax.set_ylabel("Note / 20", fontsize=12)
    ax.set_ylim(0, 21)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    return fig