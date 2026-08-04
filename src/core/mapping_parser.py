"""
Parser/compiler for CT-QC YAML mappings.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from models.mapping import (
    ColumnSpec,
    ScalarSpec,
    SectionSpec,
    SheetSpec,
    TableSpec,
    TemplateSpec,
)


SHEET_RESERVED_KEYS = {
    "sheet_name",
    "required",
    "extract",
    "is_dual_source",
    "is_iterative",
    "inject_columns",
    "note",
    "traceability_only",
    "sections",
}

SECTION_RESERVED_KEYS = {
    "db_table",
    "note",
    "anchor_text",
    "anchor_row",
    "anchor_occurrence",
    "header_row",
    "data_start_row",
    "data_end_row",
    "end_row",
    "end_condition",
    "columns",
    "metadata",
    "named_results",
    "summary_table",
    "skip_if_value",
    "skip_col",
    "bhpa_criterion",
    "traceability_only",
}

SCALAR_RESULT_KEYS = {
    "totaal",
    "pass_fail_totaal",
    "pass_fail",
    "datum_verslag_ref",
}


class TemplateMappingParser:
    """Compiles old and v6 YAML structures into one internal model."""

    def compile(self, raw: Dict[str, Any], template_id: str = "ctqc_base") -> TemplateSpec:
        if self._is_v6(raw):
            return self._compile_v6(raw, template_id)
        return self._compile_legacy(raw, template_id)

    def _is_v6(self, raw: Dict[str, Any]) -> bool:
        return isinstance(raw.get("workbook"), dict)

    def _compile_v6(self, raw: Dict[str, Any], template_id: str) -> TemplateSpec:
        workbook = raw.get("workbook", {}) or {}
        spec = TemplateSpec(
            template_id=raw.get("id") or template_id,
            version=str(raw.get("version") or workbook.get("version") or "0.0.0"),
            description=raw.get("description") or workbook.get("description") or "",
            schema="v6",
            raw=raw,
        )

        for sheet_id, sheet_config in (raw.get("sheets") or {}).items():
            if not isinstance(sheet_config, dict):
                continue

            sheet = SheetSpec(
                sheet_id=sheet_id,
                sheet_name=sheet_config.get("sheet_name", sheet_id),
                extract=sheet_config.get("extract", True) is not False,
                required=bool(sheet_config.get("required", False)),
                is_dual_source=bool(sheet_config.get("is_dual_source", False)),
                is_iterative=bool(sheet_config.get("is_iterative", False)),
                inject_columns=dict(sheet_config.get("inject_columns") or {}),
                raw=sheet_config,
            )

            for section_id, section_config in self._iter_v6_sections(sheet_config):
                section = self._compile_v6_section(sheet, section_id, section_config)
                sheet.sections[section_id] = section

            spec.sheets[sheet_id] = sheet

        return spec

    def _iter_v6_sections(self, sheet_config: Dict[str, Any]) -> Iterable[tuple[str, Dict[str, Any]]]:
        sections = sheet_config.get("sections")
        if isinstance(sections, dict):
            for section_id, section_config in sections.items():
                if isinstance(section_config, dict):
                    yield section_id, section_config

        for key, value in sheet_config.items():
            if key in SHEET_RESERVED_KEYS or not isinstance(value, dict):
                continue
            if self._is_scalar_mapping(value):
                yield "_sheet", {key: value}
            else:
                yield key, value

    def _compile_v6_section(
        self, sheet: SheetSpec, section_id: str, section_config: Dict[str, Any]
    ) -> SectionSpec:
        section = SectionSpec(
            sheet_id=sheet.sheet_id,
            sheet_name=sheet.sheet_name,
            section_id=section_id,
            db_table=section_config.get("db_table"),
            raw=section_config,
        )

        if self._is_table_mapping(section_config):
            section.tables.append(self._compile_table(section_id, section_config, "table"))

        metadata = section_config.get("metadata")
        if isinstance(metadata, dict):
            section.metadata.update(self._compile_scalar_group(metadata, "metadata"))

        named_results = section_config.get("named_results")
        if isinstance(named_results, dict):
            section.named_results.update(self._compile_scalar_group(named_results, "named_result"))

        summary_table = section_config.get("summary_table")
        if isinstance(summary_table, dict) and self._is_table_mapping(summary_table):
            name = f"{section_id}__summary_table"
            section.tables.append(self._compile_table(name, summary_table, "summary_table"))

        for key, value in section_config.items():
            if key in SECTION_RESERVED_KEYS:
                continue
            if key in SCALAR_RESULT_KEYS:
                self._add_result_scalar(section, key, value)
            elif self._is_scalar_mapping(value) or self._is_list_mapping(value):
                section.scalars[key] = ScalarSpec(key, value, "field")
            elif self._is_table_mapping(value):
                table_name = f"{section_id}__{key}"
                section.tables.append(self._compile_table(table_name, value, "nested_table"))
            elif isinstance(value, dict):
                section.result_scalars.update(self._compile_scalar_group(value, key))

        return section

    def _compile_table(self, name: str, config: Dict[str, Any], kind: str) -> TableSpec:
        columns = {
            col_name: ColumnSpec(col_name, col_config)
            for col_name, col_config in (config.get("columns") or {}).items()
            if isinstance(col_config, dict)
        }
        return TableSpec(
            name=name,
            config=config,
            columns=columns,
            db_table=config.get("db_table"),
            kind=kind,
        )

    def _compile_scalar_group(self, group: Dict[str, Any], kind: str) -> Dict[str, ScalarSpec]:
        result = {}
        for key, value in group.items():
            if key == "note":
                continue
            if self._is_scalar_mapping(value) or self._is_list_mapping(value):
                result[key] = ScalarSpec(key, value, kind)
        return result

    def _add_result_scalar(self, section: SectionSpec, key: str, value: Any) -> None:
        if self._is_scalar_mapping(value) or self._is_list_mapping(value):
            section.result_scalars[key] = ScalarSpec(key, value, "result_scalar")
        elif isinstance(value, dict):
            section.result_scalars.update(self._compile_scalar_group(value, key))

    def _is_table_mapping(self, value: Dict[str, Any]) -> bool:
        return isinstance(value, dict) and isinstance(value.get("columns"), dict)

    def _is_scalar_mapping(self, value: Any) -> bool:
        return isinstance(value, dict) and "row" in value and "col" in value

    def _is_list_mapping(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        dtype = value.get("dtype") or value.get("type")
        return dtype in {"list_of_dict", "list_of_string"}

    def _compile_legacy(self, raw: Dict[str, Any], template_id: str) -> TemplateSpec:
        spec = TemplateSpec(
            template_id=raw.get("id") or template_id,
            version=str(raw.get("version") or "0.0.0"),
            description=raw.get("description") or "",
            schema="legacy",
            raw=raw,
        )

        for sheet_name, sheet_config in (raw.get("sheets") or {}).items():
            if not isinstance(sheet_config, dict):
                continue
            sheet = SheetSpec(
                sheet_id=sheet_name,
                sheet_name=sheet_name,
                extract=True,
                required=bool(sheet_config.get("required", False)),
                raw=sheet_config,
            )
            section = SectionSpec(
                sheet_id=sheet_name,
                sheet_name=sheet_name,
                section_id="_legacy",
                raw=sheet_config,
            )
            for field_name, field_config in (sheet_config.get("fields") or {}).items():
                if isinstance(field_config, dict):
                    section.scalars[field_name] = ScalarSpec(field_name, field_config, "field")
            for table_name, table_config in (sheet_config.get("tables") or {}).items():
                if isinstance(table_config, dict):
                    section.tables.append(self._compile_legacy_table(table_name, table_config))
            sheet.sections[section.section_id] = section
            spec.sheets[sheet.sheet_id] = sheet

        return spec

    def _compile_legacy_table(self, table_name: str, table_config: Dict[str, Any]) -> TableSpec:
        columns = {
            col_name: ColumnSpec(col_name, col_config)
            for col_name, col_config in (table_config.get("columns") or {}).items()
            if isinstance(col_config, dict)
        }
        return TableSpec(
            name=table_name,
            config=table_config,
            columns=columns,
            db_table=table_config.get("table") or table_name,
            kind="legacy_table",
        )
