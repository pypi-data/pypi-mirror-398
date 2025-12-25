import shutil
from datetime import datetime
from tqdm import tqdm
import logging
import os

logger = logging.getLogger(__name__)

def get_console_width():
    """Get the current terminal width"""
    try:
        return shutil.get_terminal_size().columns
    except Exception as e:
        logger.error(f"Error getting console width: {str(e)}")
        return 80  # Default width

def create_progress_bar(total, desc):
    """Create a custom progress bar with timestamp"""
    try:
        console_width = get_console_width()
        current_time = datetime.now().strftime("%y%m%d %H:%M:%S")
        bar_format = f'{current_time} - FusionX [INFO] - {{desc}} - {{n_fmt}}/{{total_fmt}} [{{elapsed}}<{{remaining}}]'
        return tqdm(total=total, desc=desc, bar_format=bar_format, ncols=console_width, position=0, leave=True)
    except Exception as e:
        logger.error(f"Error creating progress bar: {str(e)}")
        return None

def update_progress_bar(progress_bar, new_items=None, processed_nuclei=None, current_file=None):
    """
    Update the progress bar with current progress.
    
    Args:
        progress_bar: The tqdm progress bar instance
        new_items: New items to add to the progress count
        processed_nuclei: Set of processed nuclei IDs for tracking
        current_file: Current file being processed (for display)
    """
    if progress_bar is None:
        return
        
    if new_items is not None:
        if isinstance(new_items, (list, tuple, set)):
            progress_bar.update(len(new_items))
        else:
            progress_bar.update(new_items)
            
    if processed_nuclei is not None and new_items is not None:
        if isinstance(new_items, (list, tuple)):
            try:
                new_ids = set(n for row in new_items for n in row.get('nuclei_inside', []))
                processed_nuclei.update(new_ids)
            except Exception as e:
                logger.error(f"Error updating processed nuclei: {str(e)}")
        
    if current_file is not None:
        progress_bar.set_postfix_str(f"Current file: {os.path.basename(current_file)}")
