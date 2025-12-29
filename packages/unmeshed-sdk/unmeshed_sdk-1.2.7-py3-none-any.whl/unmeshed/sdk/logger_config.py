import logging
import logging.handlers
import os
from datetime import datetime


class LoggerFactory:
    _instance = None

    @classmethod
    def setup_logging(cls, enable_file_logging=False, log_directory="logs"):
        """Setup logging configuration"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )

        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

        # File handler if enabled
        if enable_file_logging:
            if not os.path.exists(log_directory):
                os.makedirs(log_directory)

            log_file = os.path.join(
                log_directory,
                f"app_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10485760,
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name=None):
        """Get a logger instance"""
        return logging.getLogger(name or __name__)


# Create convenience functions
def get_logger(name=None):
    return LoggerFactory.get_logger(name)