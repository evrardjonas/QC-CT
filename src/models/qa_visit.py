"""
QAVisit model for CT-QC visits.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional
from dataclasses import asdict, dataclass
import json
import logging
import re
import threading

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QAVisit:
    """Represents one extracted QA visit."""

    # Identifiers
    qaid: int
    qampr: Optional[str]

    # Metadata
    template_id: str
    sidecar_version: str
    workbook_hash: str
    excel_file_name: str
    reference_qc: Optional[str] = None

    # General information
    type: Optional[str] = None
    date_test: Optional[str] = None
    hospital_id: Optional[int] = None
    system_id: Optional[int] = None
    system_info_id: Optional[int] = None
    qa_member1: Optional[str] = None
    qa_member2: Optional[str] = None
    date_to_db: Optional[str] = None

    # Extracted data
    fields: Optional[Dict[str, Any]] = None
    tables: Optional[Dict[str, Any]] = None

    # Audit
    processing_timestamp: Optional[str] = None
    extraction_method: str = "template"

    _qaid_lock: ClassVar[threading.Lock] = threading.Lock()

    def __post_init__(self):
        if self.fields is None:
            self.fields = {}
        if self.tables is None:
            self.tables = {}
        if self.date_to_db is None:
            self.date_to_db = datetime.now().isoformat()
        if self.processing_timestamp is None:
            self.processing_timestamp = datetime.now().isoformat()

    @classmethod
    def from_extraction_result(cls, hdf_store, extraction_result, sidecar: Dict, audit_system):
        """Create a QAVisit from an ExtractionResult."""
        qaid = cls._generate_qaid_thread_safe(hdf_store)
        meta = extraction_result.meta
        reference_qc = cls._first_present(
            extraction_result.fields,
            "reference_QC",
            "qa_visit.reference_QC",
        )

        visit = cls(
            qaid=qaid,
            qampr=cls._derive_qampr(extraction_result.fields, meta),
            template_id=meta["template_id"],
            sidecar_version=meta["sidecar_version"],
            workbook_hash=meta["workbook_hash"],
            excel_file_name=meta.get("source_filename", "unknown"),
            reference_qc=reference_qc,
            fields=extraction_result.fields,
            tables=extraction_result.tables,
            processing_timestamp=meta["extraction_timestamp"],
        )

        visit._extract_additional_info(extraction_result, sidecar)
        visit._resolve_references(hdf_store, audit_system)

        audit_system.log_event(
            "INFO",
            "QAVisit",
            "Created",
            f"QAVisit {qaid} created successfully",
            {
                "qampr": visit.qampr,
                "reference_qc": visit.reference_qc,
                "template": visit.template_id,
            },
        )

        return visit

    def _extract_additional_info(self, extraction_result, sidecar: Dict):
        """Extract optional visit metadata from scalar fields."""
        self.type = self._first_present(
            extraction_result.fields, "test_type", "type_test", "qa_visit.type_test"
        )
        self.date_test = self._first_present(
            extraction_result.fields, "test_date", "date_test", "visit_date", "qa_visit.date_test"
        )
        self.qa_member1 = self._first_present(
            extraction_result.fields, "qa_member1", "qa_members"
        )
        self.qa_member2 = extraction_result.fields.get("qa_member2")

        physiciens = self._first_present(
            extraction_result.fields, "physiciens", "qa_visit.physiciens"
        )
        if isinstance(physiciens, list):
            if physiciens and not self.qa_member1:
                self.qa_member1 = (
                    physiciens[0].get("nom") if isinstance(physiciens[0], dict) else physiciens[0]
                )
            if len(physiciens) > 1 and not self.qa_member2:
                self.qa_member2 = (
                    physiciens[1].get("nom") if isinstance(physiciens[1], dict) else physiciens[1]
                )

        if "qa_info" in sidecar:
            qa_config = sidecar["qa_info"]
            if "default_type" in qa_config and not self.type:
                self.type = qa_config["default_type"]

    def _resolve_references(self, hdf_store, audit_system):
        """Resolve Hospital_ID/System_ID from Linktable using numeric QAMPR matching."""
        try:
            qampr_numeric = self._as_int_or_none(self.qampr)
            if qampr_numeric is None:
                message = f"No normalized QAMPR available for reference resolution: {self.qampr}"
                logger.warning(message)
                audit_system.log_event(
                    "WARNING",
                    "QAVisit",
                    "ReferenceResolutionSkipped",
                    message,
                    {"qampr": self.qampr, "reference_qc": self.reference_qc},
                    qaid=self.qaid,
                )
                return

            linktable = self._get_reference_table(hdf_store, "Linktable")
            if linktable.empty or "Qampr" not in linktable.columns:
                message = "Reference table Linktable is missing or has no Qampr column"
                logger.warning(message)
                audit_system.log_event(
                    "WARNING",
                    "QAVisit",
                    "ReferenceResolutionSkipped",
                    message,
                    {"qampr": self.qampr},
                    qaid=self.qaid,
                )
                return

            linktable = linktable.copy()
            linktable["Qampr_numeric"] = pd.to_numeric(linktable["Qampr"], errors="coerce")
            matches = linktable[linktable["Qampr_numeric"] == qampr_numeric]

            if matches.empty:
                message = f"No Linktable match for normalized QAMPR {qampr_numeric}"
                logger.warning(message)
                audit_system.log_event(
                    "WARNING",
                    "QAVisit",
                    "ReferenceResolutionNoMatch",
                    message,
                    {"qampr": self.qampr, "reference_qc": self.reference_qc},
                    qaid=self.qaid,
                )
                return

            first_match = matches.iloc[0]
            self.hospital_id = self._as_int_or_none(first_match.get("Hospital_ID"))
            self.system_id = self._as_int_or_none(first_match.get("System_ID"))

            if self.system_id is not None:
                systems = self._get_reference_table(hdf_store, "System")
                if not systems.empty and "ID" in systems.columns:
                    systems = systems.copy()
                    systems["ID_numeric"] = pd.to_numeric(systems["ID"], errors="coerce")
                    system_matches = systems[systems["ID_numeric"] == self.system_id]
                    if not system_matches.empty:
                        self.system_info_id = self._as_int_or_none(
                            system_matches.iloc[0].get("System_Info_ID")
                        )

            audit_system.log_event(
                "INFO",
                "QAVisit",
                "ReferencesResolved",
                "References resolved successfully",
                {"hospital_id": self.hospital_id, "system_id": self.system_id},
                qaid=self.qaid,
            )
        except Exception as e:
            audit_system.log_event(
                "WARNING",
                "QAVisit",
                "ReferenceResolutionFailed",
                f"Reference resolution failed: {e}",
                {},
                qaid=self.qaid,
            )
            logger.warning(f"Reference resolution failed for QAVisit {self.qaid}: {e}")

    @staticmethod
    def _first_present(fields: Dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            value = fields.get(key)
            if value is not None and value != "":
                return value
        return default

    @staticmethod
    def _derive_qampr(fields: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
        for key in ("qampr", "QAMPR"):
            normalized = QAVisit._normalize_qampr(fields.get(key))
            if normalized is not None:
                return normalized

        for key in ("reference_QC", "qa_visit.reference_QC"):
            normalized = QAVisit._normalize_qampr(fields.get(key))
            if normalized is not None:
                return normalized

        return QAVisit._normalize_qampr(meta.get("source_filename"))

    @staticmethod
    def _normalize_qampr(value: Any) -> Optional[str]:
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

        ct_match = re.search(r"(\d+)\s*CT\b", text, flags=re.IGNORECASE)
        if ct_match:
            return str(int(ct_match.group(1)))

        return None

    @staticmethod
    def _as_int_or_none(value: Any) -> Optional[int]:
        if value is None:
            return None
        numeric = pd.to_numeric(value, errors="coerce")
        if pd.isna(numeric):
            return None
        return int(numeric)

    @staticmethod
    def _get_reference_table(hdf_store, name: str) -> pd.DataFrame:
        try:
            if name in hdf_store:
                return hdf_store.get(name)
        except Exception as e:
            logger.warning(f"Could not load reference table {name}: {e}")

        static_path = Path("data") / "static" / f"{name}.txt"
        if static_path.exists():
            try:
                return pd.read_csv(static_path)
            except Exception as e:
                logger.warning(f"Could not load static reference table {static_path}: {e}")
        return pd.DataFrame()

    def persist_to_hdf(self) -> bool:
        """
        Persist the visit to HDF5.

        This method currently keeps compatibility with the existing pipeline,
        where extraction outputs are exported separately.
        """
        try:
            logger.info(f"QAVisit {self.qaid} ready for HDF5 persistence")
            return True
        except Exception as e:
            logger.error(f"Failed to persist QAVisit {self.qaid}: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary."""
        return asdict(self)

    def save_metadata(self, file_path: str):
        """Save compact visit metadata as JSON."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                metadata = {
                    "qaid": self.qaid,
                    "qampr": self.qampr,
                    "reference_qc": self.reference_qc,
                    "template_id": self.template_id,
                    "hospital_id": self.hospital_id,
                    "system_id": self.system_id,
                    "system_info_id": self.system_info_id,
                    "excel_file_name": self.excel_file_name,
                    "processing_timestamp": self.processing_timestamp,
                    "workbook_hash": self.workbook_hash,
                }
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save QAVisit metadata: {e}")

    @classmethod
    def _generate_qaid_thread_safe(cls, hdf_store) -> int:
        """Generate a visit ID with a class-level lock."""
        with cls._qaid_lock:
            return cls._generate_qaid(hdf_store)

    @staticmethod
    def _generate_qaid(hdf_store) -> int:
        """Generate a new QAID from existing HDF5 tables when available."""
        try:
            if "QAVisit" in hdf_store:
                existing_df = hdf_store.get("QAVisit")
                if not existing_df.empty and "ID" in existing_df.columns:
                    max_id = existing_df["ID"].max()
                    logger.debug(f"Dernier QAID trouve: {max_id}")
                    return int(max_id) + 1

            if "Sequences" in hdf_store:
                sequences = hdf_store.get("Sequences")
                if "qaid" in sequences["name"].values:
                    current_id = sequences.loc[sequences["name"] == "qaid", "value"].iloc[0]
                    logger.debug(f"QAID depuis Sequences: {current_id}")
                    return int(current_id) + 1
        except Exception as e:
            logger.warning(f"Failed to generate QAID from existing data: {e}")

        fallback_id = int(datetime.now().timestamp() * 1000) % 1000000
        logger.warning(f"Utilisation QAID fallback: {fallback_id}")
        return fallback_id

    def validate(self) -> bool:
        """Validate basic visit consistency."""
        required_fields = ["qaid", "template_id", "excel_file_name"]

        for field in required_fields:
            if not getattr(self, field):
                logger.error(f"QAVisit validation failed: missing {field}")
                return False

        if self.hospital_id and self.hospital_id <= 0:
            logger.warning(f"QAVisit {self.qaid} has invalid hospital_id: {self.hospital_id}")

        return True
