"""
Template models - Classes pour la gestion des templates
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class TemplateType(Enum):
    """Types de templates disponibles"""
    BASE = "base"
    STANDARD = "standard"
    DUAL_ENERGY = "dual_energy"
    VENDOR_SPECIFIC = "vendor_specific"
    CUSTOM = "custom"


@dataclass
class FieldDefinition:
    """Définition d'un champ dans un template"""
    
    name: str
    type: str  # string, number, date, boolean
    required: bool = False
    default: Any = None
    unit: Optional[str] = None
    normalize: Optional[Dict] = None
    validators: Optional[List[Dict]] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour YAML"""
        return {
            'name': self.name,
            'type': self.type,
            'required': self.required,
            'default': self.default,
            'unit': self.unit,
            'normalize': self.normalize,
            'validators': self.validators,
            'description': self.description
        }


@dataclass
class TableDefinition:
    """Définition d'une table dans un template"""
    
    table: str  # Nom de la table Excel
    required: bool = False
    columns: Optional[Dict[str, FieldDefinition]] = None
    derive: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour YAML"""
        columns_dict = {}
        if self.columns:
            columns_dict = {name: field.to_dict() for name, field in self.columns.items()}
        
        return {
            'table': self.table,
            'required': self.required,
            'columns': columns_dict or None,
            'derive': self.derive,
            'description': self.description
        }


@dataclass
class SheetDefinition:
    """Définition d'une feuille dans un template"""
    
    name: str
    required: bool = False
    fields: Optional[Dict[str, FieldDefinition]] = None
    tables: Optional[Dict[str, TableDefinition]] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour YAML"""
        fields_dict = {}
        if self.fields:
            fields_dict = {name: field.to_dict() for name, field in self.fields.items()}
        
        tables_dict = {}
        if self.tables:
            tables_dict = {name: table.to_dict() for name, table in self.tables.items()}
        
        return {
            'name': self.name,
            'required': self.required,
            'fields': fields_dict or None,
            'tables': tables_dict or None,
            'description': self.description
        }


@dataclass
class TemplateDefinition:
    """Définition complète d'un template"""
    
    id: str
    version: str
    type: TemplateType
    description: str
    sheets: Dict[str, SheetDefinition]
    extends: Optional[str] = None
    required_sheets: Optional[List[str]] = None
    required_tables: Optional[List[str]] = None
    required_names: Optional[List[str]] = None
    base_score: int = 0
    
    def __post_init__(self):
        if self.required_sheets is None:
            self.required_sheets = [name for name, sheet in self.sheets.items() if sheet.required]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour YAML"""
        sheets_dict = {name: sheet.to_dict() for name, sheet in self.sheets.items()}
        
        return {
            'id': self.id,
            'version': self.version,
            'type': self.type.value,
            'description': self.description,
            'extends': self.extends,
            'required_sheets': self.required_sheets,
            'required_tables': self.required_tables,
            'required_names': self.required_names,
            'base_score': self.base_score,
            'sheets': sheets_dict
        }
    
    def validate_structure(self, workbook_sheets: List[str]) -> bool:
        """Valide la structure du workbook par rapport au template"""
        if not self.required_sheets:
            return True
        
        workbook_sheet_set = set(workbook_sheets)
        return all(sheet in workbook_sheet_set for sheet in self.required_sheets)
    
    def get_missing_components(self, workbook_sheets: List[str], workbook_tables: List[str]) -> Dict[str, List[str]]:
        """Retourne les composants manquants dans le workbook"""
        missing = {
            'sheets': [],
            'tables': []
        }
        
        workbook_sheet_set = set(workbook_sheets)
        workbook_table_set = set(workbook_tables)
        
        # Vérification des feuilles requises
        if self.required_sheets:
            missing['sheets'] = [sheet for sheet in self.required_sheets if sheet not in workbook_sheet_set]
        
        # Vérification des tables requises
        if self.required_tables:
            missing['tables'] = [table for table in self.required_tables if table not in workbook_table_set]
        
        return missing