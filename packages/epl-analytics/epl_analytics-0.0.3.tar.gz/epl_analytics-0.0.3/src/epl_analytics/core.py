# src/epl_analytics/core.py

"""
Fonctionnalité principale du package epl_analytics.
"""

import pandas as pd

class EPLAnalytics:
    """
    Classe principale pour EPL Analytics.

    Cette classe contient les données de notes et fournit des méthodes d'analyse.
    """
    def __init__(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Les données doivent être un DataFrame pandas")
        self.data = data

    def __repr__(self):
        return f"EPLAnalytics(data_shape={self.data.shape})"

    def _repr_html_(self):
        """
        Représentation HTML pour les notebooks Jupyter.
        """
        # Affiche l'en-tête du DataFrame
        html = "<h3>Données EPL Analytics</h3>"
        html += self.data.head().to_html()
        return html

    @staticmethod
    def from_csv(file_path, sep=';', decimal=','):
        """
        Charge les données à partir d'un fichier CSV.

        Args:
            file_path (str): Le chemin vers le fichier CSV.
            sep (str): Le séparateur pour le fichier CSV.
            decimal (str): Le caractère décimal pour le fichier CSV.

        Returns:
            EPLAnalytics: Une instance de la classe EPLAnalytics.
        """
        try:
            df = pd.read_csv(file_path, sep=sep, decimal=decimal)
            # --- Nettoyage des données ---
            # Assurez-vous que 'note' est un type numérique, en convertissant les erreurs en NaN
            df['note'] = pd.to_numeric(df['note'], errors='coerce')
            return EPLAnalytics(df)
        except FileNotFoundError:
            print(f"Erreur : Le fichier n'a pas été trouvé à l'adresse {file_path}")
            return None
        except Exception as e:
            print(f"Une erreur s'est produite lors de la lecture du fichier : {e}")
            return None