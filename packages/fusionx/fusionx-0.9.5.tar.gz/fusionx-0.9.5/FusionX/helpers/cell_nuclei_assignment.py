import os
import logging
import pandas as pd
import numpy as np
import math
import time
from tqdm import tqdm
from collections import defaultdict

logger = logging.getLogger(__name__)

def is_point_in_mask_coordinates(x, y, mask_coordinates):
    """Check if point (x,y) is in mask coordinates - reverting to original reliable method"""
    if mask_coordinates is None or len(mask_coordinates) == 0:
        return False
    
    # Convert to integers once
    point_x, point_y = int(x), int(y)
    
    # Original reliable method
    for coord in mask_coordinates:
        if coord is not None and int(coord['x']) == point_x and int(coord['y']) == point_y:
            return True
    
    return False

def create_adaptive_zones(data_df, x_column, y_column, zone_size):
    """Create spatial zones with adaptive zone size
    
    Args:
        data_df: DataFrame with coordinate data
        x_column: Name of the x-coordinate column
        y_column: Name of the y-coordinate column
        zone_size: Size of each zone in pixels
        
    Returns:
        Dictionary mapping zone ids to data indices
    """
    # Find min and max coordinates
    min_x = math.floor(data_df[x_column].min())
    max_x = math.ceil(data_df[x_column].max())
    min_y = math.floor(data_df[y_column].min())
    max_y = math.ceil(data_df[y_column].max())
    
    # Calculate number of zones in each dimension
    num_zones_x = math.ceil((max_x - min_x) / zone_size)
    num_zones_y = math.ceil((max_y - min_y) / zone_size)
    
    logger.info(f"Creating spatial grid with {num_zones_x}x{num_zones_y} zones (size: {zone_size}px)")
    
    # Function to get zone ID for a point
    def get_zone_id(x, y):
        zone_x = min(num_zones_x - 1, max(0, math.floor((x - min_x) / zone_size)))
        zone_y = min(num_zones_y - 1, max(0, math.floor((y - min_y) / zone_size)))
        return (zone_x, zone_y)
    
    # Create zones dictionary
    zones = {}
    
    # Assign items to zones
    for idx, row in data_df.iterrows():
        x, y = row[x_column], row[y_column]
        zone = get_zone_id(x, y)
        
        if zone not in zones:
            zones[zone] = []
        
        zones[zone].append(idx)
    
    # Create function to get adjacent zones
    def get_adjacent_zones(zone_x, zone_y):
        adjacent = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                adj_x, adj_y = zone_x + dx, zone_y + dy
                if 0 <= adj_x < num_zones_x and 0 <= adj_y < num_zones_y:
                    adjacent.append((adj_x, adj_y))
        return adjacent
    
    return zones, get_zone_id, get_adjacent_zones

def process_cell_nuclei_assignments(exp_name, analysis_folder, print_callback=None):
    """
    Process nuclei-to-cell assignments using spatial grid search.
    
    Args:
        exp_name: Experiment name
        analysis_folder: Path to the analysis folder
        print_callback: Optional callback function for print messages
        
    Returns:
        Dictionary with statistics
    """
    try:
        start_time = time.time()
        
        if print_callback is None:
            print_callback = lambda msg: logger.info(msg)
        
        # Define paths
        validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        if not os.path.exists(validation_dir):
            logger.error(f"Segmentation validation directory not found for {exp_name}")
            return {"error": "Segmentation validation directory not found"}
        
        # Input file paths
        final_cell_count_path = os.path.join(validation_dir, "final_cell_count.parquet")
        nuclei_com_path = os.path.join(analysis_folder, "nuclei_segmentation", "nuclei_center_of_mass.parquet")
        
        # Output file paths
        cells_nuclei_count_path = os.path.join(validation_dir, "cells_nuclei_count.parquet")
        unassigned_nuclei_path = os.path.join(validation_dir, "unassigned_nuclei.parquet")
        
        # Check if files exist
        if not os.path.exists(final_cell_count_path):
            logger.error(f"Cell dataframe file not found: {final_cell_count_path}")
            return {"error": "final_cell_count.parquet not found"}
            
        if not os.path.exists(nuclei_com_path):
            logger.error(f"Nuclei dataframe file not found: {nuclei_com_path}")
            return {"error": "nuclei_center_of_mass.parquet not found"}
        
        print_callback(f"Processing nuclei-cell assignments for {exp_name}")
        
        # Step 1: Load and duplicate input files
        logger.info(f"Loading cell dataframe from {final_cell_count_path}...")
        final_cell_count_df = pd.read_parquet(final_cell_count_path)
        
        logger.info(f"Loading nuclei dataframe from {nuclei_com_path}...")
        nuclei_df = pd.read_parquet(nuclei_com_path)
        
        # Step 2: Make clean duplicates of the dataframes
        cell_df_dup = final_cell_count_df.copy()
        nuclei_dup = nuclei_df.copy()
        
        # Step 3: Verify nuclei_df structure and extract coordinates
        nuclei_id_col = 'id'
        nuclei_x_col = 'x'
        nuclei_y_col = 'y'
        
        if 'id' not in nuclei_dup.columns:
            # Try alternative column names
            nuclei_id_col = next((col for col in nuclei_dup.columns if col.lower() in ('id', 'nuclei_id')), None)
            
            if nuclei_id_col is None:
                logger.error("Could not identify nuclei ID column")
                return {"error": "Could not identify nuclei ID column"}
        
        if 'x' not in nuclei_dup.columns or 'y' not in nuclei_dup.columns:
            # Check for center_of_mass column
            if 'center_of_mass' in nuclei_dup.columns:
                logger.info("Found center_of_mass column, extracting x and y coordinates")
                
                # Extract x and y from center_of_mass tuples
                def extract_coords(com):
                    if isinstance(com, tuple):
                        return com[0], com[1]
                    elif isinstance(com, str):
                        # Handle string representation of tuples
                        try:
                            coords = eval(com)
                            return coords[0], coords[1]
                        except:
                            return None, None
                    return None, None
                
                # Extract coordinates
                coords = nuclei_dup['center_of_mass'].apply(extract_coords)
                nuclei_dup['x'] = coords.apply(lambda c: c[0])
                nuclei_dup['y'] = coords.apply(lambda c: c[1])
                
                # Handle any remaining None values
                nuclei_dup = nuclei_dup.dropna(subset=['x', 'y'])
            else:
                # Try alternative column names
                nuclei_x_col = next((col for col in nuclei_dup.columns if col.lower() in ('x', 'x_int')), None)
                nuclei_y_col = next((col for col in nuclei_dup.columns if col.lower() in ('y', 'y_int')), None)
                
                if nuclei_x_col is None or nuclei_y_col is None:
                    logger.error("Could not identify nuclei coordinate columns")
                    return {"error": "Could not identify nuclei coordinate columns"}
                    
                # Rename columns for consistency
                nuclei_dup = nuclei_dup.rename(columns={nuclei_x_col: 'x', nuclei_y_col: 'y'})
        
        # Step 4: Verify cells_df structure
        cell_id_col = 'cell_id'
        mask_coords_col = 'mask_coordinates'
        mask_area_col = 'mask_area'
        
        if 'cell_id' not in cell_df_dup.columns:
            logger.error("Could not identify cell_id column in final_cell_count.parquet")
            return {"error": "Could not identify cell_id column"}
            
        if 'mask_coordinates' not in cell_df_dup.columns:
            # Try alternative column names
            mask_coords_col = next((col for col in cell_df_dup.columns if 'mask' in col.lower() and 'coord' in col.lower()), None)
            
            if mask_coords_col is None:
                logger.error("Could not identify mask coordinates column in final_cell_count.parquet")
                return {"error": "Could not identify mask coordinates column"}
                
            # Rename column for consistency
            cell_df_dup = cell_df_dup.rename(columns={mask_coords_col: 'mask_coordinates'})
            mask_coords_col = 'mask_coordinates'
        
        if 'mask_area' not in cell_df_dup.columns:
            # Try alternative column names
            mask_area_col = next((col for col in cell_df_dup.columns if 'mask' in col.lower() and 'area' in col.lower()), None)
            
            if mask_area_col is None:
                logger.warning("mask_area column not found in final_cell_count.parquet, creating it from mask_coordinates")
                
                # Create mask_area column by counting coordinates
                cell_df_dup['mask_area'] = cell_df_dup['mask_coordinates'].apply(
                    lambda coords: len(coords) if coords is not None else 0
                )
                mask_area_col = 'mask_area'
            else:
                # Rename column for consistency
                cell_df_dup = cell_df_dup.rename(columns={mask_area_col: 'mask_area'})
                mask_area_col = 'mask_area'
        
        # Step 5: Remove nuclei_id from cell_df_dup as per instructions
        if 'nuclei_id' in cell_df_dup.columns:
            logger.info("Removing nuclei_id column from cell dataframe")
            cell_df_dup = cell_df_dup.drop('nuclei_id', axis=1)
        
        # Step 6: Create clean cell dataframe with unique cell_ids
        cells_clean = cell_df_dup.drop_duplicates(subset=['cell_id'])
        
        # Print some basic info
        logger.info(f"Loaded {len(cells_clean)} unique cells from final_cell_count.parquet")
        logger.info(f"Loaded {len(nuclei_dup)} nuclei from nuclei_center_of_mass.parquet")
        
        # Step 7: Calculate cell centers for spatial grid assignment
        cell_centers = []
        
        for idx, cell in cells_clean.iterrows():
            mask = cell['mask_coordinates']
            
            # Skip cells with no mask coordinates
            if mask is None or len(mask) == 0:
                continue
                
            # Filter out None values in mask coordinates
            valid_mask = [c for c in mask if c is not None]
            
            if valid_mask:
                avg_x = np.mean([c['x'] for c in valid_mask])
                avg_y = np.mean([c['y'] for c in valid_mask])
                cell_centers.append({
                    'cell_idx': idx,
                    'center_x': avg_x,
                    'center_y': avg_y,
                    'cell_id': cell['cell_id'],
                    'mask_area': cell['mask_area']
                })
        
        # Create a DataFrame with cell centers
        cell_centers_df = pd.DataFrame(cell_centers)
        
        # Calculate zone size based on cell statistics
        if 'mask_area' in cells_clean.columns:
            # Calculate median and max cell area
            median_cell_area = cells_clean['mask_area'].median()
            max_cell_area = cells_clean['mask_area'].max()
            
            # Calculate approximate diameters
            median_cell_diameter = 2 * math.sqrt(median_cell_area / math.pi)
            max_cell_diameter = 2 * math.sqrt(max_cell_area / math.pi)
            
            logger.info(f"Cell statistics:")
            logger.info(f"  Median cell area: {median_cell_area:.1f} pixels²")
            logger.info(f"  Median cell diameter: {median_cell_diameter:.1f} pixels")
            logger.info(f"  Maximum cell area: {max_cell_area:.1f} pixels²")
            logger.info(f"  Maximum cell diameter: {max_cell_diameter:.1f} pixels")
        else:
            # Fallback if mask_area isn't available
            logger.warning("mask_area not available in cell data, using default values")
            median_cell_diameter = 50
            max_cell_diameter = 150
        
        # Define zone sizes based on cell statistics
        # Starting with median diameter and increasing up to 3x max diameter
        zone_sizes = [
            median_cell_diameter,              # First pass: median cell size
            median_cell_diameter * 1.5,        # Second pass: 1.5x median
            max_cell_diameter,                 # Third pass: max cell size
            max_cell_diameter * 2,             # Fourth pass: 2x max
            max_cell_diameter * 3              # Fifth pass: 3x max
        ]
        
        # Dictionary to map nucleus_id to candidate cells (cell_id, area)
        nucleus_to_cells = defaultdict(list)
        
        # Track nuclei that need to be processed
        unmatched_nuclei_indices = list(range(len(nuclei_dup)))
        total_nuclei = len(nuclei_dup)
        
        # Multi-pass search with progressively larger zone sizes
        logger.info("Starting multi-pass spatial grid search...")
        
        for pass_num, zone_size in enumerate(zone_sizes, 1):
            logger.info(f"Pass {pass_num}: Using zone size = {zone_size:.1f} pixels...")
            
            # Skip if no unmatched nuclei remain
            if not unmatched_nuclei_indices:
                logger.info(f"All nuclei matched in previous passes, skipping pass {pass_num}")
                continue
                
            # Create cell zones using the current zone size
            cell_zones, get_cell_zone, get_adjacent_zones = create_adaptive_zones(
                cell_centers_df, 'center_x', 'center_y', zone_size
            )
            
            # Create nuclei zones using the current zone size
            nuclei_subset = nuclei_dup.iloc[unmatched_nuclei_indices].copy().reset_index(drop=True)
            nuclei_zones, get_nuclei_zone, _ = create_adaptive_zones(
                nuclei_subset, 'x', 'y', zone_size
            )
            
            # Track which nuclei are still unmatched after this pass
            still_unmatched = []
            newly_matched = 0
            
            # Process each unmatched nucleus with progress reporting
            for i, subset_idx in enumerate(unmatched_nuclei_indices):
                if i % 500 == 0:
                    print_callback(f"Processing nuclei ({i}/{len(unmatched_nuclei_indices)}) - pass {pass_num}")
                
                # Get the original nucleus
                nucleus = nuclei_dup.iloc[subset_idx]
                nucleus_id = nucleus[nuclei_id_col]
                x, y = nucleus['x'], nucleus['y']
                
                # Get the zone for this nucleus
                nucleus_zone = get_nuclei_zone(x, y)
                
                # Get all adjacent zones (including the current zone)
                relevant_zones = get_adjacent_zones(*nucleus_zone)
                
                # Collect cell indices from all relevant zones
                cell_indices_to_check = []
                for zone in relevant_zones:
                    if zone in cell_zones:
                        cell_indices_to_check.extend(cell_zones[zone])
                
                # Check this nucleus against cells in relevant zones
                containing_cells = []
                
                for cell_idx in cell_indices_to_check:
                    cell = cell_centers_df.iloc[cell_idx]
                    cell_id = cell['cell_id']
                    cell_area = cell['mask_area']
                    
                    # Get the cell data from cells_clean
                    cell_data = cells_clean[cells_clean['cell_id'] == cell_id]
                    
                    # Skip if cell not found (shouldn't happen)
                    if cell_data.empty:
                        continue
                        
                    mask_coordinates = cell_data.iloc[0]['mask_coordinates']
                    
                    # Check if nucleus point is in this cell's mask
                    if is_point_in_mask_coordinates(x, y, mask_coordinates):
                        containing_cells.append((cell_id, cell_area))
                
                # Store all cells containing this nucleus
                if containing_cells:
                    nucleus_to_cells[nucleus_id].extend(containing_cells)
                    newly_matched += 1
                else:
                    still_unmatched.append(subset_idx)
            
            # Update the list of unmatched nuclei for the next pass
            unmatched_nuclei_indices = still_unmatched
            matched_so_far = total_nuclei - len(unmatched_nuclei_indices)
            logger.info(f"Pass {pass_num} results: {newly_matched} newly matched, "
                       f"{matched_so_far}/{total_nuclei} total matched ({matched_so_far/total_nuclei:.1%})")
        
        # Final pass: For any remaining unmatched nuclei, use random sampling
        if unmatched_nuclei_indices:
            print_callback(f"Final pass: random sampling for {len(unmatched_nuclei_indices)} remaining nuclei")
            sample_size = min(500, len(cells_clean))
            
            newly_matched = 0
            for i, subset_idx in enumerate(unmatched_nuclei_indices):
                if i % 100 == 0 and i > 0:
                    print_callback(f"Random sampling: processed {i}/{len(unmatched_nuclei_indices)} nuclei")
                
                nucleus = nuclei_dup.iloc[subset_idx]
                nucleus_id = nucleus[nuclei_id_col]
                x, y = nucleus['x'], nucleus['y']
                
                # Get random cells to check
                random_indices = np.random.choice(len(cells_clean), sample_size, replace=False)
                
                containing_cells = []
                for rand_idx in random_indices:
                    cell = cells_clean.iloc[rand_idx]
                    cell_id = cell['cell_id']
                    cell_area = cell['mask_area']
                    mask_coordinates = cell['mask_coordinates']
                    
                    # Check if nucleus point is in this cell's mask
                    if is_point_in_mask_coordinates(x, y, mask_coordinates):
                        containing_cells.append((cell_id, cell_area))
                
                # Store all cells containing this nucleus
                if containing_cells:
                    nucleus_to_cells[nucleus_id].extend(containing_cells)
                    newly_matched += 1
            
            matched_so_far = total_nuclei - (len(unmatched_nuclei_indices) - newly_matched)
            logger.info(f"Final pass results: {newly_matched} newly matched, "
                       f"{matched_so_far}/{total_nuclei} total matched ({matched_so_far/total_nuclei:.1%})")
        
        # Now assign each nucleus to exactly one cell (the largest when multiple options exist)
        print_callback(f"Assigning each nucleus to a unique cell")
        
        # Dictionary to map cell_id to assigned nuclei
        cell_to_nuclei = defaultdict(list)
        
        # Count statistics
        nuclei_assigned = 0
        multi_cell_nuclei = 0
        unassigned_nuclei_ids = set(nuclei_dup[nuclei_id_col])
        
        for nucleus_id, containing_cells in nucleus_to_cells.items():
            # Remove duplicates from containing_cells by converting to a set of cell_ids, then back to list of tuples
            unique_cell_ids = set()
            unique_containing_cells = []
            
            for cell_id, area in containing_cells:
                if cell_id not in unique_cell_ids:
                    unique_cell_ids.add(cell_id)
                    unique_containing_cells.append((cell_id, area))
            
            if not unique_containing_cells:
                # This nucleus is not contained in any cell
                continue
                
            # Remove from unassigned set
            if nucleus_id in unassigned_nuclei_ids:
                unassigned_nuclei_ids.remove(nucleus_id)
                
            if len(unique_containing_cells) == 1:
                # This nucleus is in exactly one cell
                cell_id, _ = unique_containing_cells[0]
                cell_to_nuclei[cell_id].append(nucleus_id)
                nuclei_assigned += 1
            else:
                # This nucleus is in multiple cells, assign to the largest one
                multi_cell_nuclei += 1
                # Sort by area, largest first
                unique_containing_cells.sort(key=lambda x: x[1], reverse=True)  
                cell_id, _ = unique_containing_cells[0]  # Take the largest cell
                cell_to_nuclei[cell_id].append(nucleus_id)
                nuclei_assigned += 1
        
        # Create the final cells_nuclei_count dataframe
        print_callback(f"Creating final assignment dataframe")
        
        cells_nuclei_rows = []
        
        for cell_id, nuclei_ids in cell_to_nuclei.items():
            if not nuclei_ids:
                # Skip cells with no nuclei
                continue
                
            # Get the cell data from final_cell_count.parquet
            cell_data = cells_clean[cells_clean['cell_id'] == cell_id]
            
            # Skip if cell not found (shouldn't happen)
            if cell_data.empty:
                continue
                
            cell_data = cell_data.iloc[0]
            
            # Create a row for each nucleus in this cell
            for nucleus_id in nuclei_ids:
                cells_nuclei_rows.append({
                    'cell_id': cell_id,
                    'nuclei_id': nucleus_id,
                    'mask_area': cell_data['mask_area'],
                    'mask_coordinates': cell_data['mask_coordinates']
                })
        
        # Convert to dataframe
        cells_nuclei_count = pd.DataFrame(cells_nuclei_rows)
        
        # Create the unassigned_nuclei dataframe
        unassigned_nuclei_df = nuclei_dup[nuclei_dup[nuclei_id_col].isin(unassigned_nuclei_ids)]
        
        # Save the results
        print_callback(f"Saving results to {validation_dir}")
        cells_nuclei_count.to_parquet(cells_nuclei_count_path)
        unassigned_nuclei_df.to_parquet(unassigned_nuclei_path)
        
        # Count unique cells
        unique_cells = len(cells_nuclei_count['cell_id'].unique())
        
        # Count cells with multiple nuclei
        cell_nuclei_counts = cells_nuclei_count.groupby('cell_id')['nuclei_id'].nunique()
        multi_nuclei_cells = cell_nuclei_counts[cell_nuclei_counts > 1]
        
        # Calculate average nuclei per multi-nuclei cell
        avg_nuclei_per_multi_cell = multi_nuclei_cells.mean() if len(multi_nuclei_cells) > 0 else 0
        
        # Print summary
        elapsed_time = time.time() - start_time
        
        # Results dictionary
        results = {
            "experiment": exp_name,
            "total_nuclei": len(nuclei_dup),
            "assigned_nuclei": nuclei_assigned,
            "unassigned_nuclei": len(unassigned_nuclei_ids),
            "unique_cells": unique_cells,
            "multi_cell_nuclei": multi_cell_nuclei,
            "cells_with_multiple_nuclei": len(multi_nuclei_cells),
            "avg_nuclei_per_multi_cell": float(avg_nuclei_per_multi_cell),
            "elapsed_time": elapsed_time
        }
        
        # Final output message
        print_callback(f"Assignments for {exp_name}: {nuclei_assigned}/{len(nuclei_dup)} nuclei assigned ({nuclei_assigned/len(nuclei_dup)*100:.1f}%)")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in process_cell_nuclei_assignments: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e), "experiment": exp_name}

def batch_process_assignments(analysis_folders, print_callback=None):
    """
    Process cell-nuclei assignments for multiple experiments
    
    Args:
        analysis_folders: Dictionary mapping experiment names to analysis folder paths
        print_callback: Optional function for printing progress
        
    Returns:
        Dictionary with results for each experiment
    """
    results = {}
    
    for exp_name, analysis_folder in analysis_folders.items():
        validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        
        # Check if validation directory exists
        if not os.path.exists(validation_dir):
            logger.warning(f"Validation directory not found for {exp_name}, skipping")
            continue
            
        # Check for input files
        final_cell_count_path = os.path.join(validation_dir, "final_cell_count.parquet")
        nuclei_com_path = os.path.join(analysis_folder, "nuclei_segmentation", "nuclei_center_of_mass.parquet")
        
        if not os.path.exists(final_cell_count_path):
            logger.warning(f"final_cell_count.parquet not found for {exp_name}, skipping")
            continue
            
        if not os.path.exists(nuclei_com_path):
            logger.warning(f"nuclei_center_of_mass.parquet not found for {exp_name}, skipping")
            continue
        
        # Process this experiment
        if print_callback:
            print_callback(f"Processing cell-nuclei assignments for {exp_name}")
            
        exp_results = process_cell_nuclei_assignments(
            exp_name,
            analysis_folder,
            print_callback
        )
        
        results[exp_name] = exp_results
    
    return results
