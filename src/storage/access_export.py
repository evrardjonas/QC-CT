"""
Export Access CT-QC - CompatibilitÃ© avec MS Access
"""

import os
import pandas as pd
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AccessExporter:
    """
    Exporte les donnÃ©es en fichiers TXT formatÃ©s pour MS Access
    """
    
    def __init__(self, export_root: str, config: Dict):
        self.export_root = export_root
        self.config = config
        self.delimiter = config.get('access', {}).get('delimiter', ',')
        self.encoding = config.get('access', {}).get('encoding', 'utf-8')
        
        os.makedirs(export_root, exist_ok=True)
        
        # Mapping complet des tables vers leurs feuilles Excel
        self.table_to_sheet = {
            # buisspanning-geometrie
            'geometry_tube_voltage': 'buisspanning-geometrie',
            'geometry_irradiated_slice_thickness': 'buisspanning-geometrie',
            'geometry_table_motion': 'buisspanning-geometrie',
            'geometry_overscan': 'buisspanning-geometrie',
            
            # Beeldkwaliteit (prÃ©fixe IQ_)
            'IQ_location': 'Beeldkwaliteit',
            'IQ_date': 'Beeldkwaliteit',
            'IQ_resolution_numeric': 'Beeldkwaliteit',
            'IQ_resolution_visual': 'Beeldkwaliteit',
            'IQ_sensitometry_measurements': 'Beeldkwaliteit',
            'IQ_uniformity': 'Beeldkwaliteit',
            'IQ_uniformity_summary': 'Beeldkwaliteit',
            'IQ_HU': 'Beeldkwaliteit',
            
            # Beeldkwaliteit_Iteratief (prÃ©fixe IQ_IT_)
            'IQ_IT_date': 'Beeldkwaliteit_Iteratief',
            'IQ_IT_resolution_numeric_it': 'Beeldkwaliteit_Iteratief',
            'IQ_IT_resolution_visual_it': 'Beeldkwaliteit_Iteratief',
            'IQ_IT_sensitometry_measurements': 'Beeldkwaliteit_Iteratief',
            'IQ_IT_uniformity': 'Beeldkwaliteit_Iteratief',
            'IQ_IT_uniformity_summary': 'Beeldkwaliteit_Iteratief',
            'IQ_IT_HU': 'Beeldkwaliteit_Iteratief',
            
            # Beeldkwaliteit_DS (prÃ©fixe IQ_DS_)
            'IQ_DS_sensitometry_measurements': 'Beeldkwaliteit_DS',
            'IQ_DS_HU': 'Beeldkwaliteit_DS',
            'IQ_DS_uniformity': 'Beeldkwaliteit_DS',
            'IQ_DS_uniformity_summary': 'Beeldkwaliteit_DS',
            
            # Beeldkwaliteit_DS_Iteratief (prÃ©fixe IQ_DS_IT_)
            'IQ_DS_IT_sensitometry_measurements': 'Beeldkwaliteit_DS_Iteratief',
            'IQ_DS_IT_HU': 'Beeldkwaliteit_DS_Iteratief',
            'IQ_DS_IT_uniformity': 'Beeldkwaliteit_DS_Iteratief',
            'IQ_DS_IT_uniformity_summary': 'Beeldkwaliteit_DS_Iteratief',
            
            # Snededikte
            'sensitivity_profile_measurements': 'Snededikte',
            'slice_thickness_measurements_1': 'Snededikte',
            'slice_thickness_measurements_2': 'Snededikte',
            
            # Ruis Detectorrij
            'noise': 'Ruis Detectorrij',
            
            # CTDI 32cm
            'ctdi_32_reproducibility': 'CTDI 32cm',
            'ctdi_32_kv': 'CTDI 32cm',
            'ctdi_32_collimation': 'CTDI 32cm',
            'ctdi_32_mas_standard': 'CTDI 32cm',
            'ctdi_32_mas_iterative': 'CTDI 32cm',
            'ctdi_32_dual_source': 'CTDI 32cm',
            'ctdi_32_twin_beam': 'CTDI 32cm',
            
            # CTDI 16cm
            'ctdi_16_kv': 'CTDI 16cm',
            'ctdi_16_kv_deviation': 'CTDI 16cm',
            
            # Buisstroommodulatie
            'tcm_dikteobject': 'Buisstroommodulatie',
            
            # protocollen
            'system_protocols': 'protocollen',
            
            # Tables gÃ©nÃ©riques (pour compatibilitÃ©)
            'CTDI_Results': 'CTDI',
            'IQ_Results': 'Image_Quality',
            'Extracted_Fields': 'Metadata',
            'QAVisit': 'Metadata',
            'Extraction_Metadata': 'Metadata',
        }
    
    def export_visit(self, qa_visit, extraction_result):
        """
        Exporte une visite QA en fichiers TXT pour Access
        """
        try:
            # Export de la visite principale
            self._export_qavisit_txt(qa_visit)
            
            # Export des donnÃ©es associÃ©es
            self._export_qa_data_txt(qa_visit, extraction_result)
            
            # Export des mÃ©tadonnÃ©es
            self._export_metadata_txt(qa_visit, extraction_result)
            
            logger.info(f"Access export completed for QAVisit {getattr(qa_visit, 'qaid', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Access export failed: {e}")
            return False
    
    def _export_qavisit_txt(self, qa_visit):
        """Exporte les donnÃ©es QAVisit en TXT"""
        visit_data = {
            'ID': [getattr(qa_visit, 'qaid', None)],
            'Qampr': [getattr(qa_visit, 'qampr', None)],
            'Reference_QC': [getattr(qa_visit, 'reference_qc', None)],
            'Type': [getattr(qa_visit, 'type', None)],
            'Date_Test': [getattr(qa_visit, 'date_test', None)],
            'Hospital_ID': [getattr(qa_visit, 'hospital_id', None)],
            'System_ID': [getattr(qa_visit, 'system_id', None)],
            'System_Info_ID': [getattr(qa_visit, 'system_info_id', None)],
            'Excel_File_Name': [getattr(qa_visit, 'excel_file_name', None)],
            'QA_Member1': [getattr(qa_visit, 'qa_member1', None)],
            'QA_Member2': [getattr(qa_visit, 'qa_member2', None)],
            'Date_To_DB': [getattr(qa_visit, 'date_to_db', None)],
            'Template_ID': [getattr(qa_visit, 'template_id', None)],
            'Workbook_Hash': [getattr(qa_visit, 'workbook_hash', None)],
        }
        
        df = pd.DataFrame(visit_data)
        file_path = os.path.join(self.export_root, "QAVisit.txt")
        self._save_dataframe_for_access(df, file_path, sheet_name='Metadata')

    def _add_visit_traceability(self, df: pd.DataFrame, qa_visit) -> pd.DataFrame:
        """Add visit traceability columns to an exported result table."""
        export_df = df.copy()
        traceability = {
            'QAID': getattr(qa_visit, 'qaid', None),
            'Qampr': getattr(qa_visit, 'qampr', None),
            'Reference_QC': getattr(qa_visit, 'reference_qc', None),
            'Source_File': getattr(qa_visit, 'excel_file_name', None),
        }
        for column, value in traceability.items():
            if column not in export_df.columns:
                export_df[column] = value
        return export_df
    
    def _export_qa_data_txt(self, qa_visit, extraction_result):
        """Exporte les donnÃ©es des tests QA en TXT"""
        try:
            # âœ… GARDER LES EXPORTS EXISTANTS QUI FONCTIONNENT
            # DonnÃ©es CTDI
            ctdi_data = self._extract_ctdi_for_access(extraction_result)
            if ctdi_data is not None and not ctdi_data.empty:
                ctdi_data = self._add_visit_traceability(ctdi_data, qa_visit)
                ctdi_path = os.path.join(self.export_root, "CTDI_Results.txt")
                self._save_dataframe_for_access(ctdi_data, ctdi_path, sheet_name='CTDI')
            
            # DonnÃ©es IQ
            iq_data = self._extract_iq_for_access(extraction_result)
            if iq_data is not None and not iq_data.empty:
                iq_data = self._add_visit_traceability(iq_data, qa_visit)
                iq_path = os.path.join(self.export_root, "IQ_Results.txt")
                self._save_dataframe_for_access(iq_data, iq_path, sheet_name='Image_Quality')
            
            # ðŸ”§ EXPORT DE TOUTES LES TABLES DU YAML ORGANISÃ‰ES PAR FEUILLE
            # 1. Tables de buisspanning-geometrie
            self._export_geometry_tube_voltage_txt(qa_visit, extraction_result)
            self._export_geometry_irradiated_slice_thickness_txt(qa_visit, extraction_result)
            self._export_geometry_table_motion_txt(qa_visit, extraction_result)
            self._export_geometry_overscan_txt(qa_visit, extraction_result)
            
            # 2. Tables de Beeldkwaliteit (prÃ©fixe IQ_)
            self._export_IQ_location_txt(qa_visit, extraction_result)
            self._export_IQ_date_txt(qa_visit, extraction_result)
            self._export_IQ_resolution_numeric_txt(qa_visit, extraction_result)
            self._export_IQ_resolution_visual_txt(qa_visit, extraction_result)
            self._export_IQ_sensitometry_measurements_txt(qa_visit, extraction_result)
            self._export_IQ_uniformity_txt(qa_visit, extraction_result)
            self._export_IQ_uniformity_summary_txt(qa_visit, extraction_result)
            self._export_IQ_HU_txt(qa_visit, extraction_result)
            
            # 3. Tables de Beeldkwaliteit_Iteratief (prÃ©fixe IQ_IT_)
            self._export_IQ_IT_date_txt(qa_visit, extraction_result)
            self._export_IQ_IT_resolution_numeric_it_txt(qa_visit, extraction_result)
            self._export_IQ_IT_resolution_visual_it_txt(qa_visit, extraction_result)
            self._export_IQ_IT_sensitometry_measurements_txt(qa_visit, extraction_result)
            self._export_IQ_IT_uniformity_txt(qa_visit, extraction_result)
            self._export_IQ_IT_uniformity_summary_txt(qa_visit, extraction_result)
            self._export_IQ_IT_HU_txt(qa_visit, extraction_result)
            
            # 4. Tables de Beeldkwaliteit_DS (prÃ©fixe IQ_DS_)
            self._export_IQ_DS_sensitometry_measurements_txt(qa_visit, extraction_result)
            self._export_IQ_DS_HU_txt(qa_visit, extraction_result)
            self._export_IQ_DS_uniformity_txt(qa_visit, extraction_result)
            self._export_IQ_DS_uniformity_summary_txt(qa_visit, extraction_result)
            
            # 5. Tables de Beeldkwaliteit_DS_Iteratief (prÃ©fixe IQ_DS_IT_)
            self._export_IQ_DS_IT_sensitometry_measurements_txt(qa_visit, extraction_result)
            self._export_IQ_DS_IT_HU_txt(qa_visit, extraction_result)
            self._export_IQ_DS_IT_uniformity_txt(qa_visit, extraction_result)
            self._export_IQ_DS_IT_uniformity_summary_txt(qa_visit, extraction_result)
            
            # 6. Tables de Snededikte
            self._export_sensitivity_profile_measurements_txt(qa_visit, extraction_result)
            self._export_slice_thickness_measurements_1_txt(qa_visit, extraction_result)
            self._export_slice_thickness_measurements_2_txt(qa_visit, extraction_result)
            
            # 7. Tables de Ruis Detectorrij
            self._export_noise_txt(qa_visit, extraction_result)
            
            # 8. Tables de CTDI 32cm
            self._export_ctdi_32_reproducibility_txt(qa_visit, extraction_result)
            self._export_ctdi_32_kv_txt(qa_visit, extraction_result)
            self._export_ctdi_32_collimation_txt(qa_visit, extraction_result)
            self._export_ctdi_32_mas_standard_txt(qa_visit, extraction_result)
            self._export_ctdi_32_mas_iterative_txt(qa_visit, extraction_result)
            self._export_ctdi_32_dual_source_txt(qa_visit, extraction_result)
            self._export_ctdi_32_twin_beam_txt(qa_visit, extraction_result)
            
            # 9. Tables de CTDI 16cm
            self._export_ctdi_16_kv_txt(qa_visit, extraction_result)
            self._export_ctdi_16_kv_deviation_txt(qa_visit, extraction_result)
            
            # 10. Tables de Buisstroommodulatie
            self._export_tcm_dikteobject_txt(qa_visit, extraction_result)
            
            # 11. Tables de protocollen
            self._export_system_protocols_txt(qa_visit, extraction_result)
            self._export_generic_tables_txt(qa_visit, extraction_result)
            self._export_scalar_db_tables_txt(qa_visit, extraction_result)
            self._export_auxiliary_results_txt(qa_visit, extraction_result)
            
            # Export des champs extraits
            if extraction_result.fields:
                fields_df = pd.DataFrame([extraction_result.fields])
                fields_df = self._standardize_column_names(fields_df)
                fields_df = self._add_visit_traceability(fields_df, qa_visit)
                fields_path = os.path.join(self.export_root, "Extracted_Fields.txt")
                self._save_dataframe_for_access(fields_df, fields_path, sheet_name='Metadata')
                
        except Exception as e:
            logger.warning(f"Could not export QA data for Access: {e}")

    def _export_generic_tables_txt(self, qa_visit, extraction_result):
        """Exports v6 db_table outputs that are not covered by legacy hardcoded names."""
        try:
            for table_name, df in extraction_result.tables.items():
                if table_name in self.table_to_sheet or df is None or df.empty:
                    continue
                export_df = self._standardize_column_names(df.copy())
                export_df = self._add_visit_traceability(export_df, qa_visit)
                file_path = os.path.join(self.export_root, f"{self._safe_table_name(table_name)}.txt")
                self._save_dataframe_for_access(export_df, file_path, sheet_name='Extracted_Tables')
        except Exception as e:
            logger.warning(f"Could not export generic v6 tables: {e}")

    def _export_scalar_db_tables_txt(self, qa_visit, extraction_result):
        """Exports scalar-only db_table sections as single-row v6 table files."""
        try:
            scalar_df = getattr(extraction_result, 'scalar_records', pd.DataFrame())
            if scalar_df is None or scalar_df.empty or 'db_table' not in scalar_df.columns:
                return

            scalar_df = scalar_df[
                scalar_df['db_table'].notna()
                & (scalar_df['db_table'].astype(str).str.strip() != '')
                & scalar_df.get('kind', pd.Series(index=scalar_df.index, dtype=object)).isin(['field', 'result_scalar'])
            ].copy()
            if scalar_df.empty:
                return

            table_backed_db_tables = {
                table_name
                for table_name, df in extraction_result.tables.items()
                if df is not None and not df.empty
            }

            for db_table, table_records in scalar_df.groupby('db_table', dropna=True):
                if db_table in table_backed_db_tables:
                    continue

                rows = []
                group_columns = ['sheet_id', 'sheet_name', 'section_id']
                for group_values, section_records in table_records.groupby(group_columns, dropna=False):
                    row = {
                        'source_sheet_id': group_values[0],
                        'source_sheet_name': group_values[1],
                        'source_section_id': group_values[2],
                    }

                    for _, scalar in section_records.iterrows():
                        name = scalar.get('name')
                        if pd.notna(name) and str(name).strip():
                            row[str(name)] = scalar.get('value')

                    for context_col in self._scalar_context_columns(section_records):
                        values = section_records[context_col].dropna().unique()
                        if len(values) > 0:
                            row[context_col] = values[0]

                    rows.append(row)

                if not rows:
                    continue

                export_df = pd.DataFrame(rows)
                export_df = self._standardize_column_names(export_df)
                export_df = self._add_visit_traceability(export_df, qa_visit)
                file_path = os.path.join(self.export_root, f"{self._safe_table_name(db_table)}.txt")
                self._save_dataframe_for_access(export_df, file_path, sheet_name='Extracted_Tables')
        except Exception as e:
            logger.warning(f"Could not export scalar-only v6 db_tables: {e}")

    def _scalar_context_columns(self, section_records: pd.DataFrame) -> List[str]:
        reserved = {
            'sheet_id',
            'sheet_name',
            'section_id',
            'db_table',
            'name',
            'kind',
            'dtype',
            'row',
            'col',
            'value',
        }
        return [col for col in section_records.columns if col not in reserved]

    def _export_auxiliary_results_txt(self, qa_visit, extraction_result):
        """Exports scalar records and named results for Access imports."""
        try:
            auxiliary = {
                'Scalar_Records': getattr(extraction_result, 'scalar_records', pd.DataFrame()),
                'Named_Results': getattr(extraction_result, 'named_results', pd.DataFrame()),
            }
            for name, df in auxiliary.items():
                if df is None or df.empty:
                    continue
                export_df = self._standardize_column_names(df.copy())
                export_df = self._add_visit_traceability(export_df, qa_visit)
                file_path = os.path.join(self.export_root, f"{name}.txt")
                self._save_dataframe_for_access(export_df, file_path, sheet_name='Metadata')
        except Exception as e:
            logger.warning(f"Could not export auxiliary v6 results: {e}")
    
    # ðŸ”§ FONCTIONS D'EXPORT SPÃ‰CIFIQUES POUR CHAQUE TABLE
    
    # 1. Fonctions pour buisspanning-geometrie
    def _export_geometry_tube_voltage_txt(self, qa_visit, extraction_result):
        """Exporte les donnÃ©es Tube Voltage"""
        try:
            if 'geometry_tube_voltage' in extraction_result.tables:
                df = extraction_result.tables['geometry_tube_voltage'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Tube_Voltage.txt")
                    sheet_name = self.table_to_sheet.get('geometry_tube_voltage', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Tube Voltage data: {e}")

    def _export_geometry_irradiated_slice_thickness_txt(self, qa_visit, extraction_result):
        """Exporte les donnÃ©es Geometry Irradiated Slice Thickness"""
        try:
            if 'geometry_irradiated_slice_thickness' in extraction_result.tables:
                df = extraction_result.tables['geometry_irradiated_slice_thickness'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Geometry_Irradiated_Slice_Thickness.txt")
                    sheet_name = self.table_to_sheet.get('geometry_irradiated_slice_thickness', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Geometry Irradiated Slice Thickness data: {e}")

    def _export_geometry_table_motion_txt(self, qa_visit, extraction_result):
        """Exporte les donnÃ©es Geometry Table Motion"""
        try:
            if 'geometry_table_motion' in extraction_result.tables:
                df = extraction_result.tables['geometry_table_motion'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Geometry_Table_Motion.txt")
                    sheet_name = self.table_to_sheet.get('geometry_table_motion', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Geometry Table Motion data: {e}")

    def _export_geometry_overscan_txt(self, qa_visit, extraction_result):
        """Exporte les donnÃ©es Geometry Overscan"""
        try:
            if 'geometry_overscan' in extraction_result.tables:
                df = extraction_result.tables['geometry_overscan'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Geometry_Overscan.txt")
                    sheet_name = self.table_to_sheet.get('geometry_overscan', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Geometry Overscan data: {e}")
    
    # 2. Fonctions pour Beeldkwaliteit (prÃ©fixe IQ_)
    def _export_IQ_location_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_location' in extraction_result.tables:
                df = extraction_result.tables['IQ_location'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Location.txt")
                    sheet_name = self.table_to_sheet.get('IQ_location', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Location data: {e}")

    def _export_IQ_date_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_date' in extraction_result.tables:
                df = extraction_result.tables['IQ_date'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Date.txt")
                    sheet_name = self.table_to_sheet.get('IQ_date', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Date data: {e}")

    def _export_IQ_resolution_numeric_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_resolution_numeric' in extraction_result.tables:
                df = extraction_result.tables['IQ_resolution_numeric'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Resolution_Numeric.txt")
                    sheet_name = self.table_to_sheet.get('IQ_resolution_numeric', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Resolution Numeric data: {e}")

    def _export_IQ_resolution_visual_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_resolution_visual' in extraction_result.tables:
                df = extraction_result.tables['IQ_resolution_visual'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Resolution_Visual.txt")
                    sheet_name = self.table_to_sheet.get('IQ_resolution_visual', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Resolution Visual data: {e}")

    def _export_IQ_sensitometry_measurements_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_sensitometry_measurements' in extraction_result.tables:
                df = extraction_result.tables['IQ_sensitometry_measurements'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Sensitometry_Measurements.txt")
                    sheet_name = self.table_to_sheet.get('IQ_sensitometry_measurements', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Sensitometry Measurements data: {e}")

    def _export_IQ_uniformity_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_uniformity' in extraction_result.tables:
                df = extraction_result.tables['IQ_uniformity'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity.txt")
                    sheet_name = self.table_to_sheet.get('IQ_uniformity', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity data: {e}")

    def _export_IQ_uniformity_summary_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_uniformity_summary' in extraction_result.tables:
                df = extraction_result.tables['IQ_uniformity_summary'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_Summary.txt")
                    sheet_name = self.table_to_sheet.get('IQ_uniformity_summary', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity Summary data: {e}")

    def _export_IQ_HU_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_HU' in extraction_result.tables:
                df = extraction_result.tables['IQ_HU'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "HU.txt")
                    sheet_name = self.table_to_sheet.get('IQ_HU', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export HU data: {e}")
    
    # 3. Fonctions pour Beeldkwaliteit_Iteratief (prÃ©fixe IQ_IT_)
    def _export_IQ_IT_date_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_date' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_date'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Date_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_date', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Date IT data: {e}")

    def _export_IQ_IT_resolution_numeric_it_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_resolution_numeric_it' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_resolution_numeric_it'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Resolution_Numeric_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_resolution_numeric_it', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Resolution Numeric IT data: {e}")

    def _export_IQ_IT_resolution_visual_it_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_resolution_visual_it' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_resolution_visual_it'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Resolution_Visual_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_resolution_visual_it', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Resolution Visual IT data: {e}")

    def _export_IQ_IT_sensitometry_measurements_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_sensitometry_measurements' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_sensitometry_measurements'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Sensitometry_Measurements_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_sensitometry_measurements', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Sensitometry Measurements IT data: {e}")

    def _export_IQ_IT_uniformity_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_uniformity' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_uniformity'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_uniformity', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity IT data: {e}")

    def _export_IQ_IT_uniformity_summary_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_uniformity_summary' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_uniformity_summary'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_Summary_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_uniformity_summary', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity Summary IT data: {e}")

    def _export_IQ_IT_HU_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_IT_HU' in extraction_result.tables:
                df = extraction_result.tables['IQ_IT_HU'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "HU_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_IT_HU', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export HU IT data: {e}")
    
    # 4. Fonctions pour Beeldkwaliteit_DS (prÃ©fixe IQ_DS_)
    def _export_IQ_DS_sensitometry_measurements_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_sensitometry_measurements' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_sensitometry_measurements'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Sensitometry_Measurements_DS.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_sensitometry_measurements', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Sensitometry Measurements DS data: {e}")

    def _export_IQ_DS_HU_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_HU' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_HU'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "HU_DS.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_HU', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export HU DS data: {e}")

    def _export_IQ_DS_uniformity_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_uniformity' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_uniformity'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_DS.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_uniformity', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity DS data: {e}")

    def _export_IQ_DS_uniformity_summary_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_uniformity_summary' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_uniformity_summary'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_Summary_DS.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_uniformity_summary', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity Summary DS data: {e}")
    
    # 5. Fonctions pour Beeldkwaliteit_DS_Iteratief (prÃ©fixe IQ_DS_IT_)
    def _export_IQ_DS_IT_sensitometry_measurements_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_IT_sensitometry_measurements' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_IT_sensitometry_measurements'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Sensitometry_Measurements_DS_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_IT_sensitometry_measurements', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Sensitometry Measurements DS IT data: {e}")

    def _export_IQ_DS_IT_HU_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_IT_HU' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_IT_HU'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "HU_DS_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_IT_HU', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export HU DS IT data: {e}")

    def _export_IQ_DS_IT_uniformity_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_IT_uniformity' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_IT_uniformity'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_DS_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_IT_uniformity', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity DS IT data: {e}")

    def _export_IQ_DS_IT_uniformity_summary_txt(self, qa_visit, extraction_result):
        try:
            if 'IQ_DS_IT_uniformity_summary' in extraction_result.tables:
                df = extraction_result.tables['IQ_DS_IT_uniformity_summary'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Uniformity_Summary_DS_IT.txt")
                    sheet_name = self.table_to_sheet.get('IQ_DS_IT_uniformity_summary', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Uniformity Summary DS IT data: {e}")
    
    # 6. Fonctions pour Snededikte
    def _export_sensitivity_profile_measurements_txt(self, qa_visit, extraction_result):
        try:
            if 'sensitivity_profile_measurements' in extraction_result.tables:
                df = extraction_result.tables['sensitivity_profile_measurements'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Sensitivity_Profile_Measurements.txt")
                    sheet_name = self.table_to_sheet.get('sensitivity_profile_measurements', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Sensitivity Profile Measurements data: {e}")

    def _export_slice_thickness_measurements_1_txt(self, qa_visit, extraction_result):
        try:
            if 'slice_thickness_measurements_1' in extraction_result.tables:
                df = extraction_result.tables['slice_thickness_measurements_1'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Slice_Thickness_Measurements_1.txt")
                    sheet_name = self.table_to_sheet.get('slice_thickness_measurements_1', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Slice Thickness Measurements 1 data: {e}")

    def _export_slice_thickness_measurements_2_txt(self, qa_visit, extraction_result):
        try:
            if 'slice_thickness_measurements_2' in extraction_result.tables:
                df = extraction_result.tables['slice_thickness_measurements_2'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Slice_Thickness_Measurements_2.txt")
                    sheet_name = self.table_to_sheet.get('slice_thickness_measurements_2', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Slice Thickness Measurements 2 data: {e}")
    
    # 7. Fonctions pour Ruis Detectorrij
    def _export_noise_txt(self, qa_visit, extraction_result):
        try:
            if 'noise' in extraction_result.tables:
                df = extraction_result.tables['noise'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "Noise.txt")
                    sheet_name = self.table_to_sheet.get('noise', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export Noise data: {e}")
    
    # 8. Fonctions pour CTDI 32cm
    def _export_ctdi_32_reproducibility_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_reproducibility' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_reproducibility'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_Reproducibility.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_reproducibility', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 Reproducibility data: {e}")

    def _export_ctdi_32_kv_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_kv' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_kv'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_KV.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_kv', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 KV data: {e}")

    def _export_ctdi_32_collimation_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_collimation' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_collimation'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_Collimation.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_collimation', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 Collimation data: {e}")

    def _export_ctdi_32_mas_standard_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_mas_standard' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_mas_standard'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_MAS_Standard.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_mas_standard', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 MAS Standard data: {e}")

    def _export_ctdi_32_mas_iterative_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_mas_iterative' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_mas_iterative'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_MAS_Iterative.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_mas_iterative', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 MAS Iterative data: {e}")

    def _export_ctdi_32_dual_source_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_dual_source' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_dual_source'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_Dual_Source.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_dual_source', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 Dual Source data: {e}")

    def _export_ctdi_32_twin_beam_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_32_twin_beam' in extraction_result.tables:
                df = extraction_result.tables['ctdi_32_twin_beam'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_32_Twin_Beam.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_32_twin_beam', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 32 Twin Beam data: {e}")
    
    # 9. Fonctions pour CTDI 16cm
    def _export_ctdi_16_kv_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_16_kv' in extraction_result.tables:
                df = extraction_result.tables['ctdi_16_kv'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_16_KV.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_16_kv', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 16 KV data: {e}")

    def _export_ctdi_16_kv_deviation_txt(self, qa_visit, extraction_result):
        try:
            if 'ctdi_16_kv_deviation' in extraction_result.tables:
                df = extraction_result.tables['ctdi_16_kv_deviation'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "CTDI_16_KV_Deviation.txt")
                    sheet_name = self.table_to_sheet.get('ctdi_16_kv_deviation', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export CTDI 16 KV Deviation data: {e}")
    
    # 10. Fonctions pour Buisstroommodulatie
    def _export_tcm_dikteobject_txt(self, qa_visit, extraction_result):
        try:
            if 'tcm_dikteobject' in extraction_result.tables:
                df = extraction_result.tables['tcm_dikteobject'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "TCM_Dikteobject.txt")
                    sheet_name = self.table_to_sheet.get('tcm_dikteobject', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export TCM Dikteobject data: {e}")
    
    # 11. Fonctions pour protocollen
    def _export_system_protocols_txt(self, qa_visit, extraction_result):
        try:
            if 'system_protocols' in extraction_result.tables:
                df = extraction_result.tables['system_protocols'].copy()
                if not df.empty:
                    df = self._standardize_column_names(df)
                    df = self._add_visit_traceability(df, qa_visit)
                    file_path = os.path.join(self.export_root, "System_Protocols.txt")
                    sheet_name = self.table_to_sheet.get('system_protocols', 'Unknown')
                    self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
        except Exception as e:
            logger.warning(f"Could not export System Protocols data: {e}")
    
    # âœ… MÃ‰THODES UTILITAIRES
    def _extract_ctdi_for_access(self, extraction_result):
        """Extrait les donnÃ©es CTDI formatÃ©es pour Access"""
        ctdi_tables = ['CTDI_Results', 'CTDI_Doses', 'ctdi_results', 'ctdi_doses']
        for table_name in ctdi_tables:
            if table_name in extraction_result.tables:
                df = extraction_result.tables[table_name].copy()
                return self._standardize_column_names(df)
        
        return None
    
    def _extract_iq_for_access(self, extraction_result):
        """Extrait les donnÃ©es IQ formatÃ©es pour Access"""
        iq_tables = ['IQ_Results', 'Image_Quality', 'iq_results', 'image_quality']
        for table_name in iq_tables:
            if table_name in extraction_result.tables:
                df = extraction_result.tables[table_name].copy()
                return self._standardize_column_names(df)
        
        return None
    
    def _standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardise les noms de colonnes pour Access"""
        df_standardized = df.copy()
        
        # Remplacement des caractÃ¨res problÃ©matiques
        df_standardized.columns = [
            str(col).replace(' ', '_')
              .replace('-', '_')
              .replace('(', '')
              .replace(')', '')
              .replace('.', '_')
              .replace('/', '_')
            for col in df_standardized.columns
        ]
        
        return df_standardized

    def _safe_table_name(self, table_name: str) -> str:
        return (
            str(table_name)
            .replace('/', '__')
            .replace('\\', '__')
            .replace(' ', '_')
            .replace(':', '_')
        )
    
    def _save_dataframe_for_access(self, df: pd.DataFrame, file_path: str, sheet_name: str = None):
        """
        Sauvegarde un DataFrame en format TXT compatible Access
        avec organisation par feuille Excel
        """
        try:
            # Si un nom de feuille est spÃ©cifiÃ©, crÃ©er un sous-dossier
            if sheet_name:
                # Nettoyer le nom du dossier
                safe_sheet_name = sheet_name.replace(' ', '_').replace('-', '_').replace('/', '_')
                sheet_dir = os.path.join(self.export_root, safe_sheet_name)
                os.makedirs(sheet_dir, exist_ok=True)
                
                # Mettre le fichier dans le dossier de la feuille
                filename = os.path.basename(file_path)
                file_path = os.path.join(sheet_dir, filename)
            else:
                # Sinon, utiliser le chemin original
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Configuration pour l'import Access
            df.to_csv(
                file_path,
                sep=self.delimiter,
                index=False,
                quoting=1,  # QUOTE_ALL
                encoding=self.encoding
            )
            
            logger.debug(f"Access TXT file created: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save Access file {file_path}: {e}")
            raise
    
    def _export_metadata_txt(self, qa_visit, extraction_result):
        """Exporte les mÃ©tadonnÃ©es en TXT"""
        metadata_data = {
            'QAID': [getattr(qa_visit, 'qaid', None)],
            'Template_ID': [getattr(qa_visit, 'template_id', None)],
            'Sidecar_Version': [getattr(qa_visit, 'sidecar_version', None)],
            'Workbook_Hash': [getattr(qa_visit, 'workbook_hash', None)],
            'Extraction_Method': [getattr(qa_visit, 'extraction_method', 'template')],
            'Processing_Timestamp': [getattr(qa_visit, 'processing_timestamp', None)],
            'Total_Sheets': [extraction_result.audit.get('stats', {}).get('total_sheets', 0)],
            'Extracted_Fields': [extraction_result.audit.get('stats', {}).get('extracted_fields', 0)],
            'Extracted_Tables': [extraction_result.audit.get('stats', {}).get('extracted_tables', 0)],
        }
        
        df = pd.DataFrame(metadata_data)
        file_path = os.path.join(self.export_root, "Extraction_Metadata.txt")
        self._save_dataframe_for_access(df, file_path, sheet_name='Metadata')
    
    def export_from_hdf(self, hdf_path: str, tables: List[str] = None):
        """
        Exporte directement depuis HDF5 vers TXT pour Access
        """
        try:
            with pd.HDFStore(hdf_path, 'r') as store:
                if tables is None:
                    tables = [key[1:] for key in store.keys()]
                
                for table in tables:
                    if table in store:
                        df = store[table]
                        file_path = os.path.join(self.export_root, f"{table}.txt")
                        sheet_name = self.table_to_sheet.get(table, 'Unknown')
                        self._save_dataframe_for_access(df, file_path, sheet_name=sheet_name)
                        logger.info(f"Exported {table} to Access format")
                    
        except Exception as e:
            logger.error(f"Failed to export from HDF5: {e}")

