# API Reference CT-QC Orchestrator

Référence des classes et fonctions principales du CT-QC Orchestrator.

## Core Components

### CTQCOrchestrator

Classe principale orchestrant le pipeline de traitement.

```python
from src.core.orchestrator import CTQCOrchestrator

orchestrator = CTQCOrchestrator(hdf_store, config)
Méthodes principales :

process_file(excel_path, processing_config) -> bool
Traite un fichier Excel unique

process_directory(directory_path, processing_config) -> List[Dict]
Traite un dossier de fichiers Excel

get_processing_stats() -> Dict
Retourne les statistiques de traitement

Exemple :

python
success = orchestrator.process_file(
    "data/raw/excel/QC300_0724_01014CT-CT13.xlsm",
    {
        'template': 'auto',
        'strict': True,
        'dry_run': False,
        'exports': {
            'parquet': 'data/analytics/parquet/',
            'access': 'data/export/access/'
        }
    }
)
TemplateSelector
Gère la détection et sélection des templates.

python
from src.core.selector import TemplateSelector

selector = TemplateSelector(templates_dir="templates")
Méthodes principales :

select_from_file(excel_path, forced=None) -> str
Sélectionne le template pour un fichier Excel

get_available_templates() -> Dict
Retourne la liste des templates disponibles

validate_template_compatibility(excel_path, template_id) -> bool
Valide la compatibilité d'un fichier avec un template

SidecarLoader
Charge et valide les fichiers sidecar YAML.

python
from src.core.sidecar import SidecarLoader

loader = SidecarLoader(templates_dir="templates")
Méthodes principales :

load(template_id, strict=False) -> Dict
Charge un sidecar pour un template donné

get_sidecar_info(template_id) -> Dict
Retourne les informations d'un sidecar

clear_cache()
Vide le cache des sidecars

AuditSystem
Système complet d'audit et traçabilité.

python
from src.core.audit import AuditSystem

audit = AuditSystem()
Méthodes principales :

log_event(level, component, event_type, message, details, file_name, qaid)
Enregistre un événement d'audit

export_to_hdf(hdf_store)
Exporte l'audit vers HDF5

export_to_parquet(output_path)
Exporte l'audit vers Parquet

get_summary_metrics() -> Dict
Retourne les métriques résumées

Engine Components
ExtractionEngine
Moteur d'extraction des données Excel.

python
from src.engine.extraction_engine import ExtractionEngine

engine = ExtractionEngine(config)
Méthodes principales :

extract_from_path(excel_path, sidecar) -> ExtractionResult
Extrait les données d'un fichier Excel

extract_from_workbook(wb, sidecar, source_path) -> ExtractionResult
Extrait les données d'un workbook OpenPyXL

ExtractionResult
Résultat de l'extraction de données.

python
from src.engine.extraction_engine import ExtractionResult

result = ExtractionResult(fields, tables, audit, meta)
Propriétés :

fields: Dict[str, Any] - Champs extraits

tables: Dict[str, pd.DataFrame] - Tables extraites

audit: Dict[str, Any] - Informations d'audit

meta: Dict[str, Any] - Métadonnées

Méthodes :

to_dict() -> Dict - Convertit en dictionnaire

save(file_path) - Sauvegarde en JSON

get_summary() -> Dict - Retourne un résumé

Storage Components
HDF5Store
Store HDF5 pour données opérationnelles.

python
from src.storage.hdf5_store import HDF5Store

hdf_store = HDF5Store("data/operational/CTdb.hdf")
Méthodes principales :

get(table_name) -> pd.DataFrame
Récupère une table

put(table_name, data, **kwargs)
Sauvegarde une table

load_reference_data(static_data_dir)
Charge les données de référence

save_all_tables_to_txt(output_dir)
Sauvegarde toutes les tables en TXT

ParquetExporter
Export des données en format Parquet analytics.

python
from src.storage.parquet_export import ParquetExporter

exporter = ParquetExporter("data/analytics/parquet/", config)
Méthodes principales :

export_visit(qa_visit, extraction_result) -> bool
Exporte une visite QA en Parquet

AccessExporter
Export des données en format TXT pour Access.

python
from src.storage.access_export import AccessExporter

exporter = AccessExporter("data/export/access/", config)
Méthodes principales :

export_visit(qa_visit, extraction_result) -> bool
Exporte une visite QA en TXT

export_from_hdf(hdf_path, tables)
Exporte directement depuis HDF5

Models
QAVisit
Représente une visite QA complète.

python
from src.models.qa_visit import QAVisit

visit = QAVisit.from_extraction_result(hdf_store, extraction_result, sidecar, audit_system)
Propriétés principales :

qaid: int - Identifiant unique

qampr: str - Numéro QAMPR

template_id: str - Template utilisé

hospital_id: int - ID hôpital

system_id: int - ID système

Méthodes :

persist_to_hdf() -> bool - Persiste dans HDF5

to_dict() -> Dict - Convertit en dictionnaire

save_metadata(file_path) - Sauvegarde les métadonnées

Utils
Configuration
python
from src.utils.config import load_config, get_config_value

config = load_config("config/default.yml")
template = get_config_value(config, "processing.default_template")
Logging
python
from src.utils.log import setup_logging, PerformanceLogger

setup_logging(config['logging'])

with PerformanceLogger("Operation"):
    # Code à mesurer
    pass
Configuration Processing
Structure de la configuration de traitement :

python
processing_config = {
    'template': 'auto',           # ou ID template spécifique
    'strict': False,              # validation stricte
    'dry_run': False,             # simulation sans écriture
    'workers': 0,                 # parallélisme (0 = séquentiel)
    'batch_size': 10,             # taille des lots
    'exports': {
        'parquet': 'chemin/parquet/',    # export Parquet
        'access': 'chemin/access/'       # export Access TXT
    }
}