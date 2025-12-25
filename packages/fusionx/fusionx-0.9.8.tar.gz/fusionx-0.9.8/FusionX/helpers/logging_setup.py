import os
import logging
import sys

def setup_logging():
    """Configure logging to redirect all logs to output.log"""
    # Use the current directory for the log file
    log_file = 'output.log'
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Changed to INFO to reduce log volume
    
    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Make sure the directory exists for the log file
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # File handler for all logs including errors
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)  # Changed to INFO level
    file_formatter = logging.Formatter('%(asctime)s - FusionX [%(levelname)s] - %(message)s', '%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # We're using custom console print functions instead of a console handler
    # to handle the inline progress updates
    
    return logging.getLogger("FusionX")
