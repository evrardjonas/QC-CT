"""
ExtractionResult model - Résultat de l'extraction
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import pandas as pd
import json


@dataclass
class ExtractionResult:
    """Résultat de l'extraction de données"""
    
    fields: Dict[str, Any]
    tables: Dict[str, pd.DataFrame]
    audit: Dict[str, Any]
    meta: Dict[str, Any]
    scalar_records: pd.DataFrame = field(default_factory=pd.DataFrame)
    named_results: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'fields': self.fields,
            'tables': {k: v.to_dict('records') for k, v in self.tables.items()},
            'scalar_records': self.scalar_records.to_dict('records') if not self.scalar_records.empty else [],
            'named_results': self.named_results.to_dict('records') if not self.named_results.empty else [],
            'audit': self.audit,
            'meta': self.meta
        }
    
    def save(self, file_path: str):
        """Sauvegarde le résultat en JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            raise Exception(f"Failed to save extraction result: {e}")
    
    @classmethod
    def load(cls, file_path: str) -> 'ExtractionResult':
        """Charge depuis un fichier JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruction des DataFrames
            tables = {}
            for table_name, records in data['tables'].items():
                tables[table_name] = pd.DataFrame(records)
            
            return cls(
                fields=data['fields'],
                tables=tables,
                audit=data['audit'],
                meta=data['meta'],
                scalar_records=pd.DataFrame(data.get('scalar_records', [])),
                named_results=pd.DataFrame(data.get('named_results', []))
            )
        except Exception as e:
            raise Exception(f"Failed to load extraction result: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'extraction"""
        return {
            'fields_count': len(self.fields),
            'tables_count': len(self.tables),
            'scalar_records_count': len(self.scalar_records),
            'named_results_count': len(self.named_results),
            'total_rows': sum(len(df) for df in self.tables.values()),
            'template_id': self.meta.get('template_id'),
            'workbook_hash': self.meta.get('workbook_hash'),
            'sheets_processed': len(self.audit.get('sheets_processed', []))
        }
