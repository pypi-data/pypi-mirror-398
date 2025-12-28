# src/epl_analytics/dashboard.py

"""
The main Streamlit dashboard application for EPL Analytics.
"""

import streamlit as st
import pandas as pd
from epl_analytics import data_loader, analysis, visualization, exporter

def main():
    """The main function to run the Streamlit dashboard."""
    st.set_page_config(layout="wide")
    st.title(" Analyse des Notes de l'EPL")

    # --- Sidebar for file upload and main controls ---
    with st.sidebar:
        st.header("1. Chargement des Données")
        uploaded_file = st.file_uploader(
            "Chargez votre fichier CSV de notes", type=["csv"]
        )
        
        # Load data using the loader module
        epl_data = data_loader.load_data(uploaded_file)

        analysis_level = None
        if epl_data is not None:
            st.header("2. Niveau d'Analyse")
            analysis_level = st.selectbox(
                "Choisir le niveau d'analyse :",
                ["Vue d'ensemble", "Par Département", "Par UE (Unité d'Enseignement)", "Par Enseignant"]
            )

    # --- Main panel for displaying data and plots ---
    if epl_data is None:
        st.info("👋 Bienvenue ! Pour commencer, veuillez charger un fichier de données via le menu latéral.")
        

    else:
        df = epl_data.data  # Extract the DataFrame from our object
        
        # --- Display filtered data ---
        st.header("Filtres des données")
        
        # Create columns for filters
        col1, col2 = st.columns(2)
        
        # Department filter
        departments = df['departement_nom'].unique()
        selected_dept = col1.multiselect("Filtrer par Département:", options=departments, default=departments)
        
        # Filter dataframe based on selected departments
        filtered_df = df[df['departement_nom'].isin(selected_dept)]
        
        # UE filter (updates based on department selection)
        ues = filtered_df['ue_nom'].unique()
        selected_ue = col2.multiselect("Filtrer par UE:", options=ues, default=ues)

        # Final filtered dataframe
        final_df = filtered_df[filtered_df['ue_nom'].isin(selected_ue)]
        
        st.dataframe(final_df.head(10))
        st.write(f"Affichage de {final_df.shape[0]} lignes sur {df.shape[0]} au total.")
        st.write("---")

        # --- Perform and display analysis based on selection ---
        if analysis_level == "Vue d'ensemble":
            st.header("📈 Vue d'ensemble des Notes")
            fig = visualization.plot_grade_distribution(final_df, "Distribution de toutes les notes filtrées")
            st.pyplot(fig)

        elif analysis_level == "Par Département":
            st.header("🏢 Analyse par Département")
            stats_df = analysis.calculate_stats_by_group(final_df, 'departement_nom')
            
            st.subheader("Statistiques descriptives")
            st.dataframe(stats_df)
            
            col1, col2 = st.columns(2)
            fig1 = visualization.plot_stats_comparison(stats_df, x_col='departement_nom', y_col='Moyenne', title="Moyenne des notes par département")
            col1.pyplot(fig1)
            fig2 = visualization.plot_stats_comparison(stats_df, x_col='departement_nom', y_col='Taux de Réussite (%)', title="Taux de réussite par département")
            col2.pyplot(fig2)
            
            fig3 = visualization.plot_grade_boxplot(final_df, x_col='departement_nom', title="Distribution des notes par département")
            st.pyplot(fig3)

        elif analysis_level == "Par UE (Unité d'Enseignement)":
            st.header("📚 Analyse par UE")
            stats_df = analysis.calculate_stats_by_group(final_df, 'ue_nom')

            st.subheader("Statistiques descriptives par UE")
            st.dataframe(stats_df)
            
            # Download button for UE stats
            csv_bytes = exporter.convert_df_to_csv_bytes(stats_df)
            st.download_button(
                label="📥 Télécharger les stats des UE (CSV)",
                data=csv_bytes,
                file_name='stats_ue.csv',
                mime='text/csv',
            )
            
            col1, col2 = st.columns(2)
            fig1 = visualization.plot_stats_comparison(stats_df, x_col='ue_nom', y_col='Moyenne', title="Moyenne des notes par UE")
            col1.pyplot(fig1)
            fig2 = visualization.plot_stats_comparison(stats_df, x_col='ue_nom', y_col='Taux de Réussite (%)', title="Taux de réussite par UE")
            col2.pyplot(fig2)

            fig3 = visualization.plot_grade_boxplot(final_df, x_col='ue_nom', title="Distribution des notes par UE")
            st.pyplot(fig3)

        elif analysis_level == "Par Enseignant":
            st.header("🧑‍🏫 Analyse par Enseignant")
            stats_df = analysis.calculate_teacher_stats(final_df)

            st.subheader("Statistiques descriptives par Enseignant")
            st.dataframe(stats_df)

            # Download button for teacher stats
            csv_bytes = exporter.convert_df_to_csv_bytes(stats_df)
            st.download_button(
                label="📥 Télécharger les stats des enseignants (CSV)",
                data=csv_bytes,
                file_name='stats_enseignants.csv',
                mime='text/csv',
            )

            col1, col2 = st.columns(2)
            fig1 = visualization.plot_stats_comparison(stats_df, x_col='enseignants', y_col='Moyenne', title="Moyenne des notes par enseignant")
            col1.pyplot(fig1)
            fig2 = visualization.plot_stats_comparison(stats_df, x_col='enseignants', y_col='Taux de Réussite (%)', title="Taux de réussite par enseignant")
            col2.pyplot(fig2)

if __name__ == "__main__":
    main()