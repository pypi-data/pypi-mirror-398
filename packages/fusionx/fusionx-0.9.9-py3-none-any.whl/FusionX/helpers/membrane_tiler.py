import os
import logging
import numpy as np
from PIL import Image
import math
import time

logger = logging.getLogger(__name__)

def calculate_histogram_window(img_array, percentile_low=1, percentile_high=99):
    """
    Calculate min and max values for display windowing based on histogram percentiles.
    
    Args:
        img_array: NumPy array of image data
        percentile_low: Lower percentile to use (default 1%)
        percentile_high: Upper percentile to use (default 99%)
        
    Returns:
        Tuple of (min_val, max_val) for display windowing
    """
    try:
        # Handle different image formats
        if len(img_array.shape) == 3:  # Color image
            # Calculate histogram for each channel
            mins = []
            maxs = []
            for c in range(img_array.shape[2]):
                channel = img_array[:, :, c].flatten()
                # Skip empty channels
                if np.max(channel) == np.min(channel):
                    continue
                # Calculate percentiles
                mins.append(np.percentile(channel, percentile_low))
                maxs.append(np.percentile(channel, percentile_high))
            
            if not mins or not maxs:  # All channels were empty
                return 0, 255
                
            min_val = min(mins)
            max_val = max(maxs)
        else:  # Grayscale
            flat_img = img_array.flatten()
            min_val = np.percentile(flat_img, percentile_low)
            max_val = np.percentile(flat_img, percentile_high)
        
        # Ensure min and max are different
        if min_val == max_val:
            min_val = 0
            max_val = 255
            
        logger.info(f"Display window: [{min_val:.1f}, {max_val:.1f}]")
        return min_val, max_val
        
    except Exception as e:
        logger.error(f"Error calculating histogram window: {str(e)}")
        return 0, 255  # Default full range

def apply_display_window(img_array, min_val, max_val):
    """
    Apply display windowing to an image for better visibility.
    Only affects how the image is displayed, not the underlying data.
    
    Args:
        img_array: NumPy array of image data
        min_val: Minimum value for window
        max_val: Maximum value for window
        
    Returns:
        Windowed image array for display
    """
    try:
        # Convert to float for calculation
        img_float = img_array.astype(np.float32)
        
        # Apply windowing
        img_windowed = np.clip(img_float, min_val, max_val)
        
        # Rescale to 0-255
        img_scaled = ((img_windowed - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        
        return img_scaled
    except Exception as e:
        logger.error(f"Error applying display window: {str(e)}")
        return img_array

def tile_membrane_image(image_path, output_dir, tile_size=1024, overlap_percent=50):
    """
    Split a membrane image into tiles of specified size with overlap.
    The edge tiles will not be padded and will maintain their irregular sizes.
    Histogram-based display windowing is applied for better visibility.
    
    Args:
        image_path: Path to the membrane image
        output_dir: Directory to save the tiles
        tile_size: Size of each tile (width=height)
        overlap_percent: Overlap between tiles in percentage (default 50%)
        
    Returns:
        Number of tiles created
    """
    try:
        start_time = time.time()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate overlap in pixels
        overlap = int(tile_size * overlap_percent / 100)
        logger.info(f"Using {overlap} pixels ({overlap_percent}%) overlap between tiles")
        
        # Open the image
        original_img = Image.open(image_path)
        width, height = original_img.size
        logger.info(f"Tiling membrane image {image_path} ({width}x{height}) into tiles with base size {tile_size}x{tile_size}")
        
        # Convert to numpy array for histogram analysis
        img_array = np.array(original_img)
        
        # Calculate global histogram windowing parameters
        min_val, max_val = calculate_histogram_window(img_array, 1, 99)
        
        # Calculate the step size between tiles
        step = tile_size - overlap
        
        # Calculate the number of tiles in each dimension
        n_tiles_x = math.ceil((width - overlap) / step)
        n_tiles_y = math.ceil((height - overlap) / step)
        
        logger.info(f"Will create approximately {n_tiles_x}x{n_tiles_y} = {n_tiles_x * n_tiles_y} tiles")
        
        # Track the number of tiles actually created
        tiles_created = 0
        
        # Find the maximum x and y coordinates for edge detection
        max_y_coord = n_tiles_y - 1
        max_x_coord = n_tiles_x - 1
        
        # Create the tiles
        for y in range(n_tiles_y):
            for x in range(n_tiles_x):
                # Calculate the tile coordinates
                x_start = x * step
                y_start = y * step
                
                # Calculate the actual tile size (may be smaller at edges)
                actual_width = min(tile_size, width - x_start)
                actual_height = min(tile_size, height - y_start)
                
                # Skip if the tile would be empty or too small
                if actual_width <= 0 or actual_height <= 0:
                    continue
                
                # Extract the tile
                if len(img_array.shape) == 3:  # Color image
                    tile_array = img_array[y_start:y_start + actual_height, x_start:x_start + actual_width, :]
                else:  # Grayscale
                    tile_array = img_array[y_start:y_start + actual_height, x_start:x_start + actual_width]
                
                # Apply display windowing for better visibility
                # This doesn't change the data, just how it's displayed
                windowed_tile = apply_display_window(tile_array, min_val, max_val)
                
                # Convert to PIL Image 
                tile_img = Image.fromarray(windowed_tile)
                
                # Save the tile using the expected naming convention (tile_{y}_{x}.png)
                # Matching the original code's coordinate order
                tile_filename = f"tile_{y}_{x}.png"
                tile_path = os.path.join(output_dir, tile_filename)
                tile_img.save(tile_path)
                
                tiles_created += 1
        
        # Close the original image
        original_img.close()
        
        # Log the maximum coordinates for reference
        logger.info(f"Maximum tile coordinates: y={max_y_coord}, x={max_x_coord}")
        logger.info(f"Created {tiles_created} tiles with {overlap_percent}% overlap in {time.time() - start_time:.2f} seconds")
        return tiles_created
        
    except Exception as e:
        logger.error(f"Error tiling membrane image {image_path}: {str(e)}")
        return 0
