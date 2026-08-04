"""
Store HDF5 CT-QC - Compatible avec vos données existantes
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class HDF5Store:
    """
    Store HDF5 étendu pour l'intégration avec vos données existantes
    """
    
    def __init__(self, hdf5_path: str, mode: str = 'a'):
        self.hdf5_path = hdf5_path
        self.mode = mode
        self.store = pd.HDFStore(hdf5_path, mode=mode)
        
    def __contains__(self, item):
        return item in self.store
    
    def get(self, table_name: str) -> pd.DataFrame:
        """Récupère une table"""
        try:
            return self.store[table_name]
        except KeyError:
            return pd.DataFrame()
    
    def put(self, table_name: str, data: pd.DataFrame, format: str = 'table', **kwargs):
        """Sauvegarde une table"""
        try:
            self.store.put(table_name, data, format=format, **kwargs)
            logger.debug(f"Table {table_name} saved ({len(data)} rows)")
        except Exception as e:
            logger.error(f"Failed to save table {table_name}: {e}")
            raise
    
    def add_record(self, table_name: str, record: List):
        """Ajoute un enregistrement (compatibilité ancien code)"""
        try:
            df = self.get(table_name)
            if df.empty:
                logger.error(f"Cannot add record to empty table: {table_name}")
                return
            
            new_record = pd.DataFrame([record], columns=df.columns)
            updated_df = pd.concat([df, new_record], ignore_index=True)
            self.put(table_name, updated_df)
            
        except Exception as e:
            logger.error(f"Failed to add record to {table_name}: {e}")
    
    def add_new_table(self, table_name: str, columns: List[str]):
        """Crée une nouvelle table (compatibilité ancien code)"""
        if table_name in self.store:
            logger.warning(f"Table {table_name} already exists")
            return
        
        df = pd.DataFrame(columns=columns)
        self.put(table_name, df)
        logger.info(f"New table created: {table_name}")
    
    def select(self, table_name: str, condition: str) -> pd.DataFrame:
        """Exécute une requête (compatibilité ancien code)"""
        try:
            return self.store.select(table_name, where=condition)
        except Exception as e:
            logger.error(f"Query failed on {table_name} with {condition}: {e}")
            return pd.DataFrame()
    
    def load_reference_data(self, static_data_dir: str):
        """Charge les données de référence depuis les fichiers TXT"""
        logger.info(f"Loading reference data from: {static_data_dir}")
        
        if not os.path.exists(static_data_dir):
            logger.warning(f"Static data directory not found: {static_data_dir}")
            return
        
        for txt_file in os.listdir(static_data_dir):
            if txt_file.endswith('.txt'):
                table_name = txt_file.replace('.txt', '')
                file_path = os.path.join(static_data_dir, txt_file)
                self._load_static_table(file_path, table_name)
    
    def _load_static_table(self, file_path: str, table_name: str):
        """Charge une table statique dans HDF5"""
        try:
            df = pd.read_csv(file_path)
            
            # Nettoyage des données
            df = self._clean_dataframe(df)
            
            if table_name in self.store:
                # Mise à jour incrémentale - évite les doublons
                existing_df = self.store[table_name]
                
                if 'ID' in df.columns and 'ID' in existing_df.columns:
                    # Fusion basée sur l'ID
                    new_ids = set(df['ID']) - set(existing_df['ID'])
                    df_to_add = df[df['ID'].isin(new_ids)]
                    
                    if not df_to_add.empty:
                        updated_df = pd.concat([existing_df, df_to_add], ignore_index=True)
                        self.put(table_name, updated_df)
                        logger.info(f"Updated table {table_name}: +{len(df_to_add)} rows")
                    else:
                        logger.debug(f"No new rows to add to {table_name}")
                else:
                    # Pas d'ID - remplacement complet
                    self.put(table_name, df)
                    logger.info(f"Replaced table {table_name}: {len(df)} rows")
            else:
                # Nouvelle table
                self.put(table_name, df)
                logger.info(f"Loaded new table {table_name}: {len(df)} rows")
                
        except Exception as e:
            logger.error(f"Failed to load static table {table_name}: {e}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie le DataFrame selon vos règles existantes"""
        df_clean = df.copy()
        
        # Conversion des types numériques
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                # Essai de conversion numérique
                try:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
                except:
                    pass
        
        # Gestion des dates
        date_columns = [col for col in df_clean.columns if 'date' in col.lower() or 'time' in col.lower()]
        for col in date_columns:
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='ignore')
            except:
                pass
        
        return df_clean
    
    def save_all_tables_to_txt(self, output_dir: str):
        """Sauvegarde toutes les tables en TXT (compatibilité ancien code)"""
        os.makedirs(output_dir, exist_ok=True)
        
        for key in self.store.keys():
            table_name = key[1:]  # Remove leading '/'
            try:
                df = self.get(table_name)
                # Remplacement des valeurs spéciales
                df = df.replace(-123456789, None)  # Votre none_number
                file_path = os.path.join(output_dir, f"{table_name}.txt")
                df.to_csv(file_path, index=False)
                logger.debug(f"Table {table_name} exported to TXT")
            except Exception as e:
                logger.error(f"Failed to export {table_name} to TXT: {e}")
    
    def get_table_info(self) -> Dict[str, Dict]:
        """Retourne des informations sur toutes les tables"""
        info = {}
        for key in self.store.keys():
            table_name = key[1:]
            df = self.get(table_name)
            info[table_name] = {
                'rows': len(df),
                'columns': list(df.columns),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'dtypes': dict(df.dtypes)
            }
        return info
    
    def optimize_storage(self):
        """Optimise le stockage HDF5"""
        try:
            # Réduction de la taille des données
            for key in self.store.keys():
                table_name = key[1:]
                df = self.get(table_name)
                
                # Optimisation des types
                for col in df.columns:
                    if df[col].dtype == 'object':
                        # Conversion en category si peu de valeurs uniques
                        if df[col].nunique() / len(df) < 0.5:
                            df[col] = df[col].astype('category')
                
                self.put(table_name, df)
            
            logger.info("HDF5 storage optimized")
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")
    
    def close(self):
        """Ferme le store HDF5"""
        try:
            self.store.close()
            logger.info("HDF5 store closed")
        except Exception as e:
            logger.error(f"Error closing HDF5 store: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()