import glob
import re
import logging

logger = logging.getLogger(__name__)

def find_experiment_files():
    """
    Find all experiment files in the current directory.
    
    Returns:
        Dict mapping experiment names to a dict with 'membrane' and 'nuclei' file paths
    """
    all_tif_files = glob.glob('*.tif')
    experiments = {}
    
    # Find all potential experiment names
    membrane_pattern = re.compile(r'(.+)_membrane\.tif$')
    nuclei_pattern = re.compile(r'(.+)_nuclei\.tif$')
    
    # Extract experiment names from filenames
    for tif_file in all_tif_files:
        membrane_match = membrane_pattern.match(tif_file)
        nuclei_match = nuclei_pattern.match(tif_file)
        
        if membrane_match:
            exp_name = membrane_match.group(1)
            if exp_name not in experiments:
                experiments[exp_name] = {}
            experiments[exp_name]['membrane'] = tif_file
            
        if nuclei_match:
            exp_name = nuclei_match.group(1)
            if exp_name not in experiments:
                experiments[exp_name] = {}
            experiments[exp_name]['nuclei'] = tif_file
    
    return experiments
