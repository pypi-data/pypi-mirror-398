# src/epl_analytics/visualization.py

"""
Module for creating visualizations of the analyzed grade data.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# --- Seaborn Style Configuration ---
sns.set_theme(style="whitegrid")

def plot_grade_distribution(df, title="Distribution of Grades"):
    """
    Plots a histogram of the grade distribution.

    Args:
        df (pd.DataFrame): DataFrame containing the 'note' column.
        title (str): The title for the plot.

    Returns:
        matplotlib.figure.Figure: The figure object for the plot.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df['note'].dropna(), bins=20, kde=True, ax=ax)
    
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Note / 20", fontsize=12)
    ax.set_ylabel("Number of Students", fontsize=12)
    ax.set_xlim(0, 20)
    
    return fig

def plot_stats_comparison(stats_df, x_col, y_col, title):
    """
    Creates a bar chart to compare a statistic across different groups.

    Args:
        stats_df (pd.DataFrame): DataFrame containing calculated statistics.
        x_col (str): The column to use for the x-axis (e.g., 'ue_code').
        y_col (str): The column to use for the y-axis (e.g., 'Moyenne').
        title (str): The title for the plot.

    Returns:
        matplotlib.figure.Figure: The figure object for the plot.
    """
    if stats_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data to display.", ha='center', va='center')
        return fig

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(data=stats_df.sort_values(y_col, ascending=False), x=x_col, y=y_col, ax=ax, palette="viridis")

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("")
    ax.set_ylabel(y_col, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout() # Adjust layout to make room for rotated labels

    # Add labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', fontsize=10)

    return fig

def plot_grade_boxplot(df, x_col, title):
    """
    Creates a boxplot to visualize grade distributions across different groups.

    Args:
        df (pd.DataFrame): The DataFrame with raw grade data.
        x_col (str): The column to group by on the x-axis (e.g., 'ue_code').
        title (str): The title for the plot.

    Returns:
        matplotlib.figure.Figure: The figure object for the plot.
    """
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data to display.", ha='center', va='center')
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