import os
import numpy as np
import pandas as pd
import tifffile
import random
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def draw_circle(image, center_y, center_x, radius, value):
    """Draw a filled circle on the image"""
    height, width = image.shape
    y_min = max(0, center_y - radius)
    y_max = min(height, center_y + radius + 1)
    x_min = max(0, center_x - radius)
    x_max = min(width, center_x + radius + 1)
    
    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            if (y - center_y)**2 + (x - center_x)**2 <= radius**2:
                image[y, x] = value
    
    return image

def visualize_cells_and_nuclei(analysis_folder):
    """
    Visualize cells from cells_nuclei_count.parquet and unassigned nuclei from unassigned_nuclei.parquet.
    Saves images in the analysis folder.
    
    Args:
        analysis_folder: Path to the analysis folder of the experiment
        
    Returns:
        Tuple of paths to the created cell and nuclei visualization images
    """
    # Get experiment name from analysis folder
    exp_name = os.path.basename(analysis_folder).replace('analysis_', '')
    
    # Output files with experiment name in the filenames
    cells_image_path = os.path.join(analysis_folder, f"{exp_name}_cell_instances.tif")
    nuclei_image_path = os.path.join(analysis_folder, f"{exp_name}_unassigned_nuclei.tif")
    
    # Find membrane image for dimensions
    membrane_image_path = os.path.join(analysis_folder, f"{exp_name}_membrane.tif")
    if not os.path.exists(membrane_image_path):
        # Fallback to just "membrane.tif"
        membrane_image_path = os.path.join(analysis_folder, "membrane.tif")
        
    # Get image dimensions from membrane image
    if os.path.exists(membrane_image_path):
        with Image.open(membrane_image_path) as img:
            width, height = img.size
        logger.info(f"Using dimensions from {membrane_image_path}: {width}x{height}")
    else:
        # Default dimensions if membrane image not found
        height, width = 6000, 6000
        logger.info(f"Membrane image not found, using default dimensions: {width}x{height}")
    
    # Input files
    validation_dir = os.path.join(analysis_folder, "segmentation_validation")
    cells_nuclei_count_path = os.path.join(validation_dir, "cells_nuclei_count.parquet")
    unassigned_nuclei_path = os.path.join(validation_dir, "unassigned_nuclei.parquet")
    
    # Check if files exist
    if not os.path.exists(cells_nuclei_count_path):
        logger.error(f"Cannot find cells_nuclei_count.parquet at {cells_nuclei_count_path}")
        return None, None
    
    # Read assigned cells
    logger.info(f"Reading cells from {cells_nuclei_count_path}")
    cells_df = pd.read_parquet(cells_nuclei_count_path)
    
    if cells_df.empty:
        logger.warning("No cells found in cells_nuclei_count.parquet, skipping cell visualization")
    else:
        # Create blank image for cells
        cells_image = np.zeros((height, width), dtype=np.uint16)
        
        # Get unique cell IDs
        cell_ids = cells_df['cell_id'].unique()
        
        # Create a mapping from cell ID to random color value (1-65535)
        cell_colors = {cell_id: random.randint(1, 65535) for cell_id in cell_ids}
        
        # Draw each cell with its random color
        for cell_id, group in cells_df.groupby('cell_id'):
            color = cell_colors[cell_id]
            
            # Get mask coordinates for this cell
            # Use first row's coordinates as all rows for this cell should have the same mask
            first_row = group.iloc[0]
            
            if 'mask_coordinates' in first_row and first_row['mask_coordinates'] is not None:
                # Draw the mask using the coordinates
                for coord in first_row['mask_coordinates']:
                    x, y = int(coord['x']), int(coord['y'])
                    if 0 <= y < height and 0 <= x < width:
                        cells_image[y, x] = color
        
        # Save the cells image
        tifffile.imwrite(cells_image_path, cells_image)
        logger.info(f"Saved cell visualization to {cells_image_path}")
    
    # Read unassigned nuclei
    if os.path.exists(unassigned_nuclei_path):
        logger.info(f"Reading unassigned nuclei from {unassigned_nuclei_path}")
        nuclei_df = pd.read_parquet(unassigned_nuclei_path)
        
        if nuclei_df.empty:
            logger.warning("No unassigned nuclei found, skipping nuclei visualization")
        else:
            # Create blank image for nuclei
            nuclei_image = np.zeros((height, width), dtype=np.uint16)
            
            # Draw each nucleus as a circle with 10-pixel diameter (radius 5)
            radius = 5
            for _, nucleus in nuclei_df.iterrows():
                if 'x' in nucleus and 'y' in nucleus:
                    x, y = int(nucleus['x']), int(nucleus['y'])
                    # Make sure coordinates are within bounds
                    if 0 <= y < height and 0 <= x < width:
                        nuclei_id = int(nucleus['id'])  # Using 'id' column from nuclei dataframe
                        
                        # Draw a circle at the nucleus position
                        nuclei_image = draw_circle(nuclei_image, y, x, radius, nuclei_id)
            
            # Save the nuclei image
            tifffile.imwrite(nuclei_image_path, nuclei_image)
            logger.info(f"Saved unassigned nuclei visualization to {nuclei_image_path}")
    else:
        logger.warning(f"Unassigned nuclei file not found: {unassigned_nuclei_path}")
        nuclei_image_path = None
    
    return cells_image_path, nuclei_image_path


def batch_visualize_experiments(analysis_folders, print_callback=None):
    """
    Generate visualizations for multiple experiments
    
    Args:
        analysis_folders: Dictionary mapping experiment names to analysis folder paths
        print_callback: Optional function for printing progress
        
    Returns:
        Dictionary with results for each experiment
    """
    results = {}
    
    if print_callback is None:
        print_callback = lambda msg: logger.info(msg)
    
    for exp_name, analysis_folder in analysis_folders.items():
        validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        
        # Check if validation directory exists
        if not os.path.exists(validation_dir):
            logger.warning(f"Validation directory not found for {exp_name}, skipping visualization")
            continue
            
        # Check for input files
        cells_nuclei_count_path = os.path.join(validation_dir, "cells_nuclei_count.parquet")
        
        if not os.path.exists(cells_nuclei_count_path):
            logger.warning(f"cells_nuclei_count.parquet not found for {exp_name}, skipping visualization")
            continue
        
        # Process this experiment
        print_callback(f"Creating visualizations for {exp_name}")
            
        cell_image_path, nuclei_image_path = visualize_cells_and_nuclei(analysis_folder)
        
        if cell_image_path or nuclei_image_path:
            results[exp_name] = {
                "status": "success",
                "cell_image_path": cell_image_path,
                "nuclei_image_path": nuclei_image_path
            }
            print_callback(f"Visualizations created for {exp_name}")
        else:
            results[exp_name] = {
                "status": "error",
                "error": "Failed to create visualizations"
            }
    
    return results
