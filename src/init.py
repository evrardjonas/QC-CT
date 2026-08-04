"""
CT-QC Orchestrator - Pipeline d'ingestion et d'analytics pour les contrôles de qualité CT
"""

__version__ = "2025.1.0"
__author__ = "Votre équipe CT-QC"
__description__ = "Excel → HDF5/TXT/Parquet avec templates et sidecars"

from .core.orchestrator import CTQCOrchestrator
from .core.selector import TemplateSelector
from .core.sidecar import SidecarLoader
from .core.audit import AuditSystem
from .models.qa_visit import QAVisit
from .storage.hdf5_store import HDF5Store
from .storage.parquet_export import ParquetExporter
from .storage.access_export import AccessExporter

__all__ = [
    'CTQCOrchestrator',
    'TemplateSelector', 
    'SidecarLoader',
    'AuditSystem',
    'QAVisit',
    'HDF5Store',
    'ParquetExporter',
    'AccessExporter'
]