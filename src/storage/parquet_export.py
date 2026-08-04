"""
Export Parquet CT-QC - Données analytics
"""

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds
from datetime import datetime
from typing import Dict, Any, Optional, List

import logging

logger = logging.getLogger(__name__)


class ParquetExporter:
    """
    Exporte les données CT-QC en format Parquet partitionné
    """
    
    def __init__(self, export_root: str, config: Dict):
        self.export_root = export_root
        self.config = config
        self.compression = config.get('parquet', {}).get('compression', 'ZSTD')
        self.row_group_size = config.get('parquet', {}).get('row_group_size', 100000)
        
        os.makedirs(export_root, exist_ok=True)
    
    def export_visit(self, qa_visit, extraction_result):
        """
        Exporte une visite QA complète en Parquet
        """
        try:
            # Métadonnées pour le partitionnement
            year = self._extract_year(qa_visit)
            hospital_id = getattr(qa_visit, 'hospital_id', 'unknown')
            system_id = getattr(qa_visit, 'system_id', 'unknown')
            
            # Structure de partitionnement
            partition_path = os.path.join(
                self.export_root,
                f"year={year}",
                f"hospital={hospital_id}", 
                f"system={system_id}"
            )
            os.makedirs(partition_path, exist_ok=True)
            
            # Export des différents types de données
            self._export_visit_metadata(qa_visit, partition_path)
            self._export_qa_results(qa_visit, extraction_result, partition_path)
            self._export_audit_data(extraction_result, partition_path)
            
            logger.info(f"Parquet export completed for QAVisit {getattr(qa_visit, 'qaid', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Parquet export failed: {e}")
            return False
    
    def _extract_year(self, qa_visit) -> str:
        """Extrait l'année de la visite"""
        date_test = getattr(qa_visit, 'date_test', None)
        if date_test:
            if isinstance(date_test, str):
                try:
                    # Tentative d'extraction depuis différents formats
                    if '-' in date_test:
                        return date_test.split('-')[0]
                    elif '/' in date_test:
                        return date_test.split('/')[-1]
                except:
                    pass
            elif hasattr(date_test, 'year'):
                return str(date_test.year)
        
        # Fallback à l'année de traitement
        processing_ts = getattr(qa_visit, 'processing_timestamp', None)
        if processing_ts:
            try:
                return processing_ts[:4]
            except:
                pass
        
        # Fallback à l'année courante
        return str(datetime.now().year)
    
    def _export_visit_metadata(self, qa_visit, partition_path: str):
        """Exporte les métadonnées de la visite"""
        metadata_data = {
            'qaid': [getattr(qa_visit, 'qaid', None)],
            'qampr': [getattr(qa_visit, 'qampr', None)],
            'reference_qc': [getattr(qa_visit, 'reference_qc', None)],
            'type': [getattr(qa_visit, 'type', None)],
            'date_test': [getattr(qa_visit, 'date_test', None)],
            'hospital_id': [getattr(qa_visit, 'hospital_id', None)],
            'system_id': [getattr(qa_visit, 'system_id', None)],
            'system_info_id': [getattr(qa_visit, 'system_info_id', None)],
            'excel_file_name': [getattr(qa_visit, 'excel_file_name', None)],
            'source_file': [getattr(qa_visit, 'excel_file_name', None)],
            'template_id': [getattr(qa_visit, 'template_id', None)],
            'sidecar_version': [getattr(qa_visit, 'sidecar_version', None)],
            'workbook_hash': [getattr(qa_visit, 'workbook_hash', None)],
            'qa_member1': [getattr(qa_visit, 'qa_member1', None)],
            'qa_member2': [getattr(qa_visit, 'qa_member2', None)],
            'processing_timestamp': [getattr(qa_visit, 'processing_timestamp', None)],
            'extraction_method': [getattr(qa_visit, 'extraction_method', 'template')],
        }
        
        df = pd.DataFrame(metadata_data)
        df = self._optimize_dataframe_types(df)
        
        file_path = os.path.join(partition_path, "visit_metadata.parquet")
        df.to_parquet(
            file_path,
            engine='pyarrow',
            compression=self.compression,
            index=False
        )
    
    def _export_qa_results(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les résultats des tests QA"""
        try:
            # ✅ GARDER LES EXPORTS EXISTANTS QUI FONCTIONNENT
            # Données CTDI
            ctdi_data = self._extract_ctdi_data(extraction_result)
            if ctdi_data is not None and not ctdi_data.empty:
                ctdi_data = self._optimize_dataframe_types(ctdi_data)
                ctdi_path = os.path.join(partition_path, "ctdi_results.parquet")
                ctdi_data.to_parquet(
                    ctdi_path,
                    engine='pyarrow', 
                    compression=self.compression,
                    index=False
                )
            
            # Données IQ
            iq_data = self._extract_iq_data(extraction_result)
            if iq_data is not None and not iq_data.empty:
                iq_data = self._optimize_dataframe_types(iq_data)
                iq_path = os.path.join(partition_path, "iq_results.parquet")
                iq_data.to_parquet(
                    iq_path,
                    engine='pyarrow',
                    compression=self.compression, 
                    index=False
                )
            
            # 🔧 AJOUTS NOUVEAUX - Exporter les autres tables
            self._export_tube_voltage_parquet(qa_visit, extraction_result, partition_path)
            self._export_slice_thickness_parquet(qa_visit, extraction_result, partition_path)
            self._export_tcm_parquet(qa_visit, extraction_result, partition_path)
            self._export_protocols_parquet(qa_visit, extraction_result, partition_path)
            self._export_geometry_parquet(qa_visit, extraction_result, partition_path)
            self._export_noise_parquet(qa_visit, extraction_result, partition_path)  # Nouveau : Noise
            self._export_all_extracted_tables(qa_visit, extraction_result, partition_path)
            self._export_auxiliary_results(extraction_result, partition_path)
            
            # Export des champs extraits
            if extraction_result.fields:
                fields_df = pd.DataFrame([extraction_result.fields])
                fields_df = self._optimize_dataframe_types(fields_df)
                fields_path = os.path.join(partition_path, "extracted_fields.parquet")
                fields_df.to_parquet(fields_path, engine='pyarrow', compression=self.compression, index=False)
                
        except Exception as e:
            logger.warning(f"Could not export QA results: {e}")

    def _export_all_extracted_tables(self, qa_visit, extraction_result, partition_path: str):
        """Exports every extracted table, including v6 db_table keys."""
        try:
            tables_dir = os.path.join(partition_path, "tables")
            os.makedirs(tables_dir, exist_ok=True)
            for table_name, df in extraction_result.tables.items():
                if df is None or df.empty:
                    continue
                export_df = df.copy()
                export_df["qaid"] = getattr(qa_visit, "qaid", None)
                export_df = self._optimize_dataframe_types(export_df)
                file_name = f"{self._safe_table_name(table_name)}.parquet"
                export_df.to_parquet(
                    os.path.join(tables_dir, file_name),
                    engine="pyarrow",
                    compression=self.compression,
                    index=False,
                )
        except Exception as e:
            logger.warning(f"Could not export generic extracted tables: {e}")

    def _export_auxiliary_results(self, extraction_result, partition_path: str):
        """Exports scalar records and named results from v6 mappings."""
        try:
            auxiliary = {
                "scalar_records": getattr(extraction_result, "scalar_records", pd.DataFrame()),
                "named_results": getattr(extraction_result, "named_results", pd.DataFrame()),
            }
            for name, df in auxiliary.items():
                if df is None or df.empty:
                    continue
                export_df = self._optimize_dataframe_types(df.copy())
                export_df.to_parquet(
                    os.path.join(partition_path, f"{name}.parquet"),
                    engine="pyarrow",
                    compression=self.compression,
                    index=False,
                )
        except Exception as e:
            logger.warning(f"Could not export auxiliary results: {e}")

    def _safe_table_name(self, table_name: str) -> str:
        return (
            str(table_name)
            .replace("/", "__")
            .replace("\\", "__")
            .replace(" ", "_")
            .replace(":", "_")
        )

    # 🔧 NOUVELLES FONCTIONS SPÉCIFIQUES
    def _export_tube_voltage_parquet(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les données Tube Voltage en Parquet"""
        try:
            if 'tube_voltage_series' in extraction_result.tables:
                df = extraction_result.tables['tube_voltage_series'].copy()
                if not df.empty:
                    df = self._optimize_dataframe_types(df)
                    file_path = os.path.join(partition_path, "tube_voltage.parquet")
                    df.to_parquet(file_path, engine='pyarrow', compression=self.compression, index=False)
        except Exception as e:
            logger.warning(f"Could not export Tube Voltage data: {e}")

    def _export_slice_thickness_parquet(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les données Slice Thickness en Parquet"""
        try:
            tables_to_export = ['sensitivity_profile', 'slice_thickness']
            for table_name in tables_to_export:
                if table_name in extraction_result.tables:
                    df = extraction_result.tables[table_name].copy()
                    if not df.empty:
                        df = self._optimize_dataframe_types(df)
                        file_path = os.path.join(partition_path, f"slice_thickness_{table_name}.parquet")
                        df.to_parquet(file_path, engine='pyarrow', compression=self.compression, index=False)
        except Exception as e:
            logger.warning(f"Could not export Slice Thickness data: {e}")

    def _export_tcm_parquet(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les données TCM en Parquet"""
        try:
            if 'tcm_verification' in extraction_result.tables:
                df = extraction_result.tables['tcm_verification'].copy()
                if not df.empty:
                    df = self._optimize_dataframe_types(df)
                    file_path = os.path.join(partition_path, "tcm.parquet")
                    df.to_parquet(file_path, engine='pyarrow', compression=self.compression, index=False)
        except Exception as e:
            logger.warning(f"Could not export TCM data: {e}")

    def _export_protocols_parquet(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les données Protocols en Parquet"""
        try:
            if 'protocols' in extraction_result.tables:
                df = extraction_result.tables['protocols'].copy()
                if not df.empty:
                    df = self._optimize_dataframe_types(df)
                    file_path = os.path.join(partition_path, "protocols.parquet")
                    df.to_parquet(file_path, engine='pyarrow', compression=self.compression, index=False)
        except Exception as e:
            logger.warning(f"Could not export Protocols data: {e}")

    def _export_geometry_parquet(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les données Geometry en Parquet"""
        try:
            geometry_tables = [table for table in extraction_result.tables.keys() 
                              if 'geometry' in table.lower()]
            for table_name in geometry_tables:
                df = extraction_result.tables[table_name].copy()
                if not df.empty:
                    df = self._optimize_dataframe_types(df)
                    file_path = os.path.join(partition_path, f"geometry_{table_name}.parquet")
                    df.to_parquet(file_path, engine='pyarrow', compression=self.compression, index=False)
        except Exception as e:
            logger.warning(f"Could not export Geometry data: {e}")

    def _export_noise_parquet(self, qa_visit, extraction_result, partition_path: str):
        """Exporte les données Noise en Parquet"""
        try:
            # Recherche des tables liées au bruit
            noise_tables = [table for table in extraction_result.tables.keys() 
                           if 'noise' in table.lower()]
            
            for table_name in noise_tables:
                df = extraction_result.tables[table_name].copy()
                if not df.empty:
                    df = self._optimize_dataframe_types(df)
                    file_path = os.path.join(partition_path, f"noise_{table_name}.parquet")
                    df.to_parquet(file_path, engine='pyarrow', compression=self.compression, index=False)
                    
            # Recherche dans les champs pour les données noise
            noise_fields = {k: v for k, v in extraction_result.fields.items() 
                          if 'noise' in k.lower()}
            if noise_fields:
                noise_df = pd.DataFrame([noise_fields])
                noise_df = self._optimize_dataframe_types(noise_df)
                noise_path = os.path.join(partition_path, "noise_fields.parquet")
                noise_df.to_parquet(noise_path, engine='pyarrow', compression=self.compression, index=False)
                
        except Exception as e:
            logger.warning(f"Could not export Noise data: {e}")

    # ✅ CONSERVER LES MÉTHODES EXISTANTES
    def _extract_ctdi_data(self, extraction_result):
        """Extrait les données CTDI"""
        # Recherche dans les tables extraites
        ctdi_tables = ['CTDI_Results', 'CTDI_Doses', 'ctdi_results', 'ctdi_doses']
        for table_name in ctdi_tables:
            if table_name in extraction_result.tables:
                return extraction_result.tables[table_name]
        
        # Recherche dans les champs structurés
        ctdi_fields = {k: v for k, v in extraction_result.fields.items() 
                      if 'ctdi' in k.lower() or 'dose' in k.lower()}
        if ctdi_fields:
            return pd.DataFrame([ctdi_fields])
        
        return None
    
    def _extract_iq_data(self, extraction_result):
        """Extrait les données Image Quality"""
        # Recherche dans les tables extraites
        iq_tables = ['IQ_Results', 'Image_Quality', 'iq_results', 'image_quality']
        for table_name in iq_tables:
            if table_name in extraction_result.tables:
                return extraction_result.tables[table_name]
        
        # Recherche dans les champs structurés
        iq_fields = {k: v for k, v in extraction_result.fields.items() 
                    if 'iq' in k.lower() or 'image' in k.lower() or 'quality' in k.lower()}
        if iq_fields:
            return pd.DataFrame([iq_fields])
        
        return None
    
    def _export_audit_data(self, extraction_result, partition_path: str):
        """Exporte les données d'audit d'extraction"""
        try:
            audit_data = []
            
            # Audit des feuilles
            for sheet_audit in extraction_result.audit.get('sheets_processed', []):
                audit_data.append({
                    'component': 'ExtractionEngine',
                    'event_type': 'SheetProcessed',
                    'sheet': sheet_audit.get('sheet'),
                    'fields_extracted': sheet_audit.get('fields_extracted', 0),
                    'tables_extracted': sheet_audit.get('tables_extracted', 0),
                    'errors': len(sheet_audit.get('errors', [])),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Statistiques globales
            stats = extraction_result.audit.get('stats', {})
            audit_data.append({
                'component': 'ExtractionEngine',
                'event_type': 'ExtractionSummary',
                'total_sheets': stats.get('total_sheets', 0),
                'processed_sheets': stats.get('processed_sheets', 0),
                'extracted_fields': stats.get('extracted_fields', 0),
                'extracted_tables': stats.get('extracted_tables', 0),
                'timestamp': datetime.now().isoformat()
            })
            
            if audit_data:
                df = pd.DataFrame(audit_data)
                df = self._optimize_dataframe_types(df)
                
                audit_path = os.path.join(partition_path, "extraction_audit.parquet")
                df.to_parquet(
                    audit_path,
                    engine='pyarrow',
                    compression=self.compression,
                    index=False
                )
                
        except Exception as e:
            logger.warning(f"Could not export audit data: {e}")
    
    def _optimize_dataframe_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimise les types de données pour Parquet"""
        df_optimized = df.copy()
        
        for col in df_optimized.columns:
            # Conversion des numériques
            if df_optimized[col].dtype == 'object':
                try:
                    df_optimized[col] = pd.to_numeric(df_optimized[col], errors='ignore')
                except:
                    pass
            
            # Conversion des dates
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    df_optimized[col] = pd.to_datetime(df_optimized[col], errors='ignore')
                except:
                    pass
            
            # Conversion en category pour les colonnes à faible cardinalité
            if df_optimized[col].dtype == 'object':
                unique_ratio = df_optimized[col].nunique() / len(df_optimized)
                if unique_ratio < 0.5:  # Moins de 50% de valeurs uniques
                    df_optimized[col] = df_optimized[col].astype('category')
        
        return df_optimized


class ParquetAnalytics:
    """
    Outils analytics pour données Parquet
    """
    
    def __init__(self, parquet_path: str, config: Dict):
        self.parquet_path = parquet_path
        self.config = config
    
    def get_global_stats(self, group_by_hospital: bool = False, group_by_system: bool = False):
        """Retourne les statistiques globales"""
        import pyarrow.dataset as ds
        
        try:
            dataset = ds.dataset(self.parquet_path, format="parquet")
            stats = {}
            
            # Comptage des visites
            visits_df = dataset.to_table(columns=['qaid']).to_pandas()
            stats['total_visits'] = visits_df['qaid'].nunique()
            
            # Statistiques par hôpital
            if group_by_hospital and 'hospital_id' in dataset.schema.names:
                hospital_df = dataset.to_table(columns=['hospital_id']).to_pandas()
                stats['hospitals_count'] = hospital_df['hospital_id'].nunique()
                stats['visits_by_hospital'] = hospital_df['hospital_id'].value_counts().to_dict()
            
            # Statistiques par système
            if group_by_system and 'system_id' in dataset.schema.names:
                system_df = dataset.to_table(columns=['system_id']).to_pandas()
                stats['systems_count'] = system_df['system_id'].nunique()
                stats['visits_by_system'] = system_df['system_id'].value_counts().to_dict()
            
            return stats
            
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return {}
    
    def export_data(self, format: str, output_file: str, filters: List[str] = None):
        """Exporte les données dans différents formats"""
        import pyarrow.dataset as ds
        
        try:
            dataset = ds.dataset(self.parquet_path, format="parquet")
            df = dataset.to_table().to_pandas()
            
            # Application des filtres
            if filters:
                for filter_str in filters:
                    if '=' in filter_str:
                        col, value = filter_str.split('=')
                        df = df[df[col] == value]
            
            if format == "csv":
                df.to_csv(output_file, index=False)
            elif format == "excel":
                df.to_excel(output_file, index=False)
            elif format == "json":
                df.to_json(output_file, orient='records', indent=2)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
    
    def generate_dashboard(self, output_dir: str):
        """Génère un dashboard analytics"""
        try:
            # Implémentation basique - à étendre
            stats = self.get_global_stats(group_by_hospital=True, group_by_system=True)
            
            dashboard_content = f"""
            CT-QC Analytics Dashboard
            ========================
            Generated: {datetime.now().isoformat()}
            
            Summary:
            - Total Visits: {stats.get('total_visits', 0)}
            - Hospitals: {stats.get('hospitals_count', 0)}
            - Systems: {stats.get('systems_count', 0)}
            """
            
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "dashboard.txt"), 'w') as f:
                f.write(dashboard_content)
                
        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
