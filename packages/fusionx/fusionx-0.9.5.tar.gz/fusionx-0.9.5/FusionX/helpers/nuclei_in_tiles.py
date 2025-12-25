import os
import logging
import numpy as np
import pandas as pd
from PIL import Image
import re
import time
import tifffile

logger = logging.getLogger(__name__)

def extract_tile_coordinates(tile_filename):
    """
    Extract y, x coordinates from a tile filename.
    
    Args:
        tile_filename: The filename in format 'tile_Y_X.png'
        
    Returns:
        Tuple of (y, x) coordinates or None if extraction fails
    """
    try:
        match = re.search(r'tile_(\d+)_(\d+)', tile_filename)
        if match:
            y, x = map(int, match.groups())
            return y, x
        return None
    except Exception as e:
        logger.error(f"Error extracting coordinates from {tile_filename}: {str(e)}")
        return None

def process_nuclei_in_tile(tile_path, nuclei_df, tile_size=1024, overlap_percent=50):
    """
    Process nuclei in a tile, identifying which nuclei are in which tile.
    
    Args:
        tile_path: Path to the tile image
        nuclei_df: DataFrame containing nuclei data with 'id', 'x', 'y' columns
        tile_size: Base size of tiles
        overlap_percent: Overlap percentage between tiles
        
    Returns:
        List of dictionaries containing nuclei information in this tile
    """
    try:
        # Extract tile coordinates from filename
        filename = os.path.basename(tile_path)
        coords = extract_tile_coordinates(filename)
        if coords is None:
            logger.error(f"Could not extract coordinates from {filename}")
            return []
            
        y_tile, x_tile = coords
        
        # Calculate step size and actual tile boundaries in the original image
        step = tile_size - int(tile_size * overlap_percent / 100)
        y_start = y_tile * step
        x_start = x_tile * step
        
        # Get tile dimensions
        img = Image.open(tile_path)
        width, height = img.size
        y_end = y_start + height
        x_end = x_start + width
        
        logger.debug(f"Tile {filename} position: ({y_start}:{y_end}, {x_start}:{x_end})")
        
        # Dump nuclei_df structure for debugging
        logger.debug(f"Nuclei DataFrame columns: {nuclei_df.columns.tolist()}")
        logger.debug(f"Nuclei DataFrame sample: {nuclei_df.iloc[0:2].to_dict('records')}")
        
        # Track nuclei found in this tile
        nuclei_in_tile = []
        
        # Process each nucleus
        for idx, nucleus in nuclei_df.iterrows():
            # Handle different DataFrame structures
            if 'x' in nuclei_df.columns and 'y' in nuclei_df.columns:
                # Direct coordinates
                nuclei_x = nucleus['x']
                nuclei_y = nucleus['y']
                nuclei_id = nucleus['id'] if 'id' in nuclei_df.columns else idx
            elif 'center_of_mass' in nuclei_df.columns:
                # Tuple coordinates
                center = nucleus['center_of_mass']
                # If center_of_mass is stored as a string "(x, y)", parse it
                if isinstance(center, str):
                    center = center.strip('()').split(',')
                    nuclei_x = float(center[0])
                    nuclei_y = float(center[1])
                else:
                    # Assuming it's a tuple or list
                    nuclei_x = float(center[0])
                    nuclei_y = float(center[1])
                nuclei_id = nucleus['id'] if 'id' in nuclei_df.columns else idx
            else:
                # Unknown format
                logger.error(f"Unrecognized nuclei data format in DataFrame")
                continue
            
            # Check if nucleus is in this tile
            if (nuclei_x >= x_start and nuclei_x < x_end and 
                nuclei_y >= y_start and nuclei_y < y_end):
                
                # Calculate relative position in the tile
                tile_x = int(nuclei_x - x_start)
                tile_y = int(nuclei_y - y_start)
                
                # Make sure coordinates are within bounds
                if (0 <= tile_x < width and 0 <= tile_y < height):
                    nuclei_in_tile.append({
                        'id': nuclei_id,
                        'global_x': nuclei_x,
                        'global_y': nuclei_y,
                        'tile_x': tile_x,
                        'tile_y': tile_y
                    })
        
        logger.info(f"Found {len(nuclei_in_tile)} nuclei in tile {filename}")
        return nuclei_in_tile
        
    except Exception as e:
        logger.error(f"Error processing nuclei in {tile_path}: {str(e)}", exc_info=True)
        return []

def process_all_tiles(tiles_dir, nuclei_parquet_path, output_dir):
    """
    Process all tiles in a directory, identifying nuclei in each tile
    but not creating mask files or nuclei_masks directory.
    
    Args:
        tiles_dir: Directory containing tile images
        nuclei_parquet_path: Path to the parquet file with nuclei data
        output_dir: Directory to save processed data (not used for saving files anymore)
        
    Returns:
        Number of tiles processed successfully
    """
    try:
        start_time = time.time()
        
        # Verify the nuclei data file exists
        if not os.path.exists(nuclei_parquet_path):
            logger.error(f"Nuclei data file not found: {nuclei_parquet_path}")
            return 0
            
        # Verify the tiles directory exists
        if not os.path.exists(tiles_dir):
            logger.error(f"Tiles directory not found: {tiles_dir}")
            return 0
        
        # Load nuclei data
        logger.info(f"Loading nuclei data from {nuclei_parquet_path}")
        nuclei_df = pd.read_parquet(nuclei_parquet_path)
        
        # Print the first few rows and columns to understand format
        logger.info(f"Nuclei DataFrame columns: {nuclei_df.columns.tolist()}")
        logger.debug(f"Nuclei DataFrame sample: {nuclei_df.head(3).to_dict('records')}")
        
        # Get all tile files
        tile_files = [f for f in os.listdir(tiles_dir) if f.startswith('tile_') and f.endswith('.png')]
        logger.info(f"Found {len(tile_files)} tiles to process")
        
        # Process each tile
        success_count = 0
        total_nuclei_processed = 0
        for tile_file in tile_files:
            tile_path = os.path.join(tiles_dir, tile_file)
            
            # Process nuclei in this tile (without creating mask files)
            nuclei_in_tile = process_nuclei_in_tile(tile_path, nuclei_df)
            
            if nuclei_in_tile:
                success_count += 1
                total_nuclei_processed += len(nuclei_in_tile)
        
        logger.info(f"Successfully processed {success_count}/{len(tile_files)} tiles with {total_nuclei_processed} nuclei in {time.time() - start_time:.2f} seconds")
        return success_count
        
    except Exception as e:
        logger.error(f"Error processing tiles: {str(e)}", exc_info=True)
        return 0
