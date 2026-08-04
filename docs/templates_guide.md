# Guide des Templates CT-QC

## Structure d'un template

Un template CT-QC est composé de deux parties:

1. **Registry** (`templates/index.yml`): Métadonnées et scores
2. **Sidecar** (`templates/*.yml`): Règles d'extraction

## Schema v6 actif

Le template actif `ctqc_base` utilise maintenant le mapping v6. Les feuilles sont
identifiees par une cle logique et pointent vers la feuille Excel avec
`sheet_name`. Les donnees sont decrites par sections:

- scalaires: `{row, col, dtype}`
- tables: `header_row`, `data_start_row`, `end_row` ou `end_condition`
- colonnes: `columns.<name>.col` avec `dtype`, `unit`, `optional`, `bool_map`,
  `locale_safe`
- filtres de lignes: `skip_if_value` et `skip_col`
- resultats isoles: `named_results`
- contexte de feuille: `inject_columns`, `is_dual_source`, `is_iterative`

`inject_columns` est applique par le moteur d'extraction aux DataFrames produits
par la feuille avant l'export. Les resultats nommes sont conserves dans une table
longue `named_results` avec la feuille, la section, la cellule source et le
contexte injecte.

## Exemple de sidecar

```yaml
id: mon_template
version: "2025.1"
extends: ctqc_base  # Héritage optionnel

sheets:
  MaFeuille:
    required: true
    fields:
      mon_champ:
        name: "NOM_DEFINI_EXCEL"
        type: "string"
        normalize:
          map:
            "valeur1": "normalisé1"
            "valeur2": "normalisé2"
        validators:
          - in: ["val1", "val2", "val3"]
Types de champs supportés
string: Texte

number: Numérique

date: Date

boolean: Booléen

Système de validation
yaml
validators:
  - range: [0, 100]          # Plage numérique
  - in: ["A", "B", "C"]      # Valeurs autorisées
  - regex: "^[A-Z]{3}$"      # Pattern regex
  - required: true           # Champ obligatoire
Héritage de templates
Les templates peuvent hériter d'un template de base:

yaml
extends: ctqc_base
Les règles sont fusionnées récursivement, la configuration enfant écrase la parente.

## 📁 **FICHIERS RACINE**

### **pyproject.toml**
```toml
[project]
name = "ct-qc-orchestrator"
version = "2025.1.0"
description = "Pipeline d'ingestion et d'analytics pour les contrôles de qualité CT"
authors = [
    {name = "Votre Équipe", email = "contact@example.com"},
]
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Healthcare Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "openpyxl>=3.1.0",
    "pandas>=2.0.0",
    "pyarrow>=12.0.0",
    "tables>=3.8.0",
    "duckdb>=0.9.0",
    "polars>=0.19.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
ctqc-ingest = "bin.ctqc_ingest:main"
ctqc-analytics = "bin.ctqc_analytics:main"
ctqc-export = "bin.ctqc_export:main"

[project.urls]
Homepage = "https://github.com/votre-org/ct-qc-orchestrator"
Documentation = "https://github.com/votre-org/ct-qc-orchestrator/docs"
Repository = "https://github.com/votre-org/ct-qc-orchestrator"
Changelog = "https://github.com/votre-org/ct-qc-orchestrator/releases"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]

docs = [
    "mkdocs>=1.4.0",
    "mkdocs-material>=9.0.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["src*", "bin*"]

[tool.setuptools.package-dir]
"src" = "src"
"bin" = "bin"

[tool.black]
line-length = 100
target-version = ['py39']
