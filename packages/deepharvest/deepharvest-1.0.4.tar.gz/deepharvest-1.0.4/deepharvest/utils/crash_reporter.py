"""
crash_reporter.py - Crash report generation
"""

import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CrashReporter:
    """Generate crash reports for debugging"""

    def __init__(self, report_dir: str = "./crash_reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def report_crash(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """Generate crash report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
        }

        # Save report
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"crash_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.error(f"Crash report saved to {report_file}")
        return str(report_file)

    def report_error(self, error_type: str, message: str, context: Dict[str, Any] = None):
        """Report non-fatal error"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": message,
            "context": context or {},
        }

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"error_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.warning(f"Error report saved to {report_file}")
