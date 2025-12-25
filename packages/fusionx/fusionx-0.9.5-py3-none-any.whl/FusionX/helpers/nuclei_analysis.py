import os
import logging
import numpy as np
import pandas as pd
from PIL import Image
import scipy.ndimage as ndimage
from numba import jit
import time

logger = logging.getLogger(__name__)

@jit(nopython=True)
def _create_center_mask(center_of_mass_image, centers, labels, radius=3):
    """
    Create a mask with circles around centers of mass.
    Numba-accelerated function for faster processing.
    """
    for i, (y, x) in enumerate(centers):
        y, x = int(y), int(x)
        label_id = labels[i]
        y_min, y_max = max(0, y - radius), min(center_of_mass_image.shape[0], y + radius + 1)
        x_min, x_max = max(0, x - radius), min(center_of_mass_image.shape[1], x + radius + 1)
        
        for yy in range(y_min, y_max):
            for xx in range(x_min, x_max):
                if (yy - y)**2 + (xx - x)**2 <= radius**2:
                    center_of_mass_image[yy, xx] = label_id
    return center_of_mass_image

def analyze_nuclei_mask(mask_path):
    """
    Analyze a nuclei segmentation mask to identify out-of-focus nuclei.
    Optimized for processing thousands of nuclei.
    
    Args:
        mask_path: Path to the nuclei segmentation mask file
        
    Returns:
        Dictionary with analysis results
    """
    try:
        start_time = time.time()
        logger.info(f"Analyzing nuclei mask: {mask_path}")
        
        # Read the mask file
        mask = np.array(Image.open(mask_path))
        
        # Get unique labels (excluding background which is 0)
        labels = np.unique(mask)
        labels = labels[labels != 0]  # Remove background
        
        total_nuclei = len(labels)
        logger.info(f"Total nuclei found: {total_nuclei}")
        
        if total_nuclei == 0:
            logger.warning("No nuclei found in the mask!")
            return {
                'total_nuclei': 0,
                'mean_area': 0,
                'out_of_focus': 0,
                'out_of_focus_percentage': 0,
                'areas': {}
            }
        
        # Calculate areas more efficiently
        # Use bincount for speed with large number of nuclei
        start_bincount = time.time()
        counts = np.bincount(mask.ravel())
        logger.debug(f"Bincount calculation took {time.time() - start_bincount:.3f} seconds")
        
        # Skip background (label 0)
        # Only include labels that actually exist in the mask
        areas = {int(label): counts[label] for label in labels}
        
        # Calculate mean area
        mean_area = np.mean(list(areas.values()))
        logger.info(f"Mean nucleus area: {mean_area:.2f} pixels")
        
        # Define threshold for out-of-focus
        threshold = 0.00 * mean_area
        logger.info(f"Out-of-focus threshold: {threshold:.2f} pixels")
        
        # Count out-of-focus nuclei
        out_of_focus = sum(1 for area in areas.values() if area < threshold)
        out_of_focus_percentage = (out_of_focus / total_nuclei) * 100 if total_nuclei > 0 else 0
        
        logger.info(f"Out-of-focus nuclei: {out_of_focus}/{total_nuclei} ({out_of_focus_percentage:.2f}%)")
        logger.info(f"Nuclei analysis completed in {time.time() - start_time:.3f} seconds")
        
        return {
            'total_nuclei': total_nuclei,
            'mean_area': mean_area,
            'out_of_focus': out_of_focus,
            'out_of_focus_percentage': out_of_focus_percentage,
            'areas': areas
        }
        
    except Exception as e:
        logger.error(f"Error analyzing nuclei mask: {str(e)}")
        return None

def calculate_center_of_mass(mask_path, output_dir=None):
    """
    Calculate the center of mass for each nucleus in the mask.
    Creates a dataframe and visualization image.
    
    Args:
        mask_path: Path to the segmentation mask
        output_dir: Directory to save results (defaults to mask directory)
        
    Returns:
        DataFrame with nuclei IDs and their centers of mass
    """
    try:
        start_time = time.time()
        logger.info(f"Calculating center of mass for nuclei in: {mask_path}")
        
        # Set default output directory
        if output_dir is None:
            output_dir = os.path.dirname(mask_path)
        
        # Read the mask
        mask = np.array(Image.open(mask_path))
        
        # Get unique labels excluding background
        labels = np.unique(mask)
        labels = labels[labels != 0]
        
        logger.info(f"Found {len(labels)} nuclei")
        
        # Calculate areas and filter out small nuclei
        analysis_results = analyze_nuclei_mask(mask_path)
        if not analysis_results:
            return None
            
        mean_area = analysis_results['mean_area']
        threshold = 0.4 * mean_area
        
        # Get areas for all nuclei
        areas = analysis_results['areas']
        
        # Filter out nuclei with area < threshold
        filtered_labels = np.array([label for label, area in areas.items() if area >= threshold])
        logger.info(f"After filtering: {len(filtered_labels)} nuclei remain")
        
        # Calculate centers of mass for filtered nuclei
        # This is optimized for large numbers of nuclei
        start_com = time.time()
        centers = ndimage.center_of_mass(mask, mask, filtered_labels)
        logger.debug(f"Center of mass calculation took {time.time() - start_com:.3f} seconds")
        
        # Create DataFrame
        df = pd.DataFrame({
            'id': filtered_labels,
            'y': [center[0] for center in centers],
            'x': [center[1] for center in centers]
        })
        
        # Add integer coordinates
        df['y_int'] = df['y'].round().astype(int)
        df['x_int'] = df['x'].round().astype(int)
        
        # Save DataFrame to parquet only (more efficient)
        parquet_path = os.path.join(output_dir, 'nuclei_center_of_mass.parquet')
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Saved center of mass data to {parquet_path}")
        
        # Create center of mass image
        start_img = time.time()
        center_of_mass_image = np.zeros_like(mask, dtype=np.uint16)
        
        # Use optimized function to create the image
        center_of_mass_image = _create_center_mask(
            center_of_mass_image, 
            centers=[(row['y_int'], row['x_int']) for _, row in df.iterrows()], 
            labels=filtered_labels
        )
        
        # Save the image
        com_image_path = os.path.join(output_dir, 'nuclei_center_of_mass.tif')
        Image.fromarray(center_of_mass_image).save(com_image_path)
        logger.info(f"Created center of mass image at {com_image_path}")
        logger.debug(f"Image creation took {time.time() - start_img:.3f} seconds")
        
        # Total processing time
        logger.info(f"Center of mass calculation completed in {time.time() - start_time:.3f} seconds")
        
        return df
        
    except Exception as e:
        logger.error(f"Error calculating center of mass: {str(e)}")
        return None
