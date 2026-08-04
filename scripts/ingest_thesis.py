#!/usr/bin/env python3
"""
Simplified thesis ingestion entry point for CT-QC Excel workbooks.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
import warnings
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from engine.extraction_engine import ExtractionEngine  # noqa: E402
from utils.config import load_config  # noqa: E402


REPORT_COLUMNS = [
    "source_file",
    "status",
    "QAID",
    "QAMPR",
    "hospital_id",
    "system_id",
    "n_fields",
    "n_tables",
    "n_named_results",
    "access_export_ok",
    "parquet_export_ok",
    "error_message",
]


VISIT_COLUMNS = [
    "QAID",
    "QAMPR",
    "source_file",
    "hospital_id",
    "system_id",
    "extraction_status",
    "n_fields",
    "n_tables",
    "n_named_results",
]


TRACE_COLUMNS = ["QAID", "QAMPR", "source_file", "hospital_id", "system_id"]
INTEGER_EXPORT_COLUMNS = {
    "QAID",
    "hospital_id",
    "system_id",
    "n_fields",
    "n_tables",
    "n_named_results",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest thesis CT-QC Excel files with one fixed YAML sidecar."
    )
    parser.add_argument("input_dir", help="Directory containing thesis .xlsm files")
    parser.add_argument("--sidecar", required=True, help="Fixed YAML sidecar path")
    parser.add_argument(
        "--to-access",
        required=True,
        dest="to_access",
        help="Access/TXT export root",
    )
    parser.add_argument(
        "--to-parquet",
        required=True,
        dest="to_parquet",
        help="Parquet export root",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_fixed_sidecar(sidecar_path: Path) -> Dict[str, Any]:
    with sidecar_path.open("r", encoding="utf-8") as handle:
        sidecar = yaml.safe_load(handle) or {}
    if not isinstance(sidecar, dict):
        raise ValueError(f"Sidecar must be a YAML mapping: {sidecar_path}")
    return sidecar


def find_excel_files(input_dir: Path) -> List[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*.xlsm")
        if path.is_file() and not path.name.startswith("~$")
    )


def first_present(fields: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = fields.get(key)
        if value is not None and value != "":
            return value
    return None


def normalize_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return None
    return int(numeric)


def normalize_qampr(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, float):
        if pd.isna(value):
            return None
        if value.is_integer():
            return str(int(value))
        return str(value).strip()

    if isinstance(value, int):
        return str(value)

    text = str(value).strip()
    if not text:
        return None

    numeric = pd.to_numeric(text, errors="coerce")
    if pd.notna(numeric):
        numeric_float = float(numeric)
        if numeric_float.is_integer():
            return str(int(numeric_float))
        return str(numeric_float)

    match = re.search(r"(\d+)\s*CT\b", text, flags=re.IGNORECASE)
    if match:
        return str(int(match.group(1)))

    return None


def derive_qampr(fields: Dict[str, Any], source_file: Path) -> Optional[str]:
    reference_qc = first_present(fields, ["reference_QC", "qa_visit.reference_QC"])
    qampr = normalize_qampr(reference_qc)
    if qampr is not None:
        return qampr
    return normalize_qampr(source_file.name)


def parse_hospital_id(source_file: Path, fields: Dict[str, Any]) -> Optional[int]:
    match = re.search(r"\bQC0*(\d+)_", source_file.name, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return normalize_int(first_present(fields, ["hospital_id", "Hospital_ID", "centrum_nummer"]))


def parse_system_id(source_file: Path, fields: Dict[str, Any]) -> Optional[int]:
    field_value = first_present(
        fields,
        [
            "system_id",
            "System_ID",
            "scanner.system_id",
            "system_nr",
            "system_number",
        ],
    )
    parsed = normalize_int(field_value)
    if parsed is not None:
        return parsed

    match = re.search(
        r"_\d{3,}CT[-_ ]*[A-Za-z]*?(\d+)\s*(?:\.[^.]+)?$",
        source_file.name,
        flags=re.IGNORECASE,
    )
    if match:
        return int(match.group(1))
    return None


def named_result_count(value: Any) -> int:
    if isinstance(value, pd.DataFrame):
        return len(value)
    return 0


def add_visit_traceability(df: pd.DataFrame, visit: Dict[str, Any]) -> pd.DataFrame:
    traced = df.copy()
    traced.columns = make_unique_columns([str(column) for column in traced.columns])
    for column in TRACE_COLUMNS:
        traced[column] = visit.get(column)
    return traced


def cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


def sanitize_column_name(column: Any) -> str:
    text = unicodedata.normalize("NFKD", str(column)).encode("ascii", "ignore").decode()
    text = re.sub(r"[^0-9A-Za-z_]+", "_", text.strip())
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = "column"
    if text[0].isdigit():
        text = f"c_{text}"
    return text


def make_unique_columns(columns: Iterable[Any]) -> List[str]:
    counts: Dict[str, int] = defaultdict(int)
    unique: List[str] = []
    for column in columns:
        base = str(column)
        counts[base] += 1
        unique.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return unique


def sanitize_columns(columns: Iterable[Any]) -> List[str]:
    counts: Dict[str, int] = defaultdict(int)
    sanitized: List[str] = []
    for column in columns:
        base = sanitize_column_name(column)
        counts[base] += 1
        sanitized.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return sanitized


def prepare_dataframe_for_export(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared.columns = sanitize_columns(prepared.columns)

    for column in prepared.columns:
        prepared[column] = prepared[column].map(cell_to_export_value)
        if column in INTEGER_EXPORT_COLUMNS:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce").astype("Int64")
            continue
        if prepared[column].dtype == "object":
            prepared[column] = prepared[column].map(
                lambda value: None if pd.isna(value) else str(value)
            )

    return prepared


def safe_table_stem(table_name: str, used: Dict[str, str]) -> str:
    stem = sanitize_column_name(table_name.replace("/", "_").replace("\\", "_"))
    existing = used.get(stem)
    if existing is None or existing == table_name:
        used[stem] = table_name
        return stem

    suffix = 2
    candidate = f"{stem}_{suffix}"
    while candidate in used and used[candidate] != table_name:
        suffix += 1
        candidate = f"{stem}_{suffix}"
    used[candidate] = table_name
    return candidate


def concat_frames(frames: List[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated.*",
            category=FutureWarning,
        )
        return pd.concat(frames, ignore_index=True, sort=False)


def append_error(row: Dict[str, Any], message: str) -> None:
    existing = str(row.get("error_message") or "").strip()
    row["error_message"] = f"{existing}; {message}" if existing else message


def export_access(
    tables: Dict[str, List[pd.DataFrame]],
    visits: List[Dict[str, Any]],
    output_root: Path,
) -> Tuple[Set[str], Dict[str, str]]:
    failed_sources: Set[str] = set()
    errors: Dict[str, str] = {}
    table_dir = output_root / "Extracted_Tables"
    metadata_dir = output_root / "Metadata"
    table_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    used_names: Dict[str, str] = {}
    for table_name, frames in tables.items():
        sources = {
            str(source)
            for frame in frames
            for source in frame.get("source_file", pd.Series(dtype=str)).dropna().unique()
        }
        try:
            df = prepare_dataframe_for_export(concat_frames(frames))
            table_path = table_dir / f"{safe_table_stem(table_name, used_names)}.txt"
            table_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(
                table_path,
                index=False,
                encoding="utf-8",
                sep=",",
                quoting=csv.QUOTE_ALL,
            )
        except Exception as exc:
            message = f"Access export failed for table {table_name}: {exc}"
            failed_sources.update(sources)
            errors[table_name] = message

    try:
        metadata = prepare_dataframe_for_export(pd.DataFrame(visits, columns=VISIT_COLUMNS))
        metadata.to_csv(
            metadata_dir / "QAVisit.txt",
            index=False,
            encoding="utf-8",
            sep=",",
            quoting=csv.QUOTE_ALL,
        )
    except Exception as exc:
        message = f"Access export failed for QAVisit metadata: {exc}"
        failed_sources.update(str(visit["source_file"]) for visit in visits)
        errors["QAVisit"] = message

    return failed_sources, errors


def export_parquet(
    tables: Dict[str, List[pd.DataFrame]],
    visits: List[Dict[str, Any]],
    output_root: Path,
) -> Tuple[Set[str], Dict[str, str]]:
    failed_sources: Set[str] = set()
    errors: Dict[str, str] = {}
    table_dir = output_root / "tables"
    metadata_dir = output_root / "metadata"
    table_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    used_names: Dict[str, str] = {}
    for table_name, frames in tables.items():
        sources = {
            str(source)
            for frame in frames
            for source in frame.get("source_file", pd.Series(dtype=str)).dropna().unique()
        }
        try:
            df = prepare_dataframe_for_export(concat_frames(frames))
            parquet_path = table_dir / f"{safe_table_stem(table_name, used_names)}.parquet"
            parquet_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(parquet_path, engine="pyarrow", index=False)
        except Exception as exc:
            message = f"Parquet export failed for table {table_name}: {exc}"
            failed_sources.update(sources)
            errors[table_name] = message

    try:
        metadata = prepare_dataframe_for_export(pd.DataFrame(visits, columns=VISIT_COLUMNS))
        metadata_path = metadata_dir / "QAVisit.parquet"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata.to_parquet(metadata_path, engine="pyarrow", index=False)
    except Exception as exc:
        message = f"Parquet export failed for QAVisit metadata: {exc}"
        failed_sources.update(str(visit["source_file"]) for visit in visits)
        errors["QAVisit"] = message

    return failed_sources, errors


def build_visit(
    qaid: int,
    source_file: Path,
    fields: Dict[str, Any],
    extraction_status: str,
    n_fields: int,
    n_tables: int,
    n_named_results: int,
) -> Dict[str, Any]:
    return {
        "QAID": qaid,
        "QAMPR": derive_qampr(fields, source_file),
        "source_file": display_path(source_file),
        "hospital_id": parse_hospital_id(source_file, fields),
        "system_id": parse_system_id(source_file, fields),
        "extraction_status": extraction_status,
        "n_fields": n_fields,
        "n_tables": n_tables,
        "n_named_results": n_named_results,
    }


def report_row_from_visit(visit: Dict[str, Any], status: str, error_message: str = "") -> Dict[str, Any]:
    return {
        "source_file": visit["source_file"],
        "status": status,
        "QAID": visit["QAID"],
        "QAMPR": visit["QAMPR"],
        "hospital_id": visit["hospital_id"],
        "system_id": visit["system_id"],
        "n_fields": visit["n_fields"],
        "n_tables": visit["n_tables"],
        "n_named_results": visit["n_named_results"],
        "access_export_ok": status == "success",
        "parquet_export_ok": status == "success",
        "error_message": error_message,
    }


def write_processing_report(report_rows: List[Dict[str, Any]], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_dataframe_for_export(pd.DataFrame(report_rows, columns=REPORT_COLUMNS)).to_csv(
        report_path,
        index=False,
        encoding="utf-8",
    )


def print_summary(report_rows: List[Dict[str, Any]], files_found: int) -> None:
    successful = sum(1 for row in report_rows if row["status"] == "success")
    failed = sum(1 for row in report_rows if row["status"] != "success")
    missing_qampr = sum(1 for row in report_rows if not row.get("QAMPR"))
    parquet_errors = sum(1 for row in report_rows if not bool(row.get("parquet_export_ok")))
    access_errors = sum(1 for row in report_rows if not bool(row.get("access_export_ok")))

    print("Batch summary")
    print(f"files found: {files_found}")
    print(f"successful: {successful}")
    print(f"failed: {failed}")
    print(f"missing QAMPR: {missing_qampr}")
    print(f"Parquet export errors: {parquet_errors}")
    print(f"Access export errors: {access_errors}")


def main() -> int:
    warnings.filterwarnings(
        "ignore",
        message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated.*",
        category=FutureWarning,
    )

    args = parse_args()
    input_dir = Path(args.input_dir)
    sidecar_path = Path(args.sidecar)
    access_root = Path(args.to_access)
    parquet_root = Path(args.to_parquet)
    report_path = access_root.parent / "processing_report.csv"

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    if not sidecar_path.exists():
        raise FileNotFoundError(f"Sidecar not found: {sidecar_path}")

    sidecar = load_fixed_sidecar(sidecar_path)
    config = load_config()
    engine = ExtractionEngine(config)

    excel_files = find_excel_files(input_dir)
    visits: List[Dict[str, Any]] = []
    report_rows: List[Dict[str, Any]] = []
    tables: Dict[str, List[pd.DataFrame]] = defaultdict(list)

    for qaid, excel_file in enumerate(excel_files, start=1):
        print(f"[{qaid}/{len(excel_files)}] extracting {display_path(excel_file)}", flush=True)
        fields: Dict[str, Any] = {}
        try:
            extraction_result = engine.extract_from_path(str(excel_file), sidecar)
            fields = extraction_result.fields or {}
            visit = build_visit(
                qaid=qaid,
                source_file=excel_file,
                fields=fields,
                extraction_status="success",
                n_fields=len(fields),
                n_tables=len(extraction_result.tables),
                n_named_results=named_result_count(extraction_result.named_results),
            )

            for table_name, df in extraction_result.tables.items():
                if df is None or df.empty:
                    continue
                tables[table_name].append(add_visit_traceability(df, visit))

            visits.append(visit)
            report_rows.append(report_row_from_visit(visit, "success"))
        except Exception as exc:
            visit = build_visit(
                qaid=qaid,
                source_file=excel_file,
                fields=fields,
                extraction_status="failed",
                n_fields=0,
                n_tables=0,
                n_named_results=0,
            )
            visits.append(visit)
            report_rows.append(report_row_from_visit(visit, "failed", str(exc)))

    source_to_report = {str(row["source_file"]): row for row in report_rows}

    access_failed_sources, access_errors = export_access(tables, visits, access_root)
    parquet_failed_sources, parquet_errors = export_parquet(tables, visits, parquet_root)

    for row in report_rows:
        if row["status"] != "success":
            row["access_export_ok"] = False
            row["parquet_export_ok"] = False

    for source in access_failed_sources:
        row = source_to_report.get(str(source))
        if row is not None:
            row["access_export_ok"] = False
    for source in parquet_failed_sources:
        row = source_to_report.get(str(source))
        if row is not None:
            row["parquet_export_ok"] = False

    for message in access_errors.values():
        for row in report_rows:
            if row["source_file"] in access_failed_sources or "QAVisit metadata" in message:
                append_error(row, message)
    for message in parquet_errors.values():
        for row in report_rows:
            if row["source_file"] in parquet_failed_sources or "QAVisit metadata" in message:
                append_error(row, message)

    write_processing_report(report_rows, report_path)
    print_summary(report_rows, len(excel_files))

    has_errors = any(row["status"] != "success" for row in report_rows)
    has_errors = has_errors or any(not bool(row["access_export_ok"]) for row in report_rows)
    has_errors = has_errors or any(not bool(row["parquet_export_ok"]) for row in report_rows)
    return 1 if has_errors else 0


if __name__ == "__main__":
    started = datetime.now()
    try:
        raise SystemExit(main())
    except Exception as exc:
        elapsed = datetime.now() - started
        print(f"Thesis ingestion failed after {elapsed}: {exc}", file=sys.stderr)
        raise SystemExit(1)
