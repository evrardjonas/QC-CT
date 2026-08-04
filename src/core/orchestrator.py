"""
Orchestrateur principal CT-QC - Version simplifiée
"""

import os
import concurrent.futures
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .selector import TemplateSelector
from .sidecar import SidecarLoader
from engine.extraction_engine import ExtractionEngine
from models.qa_visit import QAVisit
from storage.hdf5_store import HDF5Store
from .audit import AuditSystem
from utils.log import log_execution

logger = logging.getLogger(__name__)


class CTQCOrchestrator:
    """
    Orchestrateur principal du pipeline CT-QC - Version simplifiée
    """
    
    def __init__(self, hdf_store: HDF5Store, config: Dict):
        self.hdf_store = hdf_store
        self.config = config
        self.audit_system = AuditSystem()
        self.template_selector = TemplateSelector(config['templates']['directory'])
        self.sidecar_loader = SidecarLoader(config['templates']['directory'])
        self.extraction_engine = ExtractionEngine(config)
        
    @log_execution
    def process_file(self, excel_path: str, processing_config: Dict) -> bool:
        """
        Traite un fichier Excel unique - Version simplifiée
        """
        file_name = os.path.basename(excel_path)
        self.audit_system.log_processing_start(file_name)
        
        try:
            # ✅ SIMPLIFICATION : Template unique ctqc_base
            requested_template = processing_config.get('template', 'auto')
            template_id = (
                self.template_selector.select_from_file(excel_path, requested_template)
                if requested_template in (None, "auto")
                else requested_template
            )
            
            # 2. Chargement sidecar
            sidecar = self.sidecar_loader.load(
                template_id, 
                strict=processing_config.get('strict', False)
            )
            
            # 3. Extraction données
            extraction_result = self.extraction_engine.extract_from_path(
                excel_path, sidecar
            )
            
            # 4. Création QAVisit
            qa_visit = QAVisit.from_extraction_result(
                self.hdf_store, extraction_result, sidecar, self.audit_system
            )
            
            # 5. Persistance et exports
            if not processing_config.get('dry_run', False):
                success = self._persist_and_export(qa_visit, extraction_result, processing_config)
                if success:
                    self.audit_system.log_processing_success(
                        file_name, qa_visit.qaid, template_id
                    )
                    return True
                else:
                    self.audit_system.log_processing_error(
                        file_name, "Persistence failed"
                    )
                    return False
            else:
                self.audit_system.log_dry_run_success(file_name, template_id)
                return True
                
        except Exception as e:
            self.audit_system.log_processing_error(file_name, str(e))
            logger.error(f"Processing failed for {file_name}: {e}")
            return False
    
    @log_execution  
    def process_directory(self, directory_path: str, processing_config: Dict) -> List[Dict]:
        """
        Traite un dossier complet de fichiers Excel - Version simplifiée
        """
        excel_files = self._find_excel_files(directory_path)
        results = []
        
        workers = processing_config.get('workers', 0)
        if workers <= 1:
            # Traitement séquentiel
            for excel_file in excel_files:
                result = self._process_single_file(excel_file, processing_config)
                results.append(result)
        else:
            # Traitement parallèle
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
                future_to_file = {
                    executor.submit(self._process_single_file, excel_file, processing_config): excel_file
                    for excel_file in excel_files
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    excel_file = future_to_file[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'file': excel_file,
                            'success': False,
                            'error': str(e)
                        })
        
        # Finalisation
        self._finalize_batch_processing(results, processing_config)
        return results
    
    def _process_single_file(self, excel_path: str, processing_config: Dict) -> Dict:
        """Traite un fichier unique (pour parallélisation)"""
        try:
            success = self.process_file(excel_path, processing_config)
            return {
                'file': excel_path,
                'success': success,
                'error': None
            }
        except Exception as e:
            return {
                'file': excel_path,
                'success': False,
                'error': str(e)
            }
    
    def _persist_and_export(self, qa_visit: QAVisit, extraction_result, processing_config: Dict) -> bool:
        """Persiste et exporte les données"""
        try:
            # Persistance HDF5
            if not qa_visit.persist_to_hdf():
                return False
            
            # Exports additionnels
            exports = processing_config.get('exports', {})
            
            # Export Parquet
            if exports.get('parquet'):
                from storage.parquet_export import ParquetExporter
                exporter = ParquetExporter(exports['parquet'], self.config)
                exporter.export_visit(qa_visit, extraction_result)
            
            # Export Access
            if exports.get('access'):
                from storage.access_export import AccessExporter
                exporter = AccessExporter(exports['access'], self.config)
                exporter.export_visit(qa_visit, extraction_result)
            
            # Archive visite
            self._archive_visit(qa_visit, extraction_result)
            
            return True
            
        except Exception as e:
            logger.error(f"Persistence/export failed for QAVisit {qa_visit.qaid}: {e}")
            return False
    
    def _archive_visit(self, qa_visit: QAVisit, extraction_result):
        """Archive la visite pour traçabilité"""
        archive_dir = Path(self.config['storage']['visits_archive'])
        visit_dir = archive_dir / f"visit_{qa_visit.qaid}_{qa_visit.excel_file_name.replace('.', '_')}"
        visit_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarde métadonnées
        qa_visit.save_metadata(visit_dir / "metadata.json")
        extraction_result.save(visit_dir / "extraction_result.json")
        
        # Sauvegarde audit
        self.audit_system.save_visit_audit(visit_dir / "audit_log.json")
    
    def _find_excel_files(self, directory_path: str) -> List[str]:
        """Trouve tous les fichiers Excel dans un dossier"""
        excel_extensions = ('.xlsx', '.xlsm', '.xls')
        excel_files = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(excel_extensions):
                    excel_files.append(os.path.join(root, file))
        
        return sorted(excel_files)
    
    def _finalize_batch_processing(self, results: List[Dict], processing_config: Dict):
        """Finalise le traitement par lot"""
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        self.audit_system.log_batch_completion(success_count, total_count)
        
        # Export audit final
        if not processing_config.get('dry_run', False):
            self.audit_system.export_to_hdf(self.hdf_store)
            
            if processing_config.get('exports', {}).get('parquet'):
                self.audit_system.export_to_parquet(
                    processing_config['exports']['parquet']
                )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de traitement"""
        return self.audit_system.get_summary_metrics()
