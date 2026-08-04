# Architecture CT-QC Orchestrator

## Vue d'ensemble

Le CT-QC Orchestrator est un pipeline d'ingestion de données qui transforme des fichiers Excel de contrôle qualité CT en formats structurés (HDF5, Parquet, TXT) avec un système de templates et sidecars.

## Architecture technique
CT-QC/
├── bin/ # Scripts exécutables
├── src/ # Code source Python
├── data/ # Données et stockage
├── templates/ # Configuration templates
├── visits/ # Gestion des visites
├── config/ # Configuration
└── docs/ # Documentation

### Composants principaux

1. **Orchestrator** (`src/core/orchestrator.py`)
   - Coordonne le flux de traitement
   - Gère les exports multiples
   - Gestion d'erreurs et audit

2. **Template System** (`src/core/selector.py`, `src/core/sidecar.py`)
   - Détection automatique des templates
   - Chargement des règles YAML
   - Héritage et fusion de configurations

3. **Extraction Engine** (`src/engine/`)
   - Extraction des données Excel
   - Normalisation et validation
   - Conversion d'unités

4. **Storage Systems** (`src/storage/`)
   - HDF5 (données opérationnelles)
   - Parquet (analytics)
   - TXT (compatibilité Access)

## Flux de données

1. **Entrée**: Fichier Excel CT-QC
2. **Template Detection**: Auto-détection ou template forcé
3. **Sidecar Loading**: Chargement des règles YAML
4. **Data Extraction**: Extraction selon le sidecar
5. **QAVisit Creation**: Création de la visite structurée
6. **Persistence**: Sauvegarde HDF5 + exports
7. **Archive**: Archivage JSON pour traçabilité

## Formats de sortie

- **HDF5**: Stockage opérationnel, recherche rapide
- **Parquet**: Analytics, partitionné par année/hôpital/système
- **TXT**: Compatibilité MS Access
- **JSON**: Archivage et débogage