# CT-QC Thesis Pipeline

Python ETL pipeline developed for a thesis project on quality control of CT scanners. It extracts semi-structured CT-QC Excel workbooks using a fixed YAML mapping and exports structured tables for inspection and statistical analysis.

## Scope

The repository contains the extraction pipeline, its YAML mapping, and configuration files. Raw workbooks, extracted measurements, database files, and generated analysis outputs are intentionally excluded.

## Main workflow

1. Discover `.xlsm` CT-QC workbooks in an input directory.
2. Extract scalar fields, named results, and measurement tables according to `templates/ctqc_base.yml`.
3. Add visit-level traceability metadata, scanner identifiers, and the selected dose regime.
4. Write Access-compatible TXT tables, Parquet tables, and a processing report.

## Installation

Python 3.9 or newer is required.

```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

Normal-dose dataset:

```powershell
python scripts/ingest_thesis.py "data/raw/Excel" `
  --sidecar "templates/ctqc_base.yml" `
  --dose-regime normal `
  --to-access "data/export/access_normal" `
  --to-parquet "data/export/parquet_normal"
```

Low-dose dataset:

```powershell
python scripts/ingest_thesis.py "data/raw/low_dose" `
  --sidecar "templates/ctqc_base.yml" `
  --dose-regime low_dose `
  --to-access "data/export/access_low_dose" `
  --to-parquet "data/export/parquet_low_dose"
```

The ingestion command processes all `.xlsm` files below the input directory. The dose regime is supplied explicitly and is not inferred from filenames.

## Repository structure

```text
config/                 General pipeline configuration
scripts/                Command-line ingestion script
src/core/               YAML mapping compilation
src/engine/             Extraction, normalization, validation, unit conversion
src/models/             Extraction and mapping data structures
src/utils/              Configuration helpers
templates/               CT-QC workbook extraction mapping
```

## Data policy

This public repository does not contain source Excel workbooks, DICOM files, extracted CT-QC measurements, hospital exports, or generated databases. These files remain local and are excluded through `.gitignore`.

## Current status

This is research software developed for a thesis workflow. The extraction rules are tailored to the CT-QC workbook structure used in the project and should be validated before reuse with other workbook versions.
