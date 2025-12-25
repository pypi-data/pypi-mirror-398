import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import logging
import time
import math
import traceback

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

def run_comprehensive_validation(analysis_folder, nuclei_parquet_path, print_callback=None):
    """
    Run comprehensive validation of nucleus-to-cell assignments
    
    Args:
        analysis_folder: Path to the analysis folder
        nuclei_parquet_path: Path to the nuclei center of mass parquet file
        print_callback: Optional callback for progress reporting
        
    Returns:
        Dictionary with validation results
    """
    try:
        start_time = time.time()
        
        if print_callback:
            print_callback(f"running comprehensive validation")
        
        # Setup validation output folder
        validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        os.makedirs(validation_dir, exist_ok=True)
        
        # Calculate paths
        cells_path = os.path.join(analysis_folder, "nucleus_centric_cells", "cells.parquet")
        
        if not os.path.exists(cells_path):
            logger.error(f"File not found: {cells_path}")
            return {"error": "Cell data not found"}
        
        # 1. Load cells.parquet from nucleus_centric_cells directory
        logger.info("Loading cells data...")
        validated_cells = pd.read_parquet(cells_path)
        logger.info(f"Loaded {len(validated_cells)} rows from {cells_path}")
        
        # 2. Load nuclei_center_of_mass.parquet
        if not os.path.exists(nuclei_parquet_path):
            logger.error(f"Could not find nuclei data at {nuclei_parquet_path}")
            return {"error": "Nuclei data not found"}
        
        logger.info(f"Loading {nuclei_parquet_path}...")
        nuclei_com = pd.read_parquet(nuclei_parquet_path)
        logger.info(f"Loaded {len(nuclei_com)} rows from nuclei_center_of_mass.parquet")
        
        # Verify nuclei_com structure and extract coordinates
        if 'id' not in nuclei_com.columns or 'x' not in nuclei_com.columns or 'y' not in nuclei_com.columns:
            logger.error(f"Unexpected nuclei_center_of_mass.parquet structure. Columns: {nuclei_com.columns.tolist()}")
            # Try alternative column names
            id_col = next((col for col in nuclei_com.columns if col.lower() in ('id', 'nuclei_id')), None)
            x_col = next((col for col in nuclei_com.columns if col.lower() in ('x', 'x_int')), None)
            y_col = next((col for col in nuclei_com.columns if col.lower() in ('y', 'y_int')), None)
            
            if id_col and x_col and y_col:
                logger.info(f"Using alternative column names: {id_col}, {x_col}, {y_col}")
                nuclei_com = nuclei_com.rename(columns={id_col: 'id', x_col: 'x', y_col: 'y'})
            else:
                logger.error("Could not identify required columns in nuclei data")
                return {"error": "Invalid nuclei data format"}
                
        # 3. Create cross_validation.parquet with unique cell_ids (without nuclei_id)
        logger.info("Creating cross_validation.parquet...")
        cross_validation = validated_cells.groupby('cell_id').first().reset_index()
        cross_validation = cross_validation.drop('nuclei_id', axis=1)
        cross_validation.to_parquet(os.path.join(validation_dir, 'cross_validation.parquet'))
        logger.info(f"Created cross_validation.parquet with {len(cross_validation)} unique cells")
        
        # Calculate zone size based on max cell area
        max_cell_area = cross_validation['mask_area'].max() if 'mask_area' in cross_validation.columns else 10000
        logger.info(f"Max cell area: {max_cell_area} pixels²")
        
        # Calculate the approximate "diameter" of the largest cell
        # Assuming cells are roughly circular: diameter = 2 * sqrt(area/?)
        approx_max_diameter = 2 * math.sqrt(max_cell_area / math.pi)
        
        # Use 3x the largest cell diameter as our zone size
        zone_size = int(3 * approx_max_diameter)
        logger.info(f"Using zone size: {zone_size} pixels (3x largest cell diameter)")
        
        # 4. Create nuclei_center_of_mass_leftout.parquet (copy of original)
        nuclei_com_leftout = nuclei_com.copy()
        
        # 5. Initialize data structures to track assignments
        nucleus_to_cells = {}  # Map nuclei to their containing cells
        cell_to_nuclei = {}    # Map cells to their contained nuclei
        
        # 5a. Calculate cell sizes and prepare for data-driven zone sizing
        logger.info("Calculating cell statistics for data-driven zone sizing...")
        
        if 'mask_area' in cross_validation.columns:
            # Calculate median and max cell area
            median_cell_area = cross_validation['mask_area'].median()
            max_cell_area = cross_validation['mask_area'].max()
            
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
        
        # 5b. Pre-calculate cell centers for grid assignments
        logger.info("Calculating cell centers...")
        cell_centers = []
        mask_coord_field = 'mask_coordinates' if 'mask_coordinates' in cross_validation.columns else None
        
        if mask_coord_field:
            for idx, cell in cross_validation.iterrows():
                mask = cell[mask_coord_field]
                
                # NumPy array-safe check
                if mask is not None and len(mask) > 0:
                    valid_mask = []
                    for c in mask:
                        if c is not None:
                            valid_mask.append(c)
                    
                    if valid_mask:
                        avg_x = np.mean([c['x'] for c in valid_mask])
                        avg_y = np.mean([c['y'] for c in valid_mask])
                        cell_centers.append((idx, avg_x, avg_y))
        else:
            # Fallback if we can't get mask coordinates
            logger.warning("mask_coordinates not available in cell data, skipping cell center calculation")
            return {"error": "Cannot validate without mask_coordinates"}
        
        # Create a DataFrame with cell centers
        cell_centers_df = pd.DataFrame(cell_centers, columns=['cell_idx', 'center_x', 'center_y'])
        
        # Create lookup from cell_idx to cell_id
        cell_idx_to_id = {idx: cross_validation.iloc[idx]['cell_id'] for idx in range(len(cross_validation))}
        
        # 6. Multi-pass search with progressive zone sizes
        logger.info("Starting multi-pass search with progressive zone sizes...")
        
        # Prepare for tracking unmatched nuclei 
        unmatched_nuclei_indices = list(range(len(nuclei_com)))
        total_nuclei = len(nuclei_com)
        
        # Define zone sizes based on cell statistics
        # Starting with median diameter and increasing up to 3x max diameter
        zone_sizes = [
            median_cell_diameter,                          # First pass: median cell size
            median_cell_diameter * 1.5,                    # Second pass: 1.5x median
            max_cell_diameter,                             # Third pass: max cell size
            max_cell_diameter * 2,                         # Fourth pass: 2x max
            max_cell_diameter * 3                          # Fifth pass: 3x max
        ]
        
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
            nuclei_subset = nuclei_com.iloc[unmatched_nuclei_indices].copy().reset_index(drop=True)
            nuclei_zones, get_nuclei_zone, _ = create_adaptive_zones(
                nuclei_subset, 'x', 'y', zone_size
            )
            
            # Track which nuclei are still unmatched after this pass
            still_unmatched = []
            newly_matched = 0
            
            # Process each unmatched nucleus
            for i, subset_idx in enumerate(unmatched_nuclei_indices):
                if i % 1000 == 0 and print_callback:
                    print_callback(f"validating nuclei, pass {pass_num}: {i}/{len(unmatched_nuclei_indices)}")
                
                # Get the original nucleus
                nucleus = nuclei_com.iloc[subset_idx]
                nuclei_id = nucleus['id']
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
                    cell = cross_validation.iloc[cell_idx]
                    cell_id = cell['cell_id']
                    mask_coordinates = cell[mask_coord_field]
                    
                    # Check if nucleus point is in this cell's mask
                    if is_point_in_mask_coordinates(x, y, mask_coordinates):
                        containing_cells.append(cell_id)
                        
                        # Update cell_to_nuclei mapping
                        if cell_id not in cell_to_nuclei:
                            cell_to_nuclei[cell_id] = []
                        cell_to_nuclei[cell_id].append(nuclei_id)
                
                # Store the results
                nucleus_to_cells[nuclei_id] = containing_cells
                
                # Check if this nucleus was matched to any cells
                if containing_cells:
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
            logger.info(f"Final pass: Checking {len(unmatched_nuclei_indices)} unmatched nuclei against random cells...")
            sample_size = min(500, len(cross_validation))
            
            newly_matched = 0
            for i, subset_idx in enumerate(unmatched_nuclei_indices):
                if i % 100 == 0 and print_callback:
                    print_callback(f"final validation pass: {i}/{len(unmatched_nuclei_indices)}")
                
                nucleus = nuclei_com.iloc[subset_idx]
                nuclei_id = nucleus['id']
                x, y = nucleus['x'], nucleus['y']
                
                # Get random cells to check
                random_indices = np.random.choice(len(cross_validation), sample_size, replace=False)
                
                containing_cells = []
                for rand_idx in random_indices:
                    cell = cross_validation.iloc[rand_idx]
                    cell_id = cell['cell_id']
                    mask_coordinates = cell[mask_coord_field]
                    
                    # Check if nucleus point is in this cell's mask
                    if is_point_in_mask_coordinates(x, y, mask_coordinates):
                        containing_cells.append(cell_id)
                        # Update cell_to_nuclei mapping
                        if cell_id not in cell_to_nuclei:
                            cell_to_nuclei[cell_id] = []
                        cell_to_nuclei[cell_id].append(nuclei_id)
                
                # Store the results (might be empty if no matches found)
                nucleus_to_cells[nuclei_id] = containing_cells
                
                if containing_cells:
                    newly_matched += 1
            
            matched_so_far = total_nuclei - (len(unmatched_nuclei_indices) - newly_matched)
            logger.info(f"Final pass results: {newly_matched} newly matched, "
                       f"{matched_so_far}/{total_nuclei} total matched ({matched_so_far/total_nuclei:.1%})")
        
        # 7. Create final_count DataFrame - cells with unique nuclei first
        logger.info("Creating final_count.parquet...")
        
        # Start with a properly initialized DataFrame
        final_count = pd.DataFrame({
            'nuclei_id': pd.Series(dtype='int64'),
            'cell_id': pd.Series(dtype='int64'),
            'mask_area': pd.Series(dtype='int64') if 'mask_area' in cross_validation.columns else pd.Series(dtype='float64'),
            'mask_coordinates': pd.Series(dtype='object')
        })
        
        # Identify nuclei that are in exactly one cell
        unique_cell_assignments = []
        
        for nuclei_id, cell_ids in nucleus_to_cells.items():
            if len(cell_ids) == 1:
                # This nucleus is in exactly one cell
                cell_id = cell_ids[0]
                cell_data = cross_validation[cross_validation['cell_id'] == cell_id].iloc[0]
                
                mask_area = cell_data['mask_area'] if 'mask_area' in cell_data else 0
                
                unique_cell_assignments.append({
                    'nuclei_id': nuclei_id,
                    'cell_id': cell_id,
                    'mask_area': mask_area,
                    'mask_coordinates': cell_data[mask_coord_field]
                })
        
        if unique_cell_assignments:
            # Create the DataFrame with all rows at once
            unique_assignments_df = pd.DataFrame(unique_cell_assignments)
            final_count = pd.concat([final_count, unique_assignments_df], ignore_index=True)
        
        # 8. Find ambiguous nuclei and cells
        logger.info("Checking for ambiguities...")
        
        # Find cells with ambiguous nuclei - MODIFIED for stricter ambiguity handling
        ambiguous_cells = set()
        ambiguity_count = 0
        for nuclei_id, cell_ids in nucleus_to_cells.items():
            if len(cell_ids) > 1:  # Nucleus links to multiple cells
                # Check if any of these cells are in final_count
                overlapping_cells = [cell_id for cell_id in cell_ids 
                                    if cell_id in final_count['cell_id'].values]
                if len(overlapping_cells) >= 1:  # CHANGED: Now >= 1 instead of > 1
                    # This nucleus creates ambiguity - even if only one cell is in final_count
                    ambiguous_cells.update(overlapping_cells)
                    ambiguity_count += 1
        
        # 9. Remove ambiguous cells from final_count
        if ambiguous_cells:
            logger.info(f"Removing {len(ambiguous_cells)} ambiguous cells from final_count (from {ambiguity_count} ambiguous nuclei)")
            
            # Find nuclei in these ambiguous cells
            nuclei_in_ambiguous_cells = set()
            for cell_id in ambiguous_cells:
                if cell_id in cell_to_nuclei:
                    nuclei_in_ambiguous_cells.update(cell_to_nuclei[cell_id])
            
            # Remove ambiguous cells
            final_count = final_count[~final_count['cell_id'].isin(ambiguous_cells)]
            
            # Ensure ambiguous nuclei are in leftout
            assigned_nuclei = set(final_count['nuclei_id'])
            nuclei_com_leftout = nuclei_com[~nuclei_com['id'].isin(assigned_nuclei)]
        else:
            # Just remove assigned nuclei from leftout
            assigned_nuclei = set(final_count['nuclei_id'])
            nuclei_com_leftout = nuclei_com[~nuclei_com['id'].isin(assigned_nuclei)]
        
        # 10. Save results
        final_count.to_parquet(os.path.join(validation_dir, 'final_count.parquet'))
        nuclei_com_leftout.to_parquet(os.path.join(validation_dir, 'nuclei_center_of_mass_leftout.parquet'))
        
        # 11. Summarize results
        elapsed_time = time.time() - start_time
        logger.info(f"\n--- SUMMARY (Completed in {elapsed_time:.2f} seconds) ---")
        logger.info(f"Total nuclei initially: {len(nuclei_com)}")
        logger.info(f"Nuclei assigned to cells: {len(final_count)}")
        logger.info(f"Nuclei not assigned: {len(nuclei_com_leftout)}")
        
        unique_assigned_cells = len(final_count['cell_id'].unique())
        logger.info(f"Unique cells with assigned nuclei: {unique_assigned_cells}")
        
        avg_area = 0
        if len(final_count) > 0 and 'mask_area' in final_count.columns:
            avg_area = final_count['mask_area'].mean()
            logger.info(f"Average mask area: {avg_area:.2f}")
        
        # Count cells with multiple nuclei
        multi_nuclei_cells = []
        avg_nuclei_per_cell = 0
        if not final_count.empty:
            cell_nuclei_counts = final_count.groupby('cell_id')['nuclei_id'].count()
            multi_nuclei_cells = cell_nuclei_counts[cell_nuclei_counts > 1]
            logger.info(f"Cells with multiple nuclei: {len(multi_nuclei_cells)}")
            
            if len(multi_nuclei_cells) > 0:
                avg_nuclei_per_cell = multi_nuclei_cells.mean()
                logger.info(f"Average nuclei per multi-nuclei cell: {avg_nuclei_per_cell:.2f}")
        
        logger.info("Assignment process complete!")
        
        if print_callback:
            print_callback(f"validation complete, {len(final_count)}/{len(nuclei_com)} nuclei assigned")
        
        # Return summary statistics
        return {
            "total_nuclei_count": len(nuclei_com),
            "assigned_nuclei_count": len(final_count),
            "unassigned_nuclei_count": len(nuclei_com_leftout),
            "multi_assigned_nuclei_count": ambiguity_count,
            "cells_with_multiple_nuclei": len(multi_nuclei_cells),
            "avg_nuclei_per_multi_nuclei_cell": float(avg_nuclei_per_cell),
            "avg_cell_area": float(avg_area),
            "elapsed_time": elapsed_time
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive validation: {str(e)}")
        logger.error(traceback.format_exc())
        if print_callback:
            print_callback(f"error during validation: {str(e)}")
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

def batch_comprehensive_validation(analysis_folders, nuclei_data_paths, print_callback=None):
    """
    Run comprehensive validation for all experiments.
    
    Args:
        analysis_folders: Dictionary mapping exp_name to analysis folder
        nuclei_data_paths: Dictionary mapping exp_name to nuclei data path
        print_callback: Optional function for printing progress
        
    Returns:
        Dictionary mapping exp_name to validation results
    """
    try:
        results = {}
        
        for exp_name, nuclei_parquet_path in nuclei_data_paths.items():
            if exp_name not in analysis_folders:
                logger.warning(f"No analysis folder found for {exp_name}, skipping")
                continue
                
            if not os.path.exists(nuclei_parquet_path):
                logger.warning(f"Nuclei data not found for {exp_name}: {nuclei_parquet_path}")
                continue
                
            # Set up analysis folder path
            analysis_folder = analysis_folders[exp_name]
            
            # Check for nucleus_centric_cells directory
            cells_dir = os.path.join(analysis_folder, "nucleus_centric_cells")
            if not os.path.exists(cells_dir):
                logger.warning(f"No nucleus_centric_cells directory found for {exp_name}")
                continue
            
            # Run validation for this experiment
            if print_callback:
                print_callback(f"validating cell-nuclei assignments for {exp_name}")
                
            exp_results = run_comprehensive_validation(
                analysis_folder,
                nuclei_parquet_path,
                print_callback
            )
            
            results[exp_name] = exp_results
            
        return results
        
    except Exception as e:
        logger.error(f"Error in batch comprehensive validation: {str(e)}")
        if print_callback:
            print_callback(f"error during batch validation: {str(e)}")
        return {"error": str(e)}
