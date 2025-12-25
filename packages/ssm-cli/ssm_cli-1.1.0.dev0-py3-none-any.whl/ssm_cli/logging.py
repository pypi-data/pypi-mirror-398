import logging
import threading
from datetime import datetime, timedelta
from typing import Optional
from ssm_cli.xdg import get_log_file, get_all_log_files

logger = logging.getLogger(__name__)

def setup_logging(name:str = "cli"):
    """Set up basic logging configuration with date-based rotation."""
    logging.basicConfig(
        level=logging.WARNING,
        filename=get_log_file(name),
        filemode='a',
        format='%(asctime)s - %(process)d [%(threadName)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    start_log_cleanup()


def set_log_level(level: str, name: Optional[str] = None):
    """Configure logger level."""
    logger.debug(f"setting logger {name} to {level}")
    logging.getLogger(name).setLevel(level.upper())


def cleanup_old_logs(days_to_keep: int = 7):
    """Clean up log files older than specified days. Runs with no error handling."""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    for log_file in get_all_log_files():
        # Extract date from filename
        date_part = log_file.stem.split('.')[-1]
        file_date = datetime.strptime(date_part, '%Y-%m-%d')
        
        if file_date < cutoff_date:
            log_file.unlink()


def start_log_cleanup(days_to_keep: int = 7):
    """Start log cleanup in background thread without error handling."""
    thread = threading.Thread(target=cleanup_old_logs, args=(days_to_keep,), daemon=True)
    thread.start()
