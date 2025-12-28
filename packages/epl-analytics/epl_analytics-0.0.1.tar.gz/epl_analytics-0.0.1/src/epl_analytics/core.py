# src/epl_analytics/core.py

"""
Core functionality for the epl_analytics package.
"""

import pandas as pd

class EPLAnalytics:
    """
    Main class for EPL Analytics.

    This class holds the grades data and provides methods for analysis.
    """
    def __init__(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
        self.data = data

    def __repr__(self):
        return f"EPLAnalytics(data_shape={self.data.shape})"

    def _repr_html_(self):
        """
        HTML representation for Jupyter Notebooks.
        """
        # Display the head of the dataframe
        html = "<h3>EPL Analytics Data</h3>"
        html += self.data.head().to_html()
        return html

    @staticmethod
    def from_csv(file_path, sep=';', decimal=','):
        """
        Loads data from a CSV file.

        Args:
            file_path (str): The path to the CSV file.
            sep (str): The separator for the CSV file.
            decimal (str): The decimal character for the CSV file.

        Returns:
            EPLAnalytics: An instance of the EPLAnalytics class.
        """
        try:
            df = pd.read_csv(file_path, sep=sep, decimal=decimal)
            # --- Data Cleaning ---
            # Ensure 'note' is a numeric type, coercing errors to NaN
            df['note'] = pd.to_numeric(df['note'], errors='coerce')
            return EPLAnalytics(df)
        except FileNotFoundError:
            print(f"Error: The file was not found at {file_path}")
            return None
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            return None