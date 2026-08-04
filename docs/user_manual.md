# CT-QC Orchestrator User Manual

This manual describes how to run the CT-QC Orchestrator from a local checkout.
The application ingests CT quality-control Excel workbooks, extracts data with a
YAML template, and can write HDF5, Access-compatible TXT, Parquet, logs, and visit
archives.

## Contents

1. [Installation](#installation)
2. [Project Layout](#project-layout)
3. [Configuration](#configuration)
4. [Excel Ingestion](#excel-ingestion)
5. [Outputs](#outputs)
6. [Analytics and Export Commands](#analytics-and-export-commands)
7. [Logs and Troubleshooting](#logs-and-troubleshooting)
8. [Recommended Workflow](#recommended-workflow)

## Installation

### Requirements

- Python 3.9 or newer
- Enough disk space for the HDF5 database, TXT exports, Parquet exports, and visit
  archives
- CT-QC Excel files in `.xls`, `.xlsx`, or `.xlsm` format

### Install Dependencies

From the repository root:

```bash
pip install -r requirements.txt
```

For command-line scripts such as `ctqc-ingest`, install the project in editable
mode:

```bash
pip install -e .
```

### Create Runtime Folders

Most folders already exist in this checkout. If you start from a clean checkout,
create the expected runtime structure:

```bash
mkdir -p data/raw/Excel
mkdir -p data/static
mkdir -p data/operational
mkdir -p data/export/access
mkdir -p data/export/parquet
mkdir -p visits/processed
mkdir -p logs
```

On Windows PowerShell, use:

```powershell
New-Item -ItemType Directory -Force data/raw/Excel, data/static, data/operational, data/export/access, data/export/parquet, visits/processed, logs
```

## Project Layout

Important paths:

- `config/default.yml`: default runtime configuration.
- `templates/ctqc_base.yml`: main extraction template.
- `data/raw/Excel/`: suggested location for source Excel workbooks.
- `data/static/`: reference TXT tables such as hospitals and systems.
- `data/operational/CTdb.hdf`: default HDF5 database.
- `data/export/access/`: Access-compatible TXT exports.
- `data/export/parquet/`: analytics Parquet exports.
- `visits/processed/`: per-visit archives with metadata and extraction results.
- `logs/`: application and audit logs.

## Configuration

The default configuration is `config/default.yml`.

Key settings:

```yaml
processing:
  default_template: "auto"
  strict_validation: false
  dry_run: false
  workers: 0
  batch_size: 10

templates:
  directory: "templates"
  fallback_template: "ctqc_base"

storage:
  hdf5_path: "data/operational/CTdb.hdf"
  visits_archive: "visits/processed"

access:
  delimiter: ","
  encoding: "utf-8"

parquet:
  compression: "ZSTD"
```

By default, template selection resolves to `ctqc_base`. Use a custom template only
when the matching YAML sidecar exists in `templates/`.

## Excel Ingestion

### Process One Workbook

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm
```

The command uses:

- config file: `config/default.yml`
- HDF5 path: `data/operational/CTdb.hdf`
- template: `ctqc_base` through the default `auto` selection

### Use Another Config File

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm --config config/development.yml
```

### Strict Validation

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm --strict
```

Strict mode asks the sidecar loader to validate more aggressively. Use it when
checking template changes or investigating extraction issues.

### Dry Run

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm --dry-run
```

Dry run performs selection and extraction without persistence or exports. It is
the safest first check for a new workbook or template edit.

### Process a Folder

```bash
ctqc-ingest data/raw/Excel
```

The folder scan is recursive and processes files ending in `.xls`, `.xlsx`, or
`.xlsm`.

### Parallel Processing

```bash
ctqc-ingest data/raw/Excel --workers 4 --batch-size 10
```

Use parallel processing only after a sequential run works. Each worker processes
workbooks independently, so failures are reported per file.

### Write Access and Parquet Exports During Ingestion

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm \
  --to-access data/export/access \
  --to-parquet data/export/parquet
```

On PowerShell:

```powershell
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm `
  --to-access data/export/access `
  --to-parquet data/export/parquet
```

### Disable Extra Exports

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm --no-export
```

This disables Access and Parquet exports requested through CLI options. The
orchestrator still runs the extraction flow.

## Outputs

### HDF5

The default operational database is:

```text
data/operational/CTdb.hdf
```

Reference tables in `data/static/*.txt` can be loaded by the HDF5 storage layer.
The visit model currently prepares visit metadata for HDF5 persistence and uses
the existing HDF5 content to generate the next QA visit ID when possible.

### Access TXT

Access exports are written as quoted, comma-delimited UTF-8 TXT files. Files are
organized by logical source sheet where possible, for example:

```text
data/export/access/Metadata/QAVisit.txt
data/export/access/CTDI_32cm/CTDI_32_KV.txt
data/export/access/Beeldkwaliteit/Uniformity.txt
```

Generated files include a `QAID` column when they are linked to a visit.

### Parquet

Parquet exports are partitioned for analytics:

```text
data/export/parquet/year=<year>/hospital=<hospital_id>/system=<system_id>/
```

Typical files include:

- `visit_metadata.parquet`
- `extraction_audit.parquet`
- `extracted_fields.parquet`
- specific result tables such as geometry, CTDI, image-quality, noise, protocol,
  scalar, and named-result outputs
- generic extracted tables under `tables/`

### Visit Archive

Processed visits are archived under:

```text
visits/processed/
```

Each visit archive can contain:

- `metadata.json`
- `extraction_result.json`
- `audit_log.json`

## Analytics and Export Commands

### Statistics From Parquet

```bash
ctqc-analytics stats --parquet-path data/export/parquet
```

Group the statistics:

```bash
ctqc-analytics stats --parquet-path data/export/parquet --by-hospital
ctqc-analytics stats --parquet-path data/export/parquet --by-system
```

Current limitation: the `ctqc-analytics export` and `ctqc-analytics dashboard`
subcommands are present in the CLI, but the parser does not currently expose a
`--parquet-path` option for them. Use the `stats` subcommand from the CLI, or call
`ParquetAnalytics` from Python for export/dashboard work until the CLI is
extended.

### Export Access TXT From HDF5

```bash
ctqc-export access --hdf-path data/operational/CTdb.hdf --output-dir data/export/access
```

Export only selected HDF5 tables:

```bash
ctqc-export access \
  --hdf-path data/operational/CTdb.hdf \
  --output-dir data/export/access \
  --tables QAVisit CTDI_Results
```

On PowerShell:

```powershell
ctqc-export access `
  --hdf-path data/operational/CTdb.hdf `
  --output-dir data/export/access `
  --tables QAVisit CTDI_Results
```

### Audit Reports

```bash
ctqc-export audit --hdf-path data/operational/CTdb.hdf --format html --output audit.html
```

Supported output choices exposed by the CLI are `html`, `pdf`, and `csv`.

## Logs and Troubleshooting

Logs are written to `logs/` according to `config/default.yml`.

### Check That Commands Are Installed

```bash
ctqc-ingest --help
ctqc-export --help
ctqc-analytics --help
```

If the commands are missing, run:

```bash
pip install -e .
```

### Check Python Imports

```bash
python -c "import pandas, openpyxl, pyarrow, tables, yaml; print('dependencies ok')"
```

### Excel File Cannot Be Read

Close the workbook in Excel and retry. Also confirm that the file extension is
`.xls`, `.xlsx`, or `.xlsm`.

### Missing Sheet or Missing Values

Run a dry run first:

```bash
ctqc-ingest data/raw/Excel/QC300_0624_01504CT-CT11.xlsm --dry-run --strict
```

Then check:

- the workbook sheet names
- `templates/ctqc_base.yml`
- `logs/ctqc.log`
- the generated extraction audit, if an archive/export was written

### Access Import Issues

The TXT output is quoted and comma-delimited by default. If Access expects a
different delimiter or encoding, change `access.delimiter` or `access.encoding`
in `config/default.yml` and rerun the export.

### Parquet Analytics Returns No Statistics

Confirm that the path points to the Parquet export root, not to one individual
partition file:

```bash
ctqc-analytics stats --parquet-path data/export/parquet
```

If the result is empty, verify that ingestion was run with `--to-parquet` and
that Parquet files exist below `data/export/parquet`.

## Recommended Workflow

1. Put source workbooks in `data/raw/Excel/`.
2. Run one workbook with `--dry-run --strict`.
3. Review logs and extraction warnings.
4. Run the workbook without `--dry-run`.
5. Add `--to-access` and `--to-parquet` when exports are needed.
6. Process the full folder sequentially.
7. Increase `--workers` only after sequential processing is stable.
8. Keep `visits/processed/` and `logs/` for traceability.
