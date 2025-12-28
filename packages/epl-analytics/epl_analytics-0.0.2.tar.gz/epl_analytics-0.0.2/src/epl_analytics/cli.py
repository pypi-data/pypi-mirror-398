# src/epl_analytics/cli.py

"""
Interface de ligne de commande pour EPL Analytics.
"""

import typer
from typing_extensions import Annotated
import pandas as pd
from rich.console import Console
from rich.table import Table
import os
import subprocess

from epl_analytics import analysis, visualization, __version__

# Création de l'application Typer
app = typer.Typer(
    no_args_is_help=True,
    help="""
    **EPL Analytics CLI** : Un outil puissant en ligne de commande pour analyser les données de notes des étudiants
    et générer des visualisations.

    ---\n
    **Utilisation générale :**

    Pour obtenir de l'aide sur une commande spécifique, utilisez :
    `epl-analytics [COMMANDE] --help`

    Exemple : `epl-analytics calculer-stats-par-groupe --help`

    ---\n
    **Commandes disponibles :**

    *   `calculer-stats-par-groupe` : Analyse les notes groupées par une colonne spécifiée (ex: département, UE).
    *   `calculer-stats-enseignants` : Fournit des statistiques détaillées par enseignant.
    *   `tracer-distribution-notes` : Génère un histogramme de la répartition générale des notes.
    *   `tracer-boxplot-notes` : Crée un boxplot pour visualiser la distribution des notes par catégorie.
    """,
    add_completion=False,
    rich_markup_mode="markdown"
)

console = Console()

def save_df(df: pd.DataFrame, output_path: str):
    """Sauvegarde un DataFrame dans un fichier (CSV ou Excel)."""
    if output_path.endswith(".csv"):
        df.to_csv(output_path, index=False, sep=';', decimal=',')
        console.print(f":floppy_disk: Résultats sauvegardés dans [bold green]{output_path}[/bold green]")
    elif output_path.endswith(".xlsx"):
        df.to_excel(output_path, index=False)
        console.print(f":floppy_disk: Résultats sauvegardés dans [bold green]{output_path}[/bold green]")
    else:
        console.print(f"[bold red]Erreur :[/bold red] Le fichier de sortie doit avoir une extension .csv ou .xlsx. Extensions acceptées : .csv, .xlsx.")
        raise typer.Exit(1)

def version_callback(value: bool):
    """Affiche la version du package et quitte."""
    if value:
        console.print(f"epl-analytics version : {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True, help="Affiche la version de l'outil EPL Analytics et quitte.")
    ] = False
):
    """
    EPL Analytics : une CLI complète pour interagir avec les fonctionnalités d'analyse et de visualisation.
    """
    pass

@app.command(name="calculer-stats-par-groupe")
def calculate_stats_by_group(
    fichier: Annotated[
        str,
        typer.Argument(help="Chemin complet vers le fichier de données CSV contenant les notes.")
    ],
    grouper_par: Annotated[
        str,
        typer.Option("--grouper-par", "-g", help="[Obligatoire] Nom de la colonne dans le fichier CSV par laquelle les statistiques doivent être groupées (ex: 'departement_nom', 'ue_nom').")
    ],
    sortie: Annotated[
        str,
        typer.Option("--sortie", "-s", help="[Optionnel] Chemin pour sauvegarder les résultats des statistiques. Le fichier peut être au format .csv ou .xlsx.")
    ] = None
):
    """
    Calcule et affiche les statistiques descriptives des notes, groupées par une colonne spécifiée.

    Exemple d'utilisation :

    `epl-analytics calculer-stats-par-groupe data/notes_epl_simulees.csv --grouper-par departement_nom`

    Pour sauvegarder les résultats dans un fichier :

    `epl-analytics calculer-stats-par-groupe data/notes_epl_simulees.csv -g ue_nom -s statistiques_ue.csv`
    """
    try:
        df = pd.read_csv(fichier, sep=';', decimal=',')
        df['note'] = pd.to_numeric(df['note'], errors='coerce')

        stats_df = analysis.calculate_stats_by_group(df, grouper_par)

        if stats_df.empty:
            console.print(f"[yellow]Aucune donnée trouvée pour le groupement par '{grouper_par}'.[/yellow]")
            raise typer.Exit()

        console.print(f"\n:bar_chart: [bold green]Statistiques groupées par '{grouper_par}':[/bold green]")
        
        table = Table(show_header=True, header_style="bold magenta")
        for col in stats_df.columns:
            table.add_column(col)
        
        for _, row in stats_df.iterrows():
            table.add_row(*[str(item) for item in row.values])
        console.print(table)
        
        if sortie:
            save_df(stats_df, sortie)

    except FileNotFoundError:
        console.print(f"[bold red]Erreur :[/bold red] Fichier non trouvé à '{fichier}'. Veuillez vérifier le chemin.")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Une erreur est survenue lors du calcul des statistiques :[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command(name="calculer-stats-enseignants")
def calculate_teacher_stats(
    fichier: Annotated[
        str,
        typer.Argument(help="Chemin complet vers le fichier de données CSV contenant les notes.")
    ],
    sortie: Annotated[
        str,
        typer.Option("--sortie", "-s", help="[Optionnel] Chemin pour sauvegarder les résultats des statistiques. Le fichier peut être au format .csv ou .xlsx.")
    ] = None
):
    """
    Calcule et affiche les statistiques descriptives pour chaque enseignant.

    Exemple d'utilisation :

    `epl-analytics calculer-stats-enseignants data/notes_epl_simulees.csv`

    Pour sauvegarder les résultats :

    `epl-analytics calculer-stats-enseignants data/notes_epl_simulees.csv -s statistiques_enseignants.xlsx`
    """
    try:
        df = pd.read_csv(fichier, sep=';', decimal=',')
        df['note'] = pd.to_numeric(df['note'], errors='coerce')

        stats_df = analysis.calculate_teacher_stats(df)

        if stats_df.empty:
            console.print("[yellow]Impossible de calculer les statistiques par enseignant. Les données sont peut-être vides ou la colonne 'enseignants' est manquante.[/yellow]")
            raise typer.Exit()

        console.print("\n:school_satchel: [bold green]Statistiques par Enseignant :[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        for col in stats_df.columns:
            table.add_column(col)
        for _, row in stats_df.iterrows():
            table.add_row(*[str(item) for item in row.values])
        console.print(table)
        
        if sortie:
            save_df(stats_df, sortie)

    except FileNotFoundError:
        console.print(f"[bold red]Erreur :[/bold red] Fichier non trouvé à '{fichier}'. Veuillez vérifier le chemin.")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Une erreur est survenue lors du calcul des statistiques :[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command("tracer-distribution-notes")
def plot_grade_distribution(
    fichier: Annotated[str, typer.Argument(help="Chemin complet vers le fichier de données CSV contenant les notes.")],
    sortie: Annotated[str, typer.Option("--sortie", "-s", help="[Obligatoire] Chemin pour sauvegarder le graphique. L'extension du fichier (ex: .png, .jpg, .pdf) déterminera le format de sortie.")]
):
    """
    Génère un histogramme de la distribution globale des notes à partir d'un fichier CSV.

    Le graphique sera sauvegardé dans le fichier spécifié par l'option '--sortie'.

    Exemple d'utilisation :

    `epl-analytics tracer-distribution-notes data/notes_epl_simulees.csv --sortie repartition_notes.png`
    """
    try:
        df = pd.read_csv(fichier, sep=';', decimal=',')
        titre = f"Distribution des notes du fichier {os.path.basename(fichier)}"
        fig = visualization.plot_grade_distribution(df, titre)
        fig.savefig(sortie)
        console.print(f":chart_increasing: Graphique sauvegardé dans [bold green]{sortie}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Une erreur est survenue lors de la création du graphique :[/bold red] {e}")
        raise typer.Exit(1)

@app.command("tracer-boxplot-notes")
def plot_boxplot(
    fichier: Annotated[str, typer.Argument(help="Chemin complet vers le fichier de données CSV contenant les notes.")],
    colonne_x: Annotated[str, typer.Option("--colonne-x", help="[Obligatoire] Nom de la colonne dans le fichier CSV pour grouper les données sur l'axe des X (ex: 'departement_nom').")],
    sortie: Annotated[str, typer.Option("--sortie", "-s", help="[Obligatoire] Chemin pour sauvegarder le graphique. L'extension du fichier (ex: .png, .jpg, .pdf) déterminera le format de sortie.")]
):
    """
    Génère un boxplot pour visualiser la distribution des notes, groupées par une colonne spécifiée.

    Le graphique sera sauvegardé dans le fichier spécifié par l'option '--sortie'.

    Exemple d'utilisation :

    `epl-analytics tracer-boxplot-notes data/notes_epl_simulees.csv --colonne-x departement_nom --sortie boxplot_departement.png`
    """
    try:
        df = pd.read_csv(fichier, sep=';', decimal=',')
        titre = f"Distribution des notes par {colonne_x}"
        fig = visualization.plot_grade_boxplot(df, colonne_x, titre)
        fig.savefig(sortie)
        console.print(f":chart_increasing: Graphique sauvegardé dans [bold green]{sortie}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Une erreur est survenue lors de la création du graphique :[/bold red] {e}")
        raise typer.Exit(1)

@app.command()
def dashboard():
    """
    Lance le tableau de bord interactif Streamlit.
    """
    console.print("Lancement du tableau de bord Streamlit...")
    try:
        # Chemin vers le fichier dashboard.py
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
        
        # Commande à exécuter
        command = ["streamlit", "run", dashboard_path]
        
        # Exécution de la commande
        subprocess.run(command, check=True)
        
    except FileNotFoundError:
        console.print("[bold red]Erreur :[/bold red] La commande 'streamlit' n'a pas été trouvée. Assurez-vous que Streamlit est bien installé dans votre environnement.")
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Une erreur est survenue lors du lancement du tableau de bord :[/bold red]\n{e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Une erreur inattendue est survenue :[/bold red] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
