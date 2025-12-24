"""
Structured logging
"""

import logging
import json
from datetime import datetime


class StructuredLogger:
    """Structured logging handler"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        """Log structured message"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }
        getattr(self.logger, level.lower())(json.dumps(log_data))
