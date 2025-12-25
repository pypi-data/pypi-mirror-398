import os
import logging
from PIL import Image
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

def get_image_dimensions(image_path):
    """
    Get the dimensions of an image file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (width, height) or None if there was an error
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting dimensions for {image_path}: {str(e)}")
        return None

def scale_image_hermite(image_path, output_path, target_size=(5000, 5000)):
    """
    Scale an image using high-quality resampling if it's larger than target_size.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the scaled image
        target_size: Target size as (width, height)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Open the image
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Only scale if the image is larger than target size
            if width > target_size[0] or height > target_size[1]:
                # This detailed log will go to output.log
                logger.info(f"Scaling {image_path} from {width}x{height} to {target_size[0]}x{target_size[1]}")
                
                # Use Lanczos resampling (good quality downsampling)
                scaled_img = img.resize(target_size, Image.LANCZOS)
                scaled_img.save(output_path)
                logger.info(f"Saved scaled image to {output_path}")
            else:
                # Just copy the image if it's already smaller
                logger.info(f"Image {image_path} is already smaller than target size. Copying...")
                img.save(output_path)
                
        return True
    except Exception as e:
        logger.error(f"Error scaling image {image_path}: {str(e)}")
        return False

def create_analysis_folders(experiments):
    """
    Create analysis folders for each experiment.
    
    Args:
        experiments: Dictionary of experiments
        
    Returns:
        Dictionary mapping experiment names to their analysis folder paths
    """
    analysis_folders = {}
    
    for exp_name in experiments:
        folder_name = f"analysis_{exp_name}"
        os.makedirs(folder_name, exist_ok=True)
        analysis_folders[exp_name] = folder_name
        logger.debug(f"Created analysis folder: {folder_name}")
    
    return analysis_folders

def process_experiment_images(experiments, analysis_folders, target_size=(6000, 6000)):
    """
    Process membrane and nuclei images for each experiment.
    
    Args:
        experiments: Dictionary of experiments
        analysis_folders: Dictionary of analysis folders
        target_size: Target size for scaling
        
    Returns:
        Dictionary of processed image paths
    """
    processed_images = {}
    
    for exp_name, files in experiments.items():
        processed_images[exp_name] = {}
        
        # Skip incomplete experiments
        if 'membrane' not in files or 'nuclei' not in files:
            logger.warning(f"Experiment {exp_name} is incomplete. Skipping processing.")
            continue
        
        analysis_folder = analysis_folders[exp_name]
        
        # Process membrane image
        membrane_path = files['membrane']
        output_membrane = os.path.join(analysis_folder, f"{exp_name}_membrane.tif")
        if scale_image_hermite(membrane_path, output_membrane, target_size):
            processed_images[exp_name]['membrane'] = output_membrane
        
        # Process nuclei image
        nuclei_path = files['nuclei']
        output_nuclei = os.path.join(analysis_folder, f"{exp_name}_nuclei.tif")
        if scale_image_hermite(nuclei_path, output_nuclei, target_size):
            processed_images[exp_name]['nuclei'] = output_nuclei
    
    return processed_images
