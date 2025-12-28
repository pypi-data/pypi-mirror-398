# EPL Analytics 📊

**EPL Analytics** est une suite d'outils Python conçue pour l'analyse, la visualisation et l'exploration des données de notes des étudiants. Ce projet combine une bibliothèque Python flexible, une interface en ligne de commande (CLI) puissante, et un tableau de bord interactif pour fournir une solution complète d'analyse de données académiques.

Que vous soyez un développeur souhaitant intégrer des fonctionnalités d'analyse dans vos propres scripts, un analyste de données cherchant à explorer rapidement des statistiques depuis le terminal, ou un membre du personnel académique désirant une interface visuelle, EPL Analytics a l'outil qu'il vous faut.

## 🚀 Fonctionnalités Principales

*   **Tableau de Bord Interactif (Streamlit)** : Une application web élégante pour charger, filtrer et visualiser les données de manière intuitive.
*   **Interface en Ligne de Commande (CLI)** : Accédez à toutes les fonctionnalités d'analyse et de visualisation directement depuis votre terminal pour une automatisation et une intégration rapides.
*   **Bibliothèque Python** : Importez et utilisez les fonctions d'analyse et les objets de données dans vos propres scripts Python ou notebooks Jupyter pour une flexibilité maximale.
*   **Analyse Statistique Détaillée** : Calculez des statistiques descriptives (moyenne, médiane, écart-type, taux de réussite) pour l'ensemble des données ou groupées par département, unité d'enseignement (UE), ou enseignant.
*   **Visualisations Riches** : Générez des histogrammes, des boxplots et des graphiques en barres pour visualiser la distribution et la comparaison des notes.
*   **Export Facile** : Sauvegardez les tableaux de statistiques aux formats CSV ou Excel, et les graphiques aux formats PNG, JPG, ou PDF.
*   **Générateur de Données** : Un script est inclus pour créer un jeu de données simulé et réaliste, vous permettant de tester l'outil sans données réelles.

## ⚙️ Installation

### Depuis PyPI (Recommandé)

Si vous souhaitez simplement utiliser l'outil sans modifier le code source, vous pouvez l'installer directement depuis PyPI :

```bash
pip install epl-analytics
```

Après l'installation, vous pouvez vérifier que tout fonctionne en tapant :

```bash
epl-analytics --version
```
Vous aurez un guide d'utilisation en tapant :

```bash
epl-analytics --help
```


### Depuis la source (pour les développeurs)

Si vous prévoyez de contribuer au projet ou de modifier le code, suivez ces étapes :

1.  **Clonez ce dépôt ou téléchargez les fichiers du projet.**

2.  **Ouvrez un terminal et naviguez jusqu'au répertoire racine du projet.**

3.  **Installez le package et ses dépendances.**
    Cette commande installe le package `epl_analytics` en "mode éditable", ce qui signifie que toutes les modifications que vous apportez au code source seront immédiatement disponibles lorsque vous utiliserez l'outil.

```bash
pip install -e .
```

    Cette commande installe toutes les bibliothèques nécessaires, y compris Streamlit, Pandas, Typer, et Matplotlib.

## 📚 Guide d'Utilisation

Une fois le package installé, le moyen le plus simple de commencer est d'utiliser la commande `--help` pour voir toutes les commandes disponibles :

```bash
epl-analytics --help
```

EPL Analytics peut être utilisé de trois manières complémentaires :

### 1. Utilisation du Tableau de Bord Interactif

C'est le moyen le plus simple et le plus visuel d'explorer vos données.

**Lancement :**

```bash
epl-dashboard
```

ou

```bash
streamlit run src/epl_analytics/dashboard.py
```

Votre navigateur web s'ouvrira automatiquement sur l'application. Vous pourrez y charger votre fichier CSV, appliquer des filtres et visualiser les analyses en temps réel.

### 2. Utilisation de l'Interface en Ligne de Commande (CLI)

La CLI est parfaite pour l'automatisation, l'intégration dans des scripts shell, ou pour ceux qui préfèrent travailler depuis le terminal.

**Structure d'une commande :**
`epl-analytics [COMMANDE] [FICHIER_CSV] [OPTIONS]`

Pour obtenir de l'aide sur une commande, utilisez `--help`.
`epl-analytics [COMMANDE] --help`

---

#### **Commandes d'Analyse**

**`calculer-stats-par-groupe`**

Calcule les statistiques en groupant les données par une colonne. L'option `--grouper-par` est **obligatoire**.

*   **Exemple :** Analyser les notes par département.
```bash
epl-analytics calculer-stats-par-groupe data/notes_epl_simulees.csv --grouper-par departement_nom
```
*   **Exemple :** Analyser par UE et sauvegarder les résultats dans un fichier Excel.
```bash
epl-analytics calculer-stats-par-groupe data/notes_epl_simulees.csv -g ue_nom -s stats_par_ue.xlsx
```

**`calculer-stats-enseignants`**

Calcule les statistiques pour chaque enseignant.

*   **Exemple :**
```bash
epl-analytics calculer-stats-enseignants data/notes_epl_simulees.csv
```
*   **Exemple :** Sauvegarder les résultats dans un fichier CSV.
```bash
epl-analytics calculer-stats-enseignants data/notes_epl_simulees.csv -s stats_enseignants.csv
```

---

#### **Commandes de Visualisation**

**`tracer-distribution-notes`**

Génère un histogramme de la distribution de toutes les notes. L'option `--sortie` est **obligatoire**.

*   **Exemple :**
```bash
epl-analytics tracer-distribution-notes data/notes_epl_simulees.csv --sortie distribution_globale.png
```

**`tracer-boxplot-notes`**

Génère un boxplot des notes groupées par une colonne. Les options `--colonne-x` et `--sortie` sont **obligatoires**.

*   **Exemple :** Créer un boxplot des notes par département.
```bash
epl-analytics tracer-boxplot-notes data/notes_epl_simulees.csv --colonne-x departement_nom --sortie boxplot_par_dept.png
```

### 3. Utilisation en tant que Bibliothèque Python

Pour une flexibilité maximale, intégrez `epl_analytics` dans vos scripts Python ou notebooks Jupyter.

#### **Chargement des données**

La classe `EPLAnalytics` est le point d'entrée principal. Elle encapsule votre DataFrame et offre une intégration parfaite avec les notebooks (grâce à `_repr_html_`).

```python
from epl_analytics import EPLAnalytics

# Chargez vos données depuis un fichier CSV.
# La méthode 'from_csv' gère la lecture et un premier nettoyage.
epl_data = EPLAnalytics.from_csv('data/notes_epl_simulees.csv')

if epl_data:
    print("Données chargées avec succès !")
    
    # Dans un notebook Jupyter, cette ligne seule affichera un aperçu HTML du tableau.
    epl_data

    # Pour accéder au DataFrame Pandas sous-jacent :
    df = epl_data.data
    print(df.info())
```

#### **Analyse et Visualisation**

Utilisez les modules `analysis` et `visualization` pour effectuer des opérations sur votre DataFrame.

```python
from epl_analytics import analysis, visualization
import matplotlib.pyplot as plt

if epl_data:
    df = epl_data.data

    # ---
    # Analyse ---
    # Calculer les statistiques par département
    stats_dept = analysis.calculate_stats_by_group(df, 'departement_nom')
    print("\nStatistiques par département :")
    print(stats_dept)

    # ---
    # Visualisation ---
    # Créer un graphique de la distribution des notes et le sauvegarder
    fig_dist = visualization.plot_grade_distribution(df, "Distribution Globale des Notes")
    fig_dist.savefig("distribution_notes.png")
    print("\nGraphique de distribution sauvegardé dans 'distribution_notes.png'")

    # Créer un boxplot par UE
    fig_box = visualization.plot_grade_boxplot(df, x_col='ue_nom', title="Distribution des Notes par UE")
    fig_box.savefig("boxplot_ue.png")
    print("Graphique boxplot sauvegardé dans 'boxplot_ue.png'")
    
    # Pour afficher les graphiques dans un script, vous pouvez utiliser :
    # plt.show()
```

## 📄 Génération d'un Jeu de Données de Test

Si vous n'avez pas de fichier de notes, vous pouvez en générer un facilement.

1.  Assurez-vous que les dépendances sont installées (`pip install -e .`).
2.  Exécutez la commande suivante dans votre terminal :

    ```bash
    python scripts/1_generate_dataset.py
    ```

3.  Un fichier `notes_epl_simulees.csv` sera créé dans le dossier `data/`, prêt à être utilisé.

## 🏛️ Architecture du Code

Ce projet est conçu selon une architecture modulaire qui sépare clairement la logique métier (analyse, visualisation) des couches de présentation (CLI, tableau de bord).

### Structure du Projet

*   `src/epl_analytics/`: Contient le code source principal de la bibliothèque.
    *   `core.py`: Définit la classe centrale `EPLAnalytics`.
    *   `analysis.py`: Contient les fonctions pour l'analyse statistique.
    *   `visualization.py`: Regroupe les fonctions de création de graphiques.
    *   `data_loader.py`: Gère le chargement et la validation des données pour le tableau de bord.
    *   `exporter.py`: Fonctions pour exporter les données (CSV, Excel).
    *   `cli.py`: Implémente l'interface en ligne de commande.
    *   `dashboard.py`: Code de l'application Streamlit.
*   `scripts/`: Scripts utilitaires, comme la génération de données.
*   `pyproject.toml`: Fichier de configuration du projet et de ses dépendances.
*   `README.md`: Cette documentation.

### Composants Principaux

1.  **`core.py` et la classe `EPLAnalytics`**
    *   C'est le cœur de la bibliothèque. La classe `EPLAnalytics` agit comme un conteneur pour le `DataFrame` pandas, mais elle pourrait être étendue pour ajouter des méthodes ou des propriétés spécifiques au domaine.
    *   Elle offre des méthodes pratiques, comme `from_csv`, pour charger les données de manière standardisée.

2.  **Modules Fonctionnels (`analysis.py`, `visualization.py`)**
    *   Ces modules sont conçus pour être "purs". Ils contiennent des fonctions qui prennent un `DataFrame` en entrée et retournent un résultat (un `DataFrame` de statistiques ou une `Figure` Matplotlib).
    *   Ils ne dépendent pas de la manière dont les données sont chargées ou affichées, ce qui les rend réutilisables et faciles à tester.

3.  **Couches de Présentation (`cli.py`, `dashboard.py`)**
    *   **`cli.py`**: Utilise la bibliothèque `Typer` pour créer une interface en ligne de commande. Il analyse les arguments de l'utilisateur, charge les données dans un `DataFrame`, appelle les fonctions des modules `analysis` et `visualization`, puis formate la sortie pour le terminal (tableaux `rich`, sauvegarde de fichiers).
    *   **`dashboard.py`**: Utilise `Streamlit` pour créer une interface web interactive. Il utilise le module `data_loader` pour gérer le téléversement de fichiers, puis passe le `DataFrame` aux mêmes fonctions d'analyse et de visualisation pour afficher les résultats de manière dynamique. Le module `exporter` est utilisé pour les fonctionnalités de téléchargement.

### Diagramme Simplifié des Interactions

```
            +---------------------------+
            |   scripts/ (ex: generate) |
            +-------------+-------------+
                          |
                          v
+----------------+      +------------------+      +-------------------+
|   cli.py       |----->|                  |<-----|   dashboard.py    |
| (Typer CLI)    |      |  Bibliothèque    |      | (Streamlit App)   |
+----------------+      |                  |      +---------+---------+
       |                |   - analysis.py  |                |
       +--------------->|   - viz.py       |<---------------+ 
                        |   - core.py      |
                        |   - exporter.py  |
                        |   - data_loader.py|
                        +------------------+
```

Cette architecture découplée permet d'ajouter facilement de nouvelles fonctionnalités d'analyse ou de créer de nouvelles interfaces (par exemple, une API REST) sans modifier la logique existante.