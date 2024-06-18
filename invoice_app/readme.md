# Documentation Technique
Spirit - Invoice API

Introduction
------------
Ce code est conçu pour extraire des données à partir de fichiers JSON, les traiter et les envoyer à l'API OpenAI pour générer une sortie JSON basée sur les informations fournies. Les résultats sont ensuite enregistrés dans un fichier CSV.

Structure
-----------------
Le code est divisé en plusieurs fonctions pour faciliter la modularité et la maintenance. Voici une description détaillée de chaque fonction.

### Fonction `estimate_token_count(text)`

Cette fonction estime le nombre de jetons dans un texte donné en fonction de sa longueur. Elle suppose une longueur moyenne de jeton, espaces compris.

#### Paramètres

* `text` (str) : Le texte à évaluer.

#### Retour

* (int) : Le nombre estimé de jetons dans le texte.

### Fonction `extract_data_json(json_data)`

Cette fonction extrait et traite les données à partir d'un fichier JSON.

#### Paramètres

* `json_data` (dict) : Les données JSON à traiter.

#### Retour

* (dict) : Un dictionnaire contenant la phrase extraite et le nom du fichier.

### Fonction `process_json_files(directory_path, output_dir_path)`

Cette fonction traite les fichiers JSON d'un répertoire local un par un, appelle la fonction `process_json_file` pour chaque fichier et enregistre les résultats dans un fichier CSV.

#### Paramètres

* `directory_path` (str) : Le chemin du répertoire contenant les fichiers JSON.
* `output_dir_path` (str) : Le chemin du répertoire où enregistrer le fichier CSV de sortie.

#### Retour

* (list) : Une liste de dictionnaires contenant les résultats pour chaque fichier JSON.

### Fonction `process_json_file(json_data)`

Cette fonction traite un fichier JSON, tronque le texte si nécessaire pour respecter la limite de jetons, appelle l'API OpenAI pour générer une sortie JSON et renvoie les informations sur la facture.

#### Paramètres

* `json_data` (dict) : Les données JSON à traiter.

#### Retour

* (dict) : Un dictionnaire contenant les informations sur la facture.

Dépendances
------------
Le code dépend des bibliothèques suivantes :

* `os` : Pour les fonctionnalités liées au système d'exploitation.
* `re` : Pour les expressions régulières.
* `csv` : Pour lire et écrire des fichiers CSV.
* `json` : Pour lire et écrire des fichiers JSON.
* `glob` : Pour rechercher des fichiers correspondant à un motif donné.
* `openai` : Pour interagir avec l'API OpenAI.
* `chardet` : Pour détecter l'encodage d'un fichier.
* `tqdm` : Pour afficher une barre de progression lors du traitement des fichiers.
* `pydantic` : Pour la validation et la gestion des données.
* `dotenv` : Pour charger les variables d'environnement à partir d'un fichier .env.

Configuration
-------------

Le code nécessite un fichier .env contenant la clé d'API OpenAI :

`OPENAI_API_KEY=<votre_clé_d_api_openai>`

Utilisation
-----------

1. Assurez-vous d'avoir installé toutes les dépendances.
2. Configurez le fichier .env avec votre clé d'API OpenAI.
3. Exécutez le code en fournissant le chemin du répertoire contenant les fichiers JSON et le chemin du répertoire où enregistrer le fichier CSV de sortie.

Format des données
------------------

### Entrée

Les données d'entrée doivent être au format JSON, avec les champs suivants :

* `pages` (list) : Une liste d'objets représentant les pages du document.

Chaque objet de page doit avoir le format suivant :

* `$type` (str) : Le type de l'objet, doit être "PageContent".
* `Items` (list) : Une liste d'objets représentant les zones de texte de la page.

Chaque objet de zone de texte doit avoir le format suivant :

* `$type` (str) : Le type de l'objet, doit être "TextZone".
* `Ln` (list) : Une liste d'objets représentant les lignes de texte.

Chaque objet de ligne de texte doit avoir le format suivant :

* `Items` (list) : Une liste d'objets représentant les mots de la ligne.

Chaque objet de mot doit avoir le format suivant :

* `$type` (str) : Le type de l'objet, doit être "Word".
* `Value` (str) : La valeur du mot.

### Sortie

Les données de sortie sont au format CSV, avec les champs suivants :

* `sentence` (str) : La phrase extraite du fichier JSON.
* `file_name` (str) : Le nom du fichier JSON.
* `LLM_output` (str) : La sortie JSON générée par l'API OpenAI.

Limitations
-----------
* La limite de jetons pour l'API OpenAI est actuellement fixée à 32000 jetons. Si la taille du texte dépasse cette limite, il sera tronqué.
* Le code suppose que les fichiers JSON ont une structure spécifique. Si les données d'entrée n'ont pas la bonne structure, le code peut échouer ou produire des résultats incorrects.
