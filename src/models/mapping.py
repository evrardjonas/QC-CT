"""
Typed mapping models for CT-QC YAML extraction.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScalarSpec:
    name: str
    config: Dict[str, Any]
    kind: str = "field"


@dataclass
class ColumnSpec:
    name: str
    config: Dict[str, Any]


@dataclass
class TableSpec:
    name: str
    config: Dict[str, Any]
    columns: Dict[str, ColumnSpec]
    db_table: Optional[str] = None
    kind: str = "table"


@dataclass
class SectionSpec:
    sheet_id: str
    sheet_name: str
    section_id: str
    db_table: Optional[str] = None
    scalars: Dict[str, ScalarSpec] = field(default_factory=dict)
    metadata: Dict[str, ScalarSpec] = field(default_factory=dict)
    named_results: Dict[str, ScalarSpec] = field(default_factory=dict)
    result_scalars: Dict[str, ScalarSpec] = field(default_factory=dict)
    tables: List[TableSpec] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SheetSpec:
    sheet_id: str
    sheet_name: str
    extract: bool = True
    required: bool = False
    is_dual_source: bool = False
    is_iterative: bool = False
    inject_columns: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, SectionSpec] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateSpec:
    template_id: str
    version: str
    description: str = ""
    schema: str = "v6"
    sheets: Dict[str, SheetSpec] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
