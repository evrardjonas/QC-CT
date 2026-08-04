# CT-QC Orchestrator

Pipeline d'ingestion et d'analytics pour les contrôles de qualité CT (Excel → HDF5/TXT/Parquet).

## 🚀 Fonctionnalités

- **Ingestion automatique** des fichiers Excel CT-QC
- **Détection de templates** avec système de scoring
- **Sidecars YAML** pour la configuration des règles
- **Export multiple** : HDF5, Parquet, TXT (Access)
- **Audit complet** avec traçabilité
- **Archivage structuré** des visites

## 📦 Installation

```bash
# Installation en mode développement
pip install -e .

# Ou installation des dépendances seulement
pip install -r requirements.txt