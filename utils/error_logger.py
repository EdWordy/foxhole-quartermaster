# utils/error_logger.py
import logging
import os
from datetime import datetime
import traceback

class ErrorLogger:
    def __init__(self, app_name='FoxholeQuartermaster'):
        self.app_name = app_name
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Set up logging configuration."""
        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create log filename with date
        log_file = f'logs/{self.app_name.lower()}_{datetime.now():%Y%m%d}.log'
        
        # File handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Remove existing handlers to prevent duplicates
        logger.handlers.clear()
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def log_error(self, error, context=""):
        """Log an error with context and stack trace."""
        error_msg = f"{context}: {str(error)}"
        stack_trace = traceback.format_exc()
        self.logger.error(f"{error_msg}\n{stack_trace}")
        
    def log_warning(self, message, context=""):
        """Log a warning message with context."""
        self.logger.warning(f"{context}: {message}")
    
    def log_info(self, message):
        """Log an info message."""
        self.logger.info(message)
        
    def get_latest_logs(self, num_lines=50):
        """Get the most recent log entries."""
        try:
            log_file = f'logs/{self.app_name.lower()}_{datetime.now():%Y%m%d}.log'
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    return ''.join(f.readlines()[-num_lines:])
            return "No logs found for today."
        except Exception as e:
            return f"Error reading logs: {str(e)}"