#!/usr/bin/env python3
"""
Outils analytics et reporting CT-QC
"""

import argparse
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from storage.parquet_export import ParquetAnalytics
from utils.config import load_config


def main():
    """Outils analytics pour données CT-QC"""
    parser = argparse.ArgumentParser(
        prog="ctqc-analytics",
        description="Analytics et reporting des données CT-QC"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes")
    
    # Stats globales
    stats_parser = subparsers.add_parser("stats", help="Statistiques globales")
    stats_parser.add_argument("--parquet-path", required=True, 
                             help="Chemin données Parquet")
    stats_parser.add_argument("--by-hospital", action="store_true",
                             help="Grouper par hôpital")
    stats_parser.add_argument("--by-system", action="store_true",
                             help="Grouper par système")
    
    # Export analytics
    export_parser = subparsers.add_parser("export", help="Export analytics")
    export_parser.add_argument("--format", choices=["csv", "excel", "json"], 
                              default="csv", help="Format d'export")
    export_parser.add_argument("--output", "-o", required=True,
                             help="Fichier de sortie")
    export_parser.add_argument("--filters", nargs="+",
                             help="Filtres (ex: hospital_id=300)")
    
    # Dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Génération dashboard")
    dashboard_parser.add_argument("--output-dir", required=True,
                                help="Dossier de sortie dashboard")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = load_config()
    analytics = ParquetAnalytics(args.parquet_path, config)
    
    if args.command == "stats":
        stats = analytics.get_global_stats(
            group_by_hospital=args.by_hospital,
            group_by_system=args.by_system
        )
        print("=== CT-QC Analytics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
            
    elif args.command == "export":
        analytics.export_data(args.format, args.output, args.filters)
        print(f"Data exported to {args.output}")
        
    elif args.command == "dashboard":
        analytics.generate_dashboard(args.output_dir)
        print(f"Dashboard generated in {args.output_dir}")


if __name__ == "__main__":
    main()