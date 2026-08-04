"""
Système d'audit CT-QC
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Événement d'audit"""
    timestamp: str
    level: str  # INFO, WARNING, ERROR, SUCCESS, DEBUG
    component: str
    event_type: str
    message: str
    details: Dict[str, Any]
    file_name: str = ""
    qaid: Optional[int] = None
    duration_ms: Optional[int] = None


class AuditSystem:
    """
    Système d'audit moderne avec export multi-format
    """
    
    def __init__(self):
        self.events: List[AuditEvent] = []
        self.metrics: Dict[str, Any] = {
            'processing_start': datetime.now().isoformat(),
            'files_processed': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_events': 0
        }
        
    def log_event(self, level: str, component: str, event_type: str, 
                 message: str, details: Dict = None, file_name: str = "", 
                 qaid: int = None, duration_ms: int = None):
        """Enregistre un événement d'audit"""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            level=level,
            component=component,
            event_type=event_type,
            message=message,
            details=details or {},
            file_name=file_name,
            qaid=qaid,
            duration_ms=duration_ms
        )
        self.events.append(event)
        self.metrics['total_events'] += 1
        
        # Log également dans le système de logging
        log_message = f"[{level}] {component}.{event_type}: {message}"
        if file_name:
            log_message += f" | File: {file_name}"
        if duration_ms:
            log_message += f" | Duration: {duration_ms}ms"
        
        if level == "ERROR":
            logger.error(log_message)
        elif level == "WARNING":
            logger.warning(log_message)
        elif level == "SUCCESS":
            logger.info(log_message)
        else:
            logger.info(log_message)
    
    # Méthodes pratiques
    def log_processing_start(self, file_name: str):
        self.metrics['files_processed'] += 1
        self.log_event("INFO", "Orchestrator", "ProcessingStart", 
                      f"Start processing file", {"file": file_name}, file_name)
    
    def log_processing_success(self, file_name: str, qaid: int, template_id: str):
        self.metrics['successful_files'] += 1
        self.log_event("SUCCESS", "Orchestrator", "ProcessingComplete", 
                      f"File processed successfully", 
                      {"qaid": qaid, "template_id": template_id}, file_name, qaid)
    
    def log_processing_error(self, file_name: str, error: str):
        self.metrics['failed_files'] += 1
        self.log_event("ERROR", "Orchestrator", "ProcessingFailed", 
                      f"Processing failed: {error}", 
                      {"error": str(error)}, file_name)
    
    def log_dry_run_success(self, file_name: str, template_id: str):
        self.log_event("INFO", "Orchestrator", "DryRunComplete", 
                      f"Dry-run validation successful", 
                      {"template_id": template_id}, file_name)
    
    def log_template_selection(self, file_name: str, template_id: str, method: str):
        self.log_event("INFO", "TemplateSelector", "TemplateSelected", 
                      f"Template {template_id} selected", 
                      {"method": method}, file_name)
    
    def log_extraction_result(self, file_name: str, fields_count: int, tables_count: int):
        self.log_event("INFO", "ExtractionEngine", "ExtractionComplete", 
                      f"Extracted {fields_count} fields and {tables_count} tables", 
                      {"fields": fields_count, "tables": tables_count}, file_name)
    
    def log_batch_completion(self, success_count: int, total_count: int):
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        self.log_event("INFO", "Orchestrator", "BatchComplete", 
                      f"Batch processing completed", 
                      {"success_count": success_count, "total_count": total_count, 
                       "success_rate": f"{success_rate:.1f}%"})
    
    # Export des données d'audit
    def export_to_hdf(self, hdf_store):
        """Exporte l'audit vers HDF5"""
        if not self.events:
            return
        
        audit_data = []
        for event in self.events:
            audit_data.append({
                'timestamp': event.timestamp,
                'level': event.level,
                'component': event.component,
                'event_type': event.event_type,
                'message': event.message,
                'file_name': event.file_name,
                'qaid': event.qaid,
                'duration_ms': event.duration_ms,
                'details': json.dumps(event.details, ensure_ascii=False)
            })
        
        df = pd.DataFrame(audit_data)
        
        try:
            if 'AuditTrail' in hdf_store:
                existing_df = hdf_store.get('AuditTrail')
                updated_df = pd.concat([existing_df, df], ignore_index=True)
                hdf_store.put('AuditTrail', updated_df)
            else:
                hdf_store.put('AuditTrail', df)
                
            logger.info(f"Audit data exported to HDF5: {len(df)} events")
        except Exception as e:
            logger.error(f"Failed to export audit to HDF5: {e}")
    
    def export_to_parquet(self, output_path: str):
        """Exporte l'audit vers Parquet"""
        if not self.events:
            return
        
        audit_data = []
        for event in self.events:
            audit_data.append(asdict(event))
        
        df = pd.DataFrame(audit_data)
        os.makedirs(output_path, exist_ok=True)
        
        try:
            # Partitionnement par date
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            for date in df['date'].unique():
                date_df = df[df['date'] == date]
                date_str = date.strftime("%Y%m%d")
                file_path = os.path.join(output_path, f"audit_{date_str}.parquet")
                date_df.drop('date', axis=1).to_parquet(file_path, index=False)
            
            logger.info(f"Audit data exported to Parquet: {len(df)} events")
        except Exception as e:
            logger.error(f"Failed to export audit to Parquet: {e}")
    
    def export_to_txt(self, output_path: str):
        """Exporte l'audit vers TXT (pour Access)"""
        if not self.events:
            return
        
        os.makedirs(output_path, exist_ok=True)
        file_path = os.path.join(output_path, "AuditTrail.txt")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("timestamp\tlevel\tcomponent\tevent_type\tmessage\tfile_name\tqaid\tduration_ms\tdetails\n")
                for event in self.events:
                    details_str = json.dumps(event.details, ensure_ascii=False).replace('\t', ' ')
                    line = f"{event.timestamp}\t{event.level}\t{event.component}\t{event.event_type}\t{event.message}\t{event.file_name}\t{event.qaid}\t{event.duration_ms}\t{details_str}\n"
                    f.write(line)
            
            logger.info(f"Audit data exported to TXT: {len(self.events)} events")
        except Exception as e:
            logger.error(f"Failed to export audit to TXT: {e}")
    
    def save_visit_audit(self, file_path: str):
        """Sauvegarde l'audit d'une visite spécifique"""
        visit_events = [e for e in self.events if e.qaid is not None]
        if not visit_events:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                audit_data = [asdict(event) for event in visit_events]
                json.dump(audit_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save visit audit: {e}")
    
    def load_from_hdf(self, hdf_store):
        """Charge l'audit depuis HDF5"""
        try:
            if 'AuditTrail' in hdf_store:
                df = hdf_store.get('AuditTrail')
                self.events = []
                for _, row in df.iterrows():
                    event = AuditEvent(
                        timestamp=row['timestamp'],
                        level=row['level'],
                        component=row['component'],
                        event_type=row['event_type'],
                        message=row['message'],
                        file_name=row['file_name'],
                        qaid=row['qaid'],
                        duration_ms=row['duration_ms'],
                        details=json.loads(row['details'])
                    )
                    self.events.append(event)
        except Exception as e:
            logger.error(f"Failed to load audit from HDF5: {e}")
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Retourne des métriques résumées"""
        metrics = self.metrics.copy()
        
        if self.events:
            metrics['total_events'] = len(self.events)
            metrics['error_events'] = len([e for e in self.events if e.level == "ERROR"])
            metrics['warning_events'] = len([e for e in self.events if e.level == "WARNING"])
            metrics['success_events'] = len([e for e in self.events if e.level == "SUCCESS"])
            
            if metrics['files_processed'] > 0:
                metrics['success_rate'] = (metrics['successful_files'] / metrics['files_processed'] * 100)
            else:
                metrics['success_rate'] = 0
        
        metrics['processing_end'] = datetime.now().isoformat()
        return metrics
    
    def generate_report(self, format: str = "html", output_file: str = None) -> str:
        """Génère un rapport d'audit"""
        metrics = self.get_summary_metrics()
        
        if format == "html":
            return self._generate_html_report(metrics, output_file)
        elif format == "csv":
            return self._generate_csv_report(metrics, output_file)
        else:
            return self._generate_text_report(metrics, output_file)
    
    def _generate_html_report(self, metrics: Dict, output_file: str) -> str:
        """Génère un rapport HTML"""
        # Implémentation simplifiée
        html_content = f"""
        <html>
        <head><title>CT-QC Audit Report</title></head>
        <body>
            <h1>CT-QC Audit Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            <h2>Summary</h2>
            <ul>
                <li>Files Processed: {metrics['files_processed']}</li>
                <li>Successful: {metrics['successful_files']}</li>
                <li>Failed: {metrics['failed_files']}</li>
                <li>Success Rate: {metrics.get('success_rate', 0):.1f}%</li>
            </ul>
        </body>
        </html>
        """
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def _generate_csv_report(self, metrics: Dict, output_file: str) -> str:
        """Génère un rapport CSV"""
        csv_lines = ["metric,value"]
        for key, value in metrics.items():
            csv_lines.append(f"{key},{value}")
        
        csv_content = "\n".join(csv_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
        
        return csv_content
    
    def _generate_text_report(self, metrics: Dict, output_file: str) -> str:
        """Génère un rapport texte"""
        text_lines = [
            "CT-QC AUDIT REPORT",
            "==================",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "SUMMARY:",
            f"  Files Processed: {metrics['files_processed']}",
            f"  Successful:      {metrics['successful_files']}",
            f"  Failed:          {metrics['failed_files']}",
            f"  Success Rate:    {metrics.get('success_rate', 0):.1f}%",
            f"  Total Events:    {metrics['total_events']}",
        ]
        
        text_content = "\n".join(text_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        return text_content
    
    def clear_events(self):
        """Vide les événements d'audit"""
        self.events.clear()
        self.metrics = {
            'processing_start': datetime.now().isoformat(),
            'files_processed': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_events': 0
        }