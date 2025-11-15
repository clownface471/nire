"""
Logging Configuration
Sets up structured logging with file and console output.
"""

import sys
import structlog
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = "./data/logs/nire.log"):
    """
    Configure structlog for the application.
    
    Outputs:
    - JSON logs to file (for production analysis)
    - Pretty console logs (for development)
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File processor (JSON)
    file_processor = structlog.processors.JSONRenderer()
    
    # Console processor (Pretty)
    console_processor = structlog.dev.ConsoleRenderer()
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            console_processor if log_level == "DEBUG" else file_processor,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set log level
    level_map = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
    }
    
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level_map.get(log_level, 20),
    )
