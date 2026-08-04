#!/usr/bin/env python3
"""
Export et reporting CT-QC
"""

import argparse
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from storage.access_export import AccessExporter
from core.audit import AuditSystem
from utils.config import load_config


def main():
    """Export et reporting"""
    parser = argparse.ArgumentParser(
        prog="ctqc-export",
        description="Export et reporting des données CT-QC"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes")
    
    # Export Access
    access_parser = subparsers.add_parser("access", help="Export pour MS Access")
    access_parser.add_argument("--hdf-path", required=True, help="Chemin HDF5")
    access_parser.add_argument("--output-dir", required=True, help="Dossier sortie")
    access_parser.add_argument("--tables", nargs="+", 
                              help="Tables spécifiques (sinon toutes)")
    
    # Audit report
    audit_parser = subparsers.add_parser("audit", help="Rapport d'audit")
    audit_parser.add_argument("--hdf-path", required=True, help="Chemin HDF5")
    audit_parser.add_argument("--format", choices=["html", "pdf", "csv"],
                             default="html", help="Format rapport")
    audit_parser.add_argument("--output", "-o", required=True,
                             help="Fichier de sortie")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = load_config()
    
    if args.command == "access":
        exporter = AccessExporter(args.output_dir, config)
        exporter.export_from_hdf(args.hdf_path, args.tables)
        print(f"Access export completed to {args.output_dir}")
        
    elif args.command == "audit":
        audit_system = AuditSystem()
        audit_system.load_from_hdf(args.hdf_path)
        audit_system.generate_report(args.format, args.output)
        print(f"Audit report generated: {args.output}")


if __name__ == "__main__":
    main()