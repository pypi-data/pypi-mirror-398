import os
import logging
import numpy as np
import pandas as pd
from PIL import Image
import tifffile
import torch
import torch.nn.functional as F
import cv2
import time
import json
from pathlib import Path
from scipy.spatial import KDTree

# Set logger to only show INFO and above (no DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def mask_to_coordinates(mask, x_offset=0, y_offset=0):
    """
    Convert a binary mask to a list of all (x,y) coordinates where mask > 0 (all pixels in the mask).
    
    Args:
        mask: Binary mask array
        x_offset: Offset to add to x coordinates
        y_offset: Offset to add to y coordinates
        
    Returns:
        List of dictionaries with 'x' and 'y' keys for all pixels in the mask
    """
    y_indices, x_indices = np.where(mask > 0)
    # Add offsets to get global coordinates
    global_x = x_indices + x_offset
    global_y = y_indices + y_offset
    # Return as JSON-serializable list
    return [{'x': int(x), 'y': int(y)} for x, y in zip(global_x, global_y)]

def initialize_cellx_predictor():
    """Initialize SAM-based CellX predictor"""
    try:
        import torch
        from FusionX.segment_anything_custom.predictor import SamPredictor
        from FusionX.segment_anything_custom.build_sam import sam_model_registry
        
        # Only essential logging
        logger.info("Initializing CellX predictor")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Model is in ~/.cellx
        home_dir = os.path.expanduser("~")
        model_path = os.path.join(home_dir, ".cellx", "CellX.pth")
        
        if not os.path.exists(model_path):
            logger.error(f"CellX model not found at {model_path}")
            return None
        
        sam = sam_model_registry["vit_b"](checkpoint=model_path)
        sam.to(device=device)
        
        predictor = SamPredictor(sam)
        
        return predictor
        
    except Exception as e:
        logger.error(f"Error initializing CellX predictor: {str(e)}")
        return None

def run_inference_for_nucleus(predictor, image, y, x, scale_factors=None):
    """
    Run inference for a single nucleus prompt with pre-scaled image
    
    Args:
        predictor: The CellX predictor with image already set
        image: Original image (for dimensions reference)
        y, x: Coordinates in the original image space
        scale_factors: Optional tuple of (y_scale, x_scale) if image was pre-scaled
        
    Returns:
        Mask in original image dimensions and confidence score
    """
    try:
        # Scale the coordinates if needed
        if scale_factors:
            y_scale, x_scale = scale_factors
            scaled_y = int(y * y_scale)
            scaled_x = int(x * x_scale)
            return batch_cellx_inference(
                predictor, 
                image, 
                [(scaled_y, scaled_x)], 
                needs_scaling=False,  # Scaling already handled via scale_factors
                original_dims=True    # We'll need to scale the mask back to original dimensions
            )
        else:
            # No scaling needed
            return batch_cellx_inference(
                predictor, 
                image, 
                [(y, x)], 
                needs_scaling=False,
                original_dims=False
            )
    except Exception as e:
        logger.error(f"Error in single nucleus inference: {str(e)}")
        return None, None

def batch_cellx_inference(predictor, image, nuclei_coords, needs_scaling=False, original_dims=False):
    """
    Run inference with multiple nuclei points as prompts
    
    Args:
        predictor: The CellX predictor
        image: Original image for dimensions reference
        nuclei_coords: List of (y, x) coordinates
        needs_scaling: Whether coordinates need to be scaled (legacy parameter)
        original_dims: Whether to scale the mask back to original dimensions
        
    Returns:
        Mask in original image dimensions and confidence score
    """
    try:
        # Store original dimensions
        orig_height, orig_width = image.shape[:2]
        
        if needs_scaling:
            # Legacy code path - scale image and coordinates here
            scaled_image = cv2.resize(image, (1024, 1024), interpolation=cv2.INTER_LINEAR)
            
            # Scale nuclei coordinates
            y_scale = 1024 / orig_height
            x_scale = 1024 / orig_width
            
            # Convert to scaled (x, y) coordinates for SAM
            scaled_coords = []
            for y, x in nuclei_coords:
                scaled_y = int(y * y_scale)
                scaled_x = int(x * x_scale)
                scaled_coords.append((scaled_x, scaled_y))  # (x, y) format for SAM
                
            # Set the image if we're using the legacy code path
            predictor.set_image(scaled_image)
            
            # Convert to numpy array
            coords_array = np.array(scaled_coords)
        else:
            # No scaling needed, just convert to (x, y) format for SAM
            coords_array = np.array([(x, y) for y, x in nuclei_coords])
        
        # Convert to tensor format
        coords_torch = torch.tensor(coords_array[np.newaxis, :, :], 
                                  dtype=torch.float32).to(predictor.device)
        
        # Create labels (all 1's for positive points)
        labels_torch = torch.ones((1, len(nuclei_coords)), 
                                dtype=torch.long).to(predictor.device)
        
        # Create point prompt
        point_prompt = (coords_torch, labels_torch)
        
        # Get embeddings from prompt encoder
        sparse_embeddings, dense_embeddings = predictor.model.prompt_encoder(
            points=point_prompt,
            boxes=None,
            masks=None,
        )
        
        # Feed to mask decoder
        low_res_logits, score = predictor.model.mask_decoder(
            image_embeddings=predictor.features,
            image_pe=predictor.model.prompt_encoder.get_dense_pe(),
            sparse_prompt_embeddings=sparse_embeddings,
            dense_prompt_embeddings=dense_embeddings,
            multimask_output=False,
        )
        
        # Convert to probabilities
        low_res_probs = torch.sigmoid(low_res_logits)
        
        if needs_scaling or original_dims:
            # Upscale to 1024x1024 first
            pred_1024 = F.interpolate(
                low_res_probs,
                size=(1024, 1024),
                mode='bilinear',
                align_corners=False
            )
            
            # Get the mask at 1024x1024
            mask_1024 = np.uint8(pred_1024.detach().cpu().numpy().squeeze() > 0.9)
            
            # Process the mask
            mask_1024 = fix_binary_mask(mask_1024)
            
            # Resize back to original dimensions
            final_mask = cv2.resize(mask_1024, (orig_width, orig_height), interpolation=cv2.INTER_NEAREST)
        else:
            # For 1024x1024 images, just use the mask directly
            pred_1024 = F.interpolate(
                low_res_probs,
                size=(1024, 1024),
                mode='bilinear',
                align_corners=False
            )
            
            # Get the mask
            final_mask = np.uint8(pred_1024.detach().cpu().numpy().squeeze() > 0.9)
            
            # Process the mask
            final_mask = fix_binary_mask(final_mask)
        
        # Get confidence score
        confidence = round(score.item(), 3)
            
        return final_mask, confidence
    except Exception as e:
        logger.error(f"Error in batch CellX inference: {str(e)}")
        return None, None

def fix_binary_mask(seg, small_hole_size=10):
    """Process a binary segmentation mask to fix small holes"""
    try:
        binary = seg.astype(np.uint8)
        num_labels, labels = cv2.connectedComponents(binary)
        if num_labels > 1:
            largest_label = 1 + np.argmax([np.sum(labels == i) for i in range(1, num_labels)])
            largest_mask = (labels == largest_label).astype(np.uint8)
        else:
            largest_mask = binary
        kernel_size = 2 * small_hole_size + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        closed_mask = cv2.morphologyEx(largest_mask, cv2.MORPH_CLOSE, kernel)
        return closed_mask
    except Exception as e:
        logger.error(f"Error processing binary mask: {str(e)}")
        return seg

def extract_tile_coordinates(tile_filename):
    """Extract tile coordinates from filename (tile_Y_X.png)"""
    try:
        import re
        match = re.search(r'tile_(\d+)_(\d+)', tile_filename)
        if match:
            y, x = map(int, match.groups())
            return y, x
        return None
    except Exception as e:
        logger.error(f"Error extracting coordinates from {tile_filename}: {str(e)}")
        return None

def check_touches_edge(mask, margin=1):
    """Check if a mask touches the edge of the image"""
    height, width = mask.shape
    
    # Check each edge with the specified margin
    touches_left = np.any(mask[:, :margin])
    touches_top = np.any(mask[:margin, :])
    touches_right = np.any(mask[:, width-margin:])
    touches_bottom = np.any(mask[height-margin:, :])
    
    return {
        "left": touches_left,
        "top": touches_top,
        "right": touches_right,
        "bottom": touches_bottom,
        "any": touches_left or touches_top or touches_right or touches_bottom
    }

def find_nuclei_in_mask(mask, nuclei_df, x_offset, y_offset):
    """Find which nuclei are inside a mask"""
    nuclei_inside = []
    
    for _, nucleus in nuclei_df.iterrows():
        # Calculate local coordinates
        local_x = int(nucleus['x'] - x_offset)
        local_y = int(nucleus['y'] - y_offset)
        
        # Check if coordinates are within mask bounds
        if 0 <= local_y < mask.shape[0] and 0 <= local_x < mask.shape[1]:
            # Check if coordinate is within the mask
            if mask[local_y, local_x]:
                nuclei_inside.append(nucleus)
    
    return pd.DataFrame(nuclei_inside)

def calculate_iou(mask1, mask2):
    """Calculate Intersection over Union between two binary masks"""
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    if union == 0:
        return 0
    return intersection / union

def check_all_pairs_iou(masks_dict, threshold=0.4):
    """Check if IoU between all pairs of masks exceeds threshold"""
    mask_ids = list(masks_dict.keys())
    
    if len(mask_ids) <= 1:
        return True
    
    for i in range(len(mask_ids)):
        for j in range(i+1, len(mask_ids)):
            id1, id2 = mask_ids[i], mask_ids[j]
            iou = calculate_iou(masks_dict[id1], masks_dict[id2])
            
            if iou < threshold:
                return False
    
    return True

def is_at_image_edge(x_start, y_start, width, height, full_img_width, full_img_height):
    """Check if a tile is at the edge of the full image"""
    is_at_left = (x_start == 0)
    is_at_top = (y_start == 0)
    is_at_right = (x_start + width >= full_img_width)
    is_at_bottom = (y_start + height >= full_img_height)
    
    return {
        "left": is_at_left,
        "top": is_at_top,
        "right": is_at_right,
        "bottom": is_at_bottom,
        "any": is_at_left or is_at_top or is_at_right or is_at_bottom
    }

def process_tiles_with_nuclei_tracking(membrane_tiles_dir, nuclei_parquet_path, output_dir, 
                                      full_img_width, full_img_height, 
                                      tile_size=1024, overlap_percent=50):
    """
    Process all tiles with nucleus-centric tracking to handle cell boundaries.
    Does not save instance mask .tif files anymore.
    Minimal logging for efficiency.
    
    Args:
        membrane_tiles_dir: Directory containing membrane tile images
        nuclei_parquet_path: Path to the nucleus center of mass data
        output_dir: Directory to save output files (only dataframe, no tifs)
        full_img_width: Width of the original full image
        full_img_height: Height of the original full image
        tile_size: Size of tiles (default 1024)
        overlap_percent: Overlap percentage between tiles (default 50%)
        
    Returns:
        Path to the cells dataframe
    """
    try:
        start_time = time.time()
        # Minimal logging - only essential info
        logger.info("Starting nucleus-centric cell tracking")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Try to load existing cells dataframe if it exists
        cells_df_path = os.path.join(output_dir, "cells.parquet")
        if os.path.exists(cells_df_path):
            cells_df = pd.read_parquet(cells_df_path)
            processed_nuclei = set(cells_df["nuclei_id"].unique())
            # Get the next cell ID (max + 1)
            next_cell_id = cells_df["cell_id"].max() + 1 if len(cells_df) > 0 else 1
            
            # Single log message for setup
            logger.info(f"Found existing data: {len(processed_nuclei)} processed nuclei")
        else:
            # Create empty dataframe with simplified structure
            cells_df = pd.DataFrame({
                "nuclei_id": pd.Series(dtype=int),
                "cell_id": pd.Series(dtype=int),
                "mask_area": pd.Series(dtype=int),
                "mask_coordinates": pd.Series(dtype=object)
            })
            processed_nuclei = set()
            next_cell_id = 1
        
        # Load nuclei data
        nuclei_df = pd.read_parquet(nuclei_parquet_path)
        
        # Initialize CellX predictor
        predictor = initialize_cellx_predictor()
        if predictor is None:
            logger.error("Failed to initialize CellX predictor")
            return None
        
        # Calculate tile parameters
        step = tile_size - int(tile_size * overlap_percent / 100)
        
        # Get all tiles
        tile_files = [f for f in os.listdir(membrane_tiles_dir) if f.startswith('tile_') and f.endswith('.png')]
        
        # Single simple log for setup
        logger.info(f"Processing {len(tile_files)} tiles for {len(nuclei_df)} nuclei")
        
        # Keep track of total progress
        total_nuclei = len(nuclei_df)
        total_processed = len(processed_nuclei)
        save_interval = 20  # Save every 20 tiles with changes
        tiles_since_save = 0
        
        # Process each tile
        for tile_index, tile_file in enumerate(sorted(tile_files)):
            # Extract tile coordinates
            tile_coords = extract_tile_coordinates(tile_file)
            if tile_coords is None:
                continue
            
            y_tile, x_tile = tile_coords
            tile_id = f"{y_tile}_{x_tile}"
            
            # Calculate global coordinates of this tile
            x_start = x_tile * step
            y_start = y_tile * step
            
            # Load the tile image
            tile_path = os.path.join(membrane_tiles_dir, tile_file)
            tile_img = np.array(Image.open(tile_path))
            if len(tile_img.shape) == 2:  # Convert grayscale to RGB
                tile_img = np.stack([tile_img, tile_img, tile_img], axis=2)
            elif tile_img.shape[2] == 4:  # Convert RGBA to RGB
                tile_img = tile_img[:, :, :3]
                
            height, width = tile_img.shape[:2]
            
            # Check if this tile is at the edge of the full image
            tile_at_edge = is_at_image_edge(x_start, y_start, width, height, 
                                          full_img_width, full_img_height)
            
            # Create a mask to store instances for this tile (in memory only)
            tile_instance_mask = np.zeros((height, width), dtype=np.uint16)
            
            # Determine if scaling is needed and prepare the image for the predictor
            needs_scaling = (height != 1024 or width != 1024)
            
            # Calculate scaling factors and scale the image once if needed
            scale_factors = None
            if needs_scaling:
                y_scale = 1024 / height
                x_scale = 1024 / width
                scale_factors = (y_scale, x_scale)
                
                # Scale the image only once per tile
                scaled_tile_img = cv2.resize(tile_img, (1024, 1024), interpolation=cv2.INTER_LINEAR)
                predictor.set_image(scaled_tile_img)
            else:
                # No scaling needed
                predictor.set_image(tile_img)
            
            # Find nuclei in this tile
            nuclei_in_tile = nuclei_df[
                (nuclei_df['x'] >= x_start) & (nuclei_df['x'] < x_start + width) &
                (nuclei_df['y'] >= y_start) & (nuclei_df['y'] < y_start + height)
            ]
            
            # Skip if no nuclei in this tile
            if len(nuclei_in_tile) == 0:
                continue
            
            # Filter out already processed nuclei
            unprocessed_nuclei = nuclei_in_tile[~nuclei_in_tile['id'].isin(processed_nuclei)]
            
            # Skip if no unprocessed nuclei in this tile
            if len(unprocessed_nuclei) == 0:
                continue
                
            # Batch counter for this tile
            newly_processed_nuclei = 0
            
            # Process each unprocessed nucleus
            for _, nucleus in unprocessed_nuclei.iterrows():
                nuc_id = nucleus['id']
                
                # Calculate local coordinates within tile
                local_x = int(nucleus['x'] - x_start)
                local_y = int(nucleus['y'] - y_start)
                
                # Run inference for this nucleus (coordinates will be scaled inside if needed)
                mask, _ = run_inference_for_nucleus(
                    predictor, 
                    tile_img,
                    local_y, 
                    local_x, 
                    scale_factors
                )
                
                if mask is None:
                    continue
                
                # Check if mask touches tile edge
                edge_info = check_touches_edge(mask)
                
                # Determine if we should process this nucleus in this tile
                skip_nucleus = False
                
                # If mask touches a tile edge that's not at full image boundary, skip it
                if edge_info["any"]:
                    # Check each edge that the mask touches
                    if edge_info["left"] and not tile_at_edge["left"]:
                        skip_nucleus = True
                    if edge_info["top"] and not tile_at_edge["top"]:
                        skip_nucleus = True
                    if edge_info["right"] and not tile_at_edge["right"]:
                        skip_nucleus = True
                    if edge_info["bottom"] and not tile_at_edge["bottom"]:
                        skip_nucleus = True
                
                if skip_nucleus:
                    continue
                
                # Find all nuclei inside this mask
                nuclei_inside_mask = find_nuclei_in_mask(mask, nuclei_in_tile, x_start, y_start)
                
                if len(nuclei_inside_mask) == 0:
                    continue
                elif len(nuclei_inside_mask) == 1:
                    # Simple case: just one nucleus in the mask
                    # Get all pixel coordinates in the mask
                    mask_coords = mask_to_coordinates(mask, x_start, y_start)
                    
                    # Add to cells dataframe (simplified structure)
                    new_row = {
                        "nuclei_id": nuc_id,
                        "cell_id": next_cell_id,
                        "mask_area": np.sum(mask),
                        "mask_coordinates": mask_coords
                    }
                    cells_df = pd.concat([cells_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # Mark this nucleus as processed
                    processed_nuclei.add(nuc_id)
                    newly_processed_nuclei += 1
                    
                    # Add to tile instance mask (in memory only)
                    tile_instance_mask[mask > 0] = next_cell_id
                    
                    # Increment cell ID
                    next_cell_id += 1
                    
                else:
                    # Multiple nuclei case: potential syncytium
                    # Skip if any nucleus is already processed
                    already_processed = [n for n in nuclei_inside_mask['id'] if n in processed_nuclei]
                    if already_processed:
                        continue
                    
                    # Run inference for each nucleus individually
                    nuclei_masks = {}
                    for _, nuc in nuclei_inside_mask.iterrows():
                        n_id = nuc['id']
                        n_local_x = int(nuc['x'] - x_start)
                        n_local_y = int(nuc['y'] - y_start)
                        n_mask, _ = run_inference_for_nucleus(
                            predictor, 
                            tile_img, 
                            n_local_y, 
                            n_local_x, 
                            scale_factors
                        )
                        if n_mask is not None:
                            nuclei_masks[n_id] = n_mask
                    
                    # Calculate IoU between all pairs
                    high_iou = check_all_pairs_iou(nuclei_masks, threshold=0.4)
                    
                    if high_iou:
                        # This is a syncytium - run collective inference
                        # Collect local coordinates in the tile
                        local_coords = []
                        for _, nuc in nuclei_inside_mask.iterrows():
                            loc_y = int(nuc['y'] - y_start)
                            loc_x = int(nuc['x'] - x_start)
                            local_coords.append((loc_y, loc_x))
                        
                        # Scale the local coordinates if needed
                        if scale_factors:
                            y_scale, x_scale = scale_factors
                            scaled_coords = []
                            for y, x in local_coords:
                                scaled_y = int(y * y_scale)
                                scaled_x = int(x * x_scale)
                                scaled_coords.append((scaled_y, scaled_x))
                            # Run with already-scaled coordinates
                            collective_mask, _ = batch_cellx_inference(
                                predictor, 
                                tile_img, 
                                scaled_coords, 
                                needs_scaling=False,
                                original_dims=True
                            )
                        else:
                            # No scaling needed
                            collective_mask, _ = batch_cellx_inference(
                                predictor, 
                                tile_img, 
                                local_coords, 
                                needs_scaling=False,
                                original_dims=False
                            )
                        
                        if collective_mask is not None:
                            # Get all pixel coordinates in the collective mask
                            collective_coords = mask_to_coordinates(collective_mask, x_start, y_start)
                            
                            # Add all nuclei to the same cell
                            for _, nuc in nuclei_inside_mask.iterrows():
                                n_id = nuc['id']
                                
                                # Add to cells dataframe (simplified structure)
                                new_row = {
                                    "nuclei_id": n_id,
                                    "cell_id": next_cell_id,
                                    "mask_area": np.sum(collective_mask),
                                    "mask_coordinates": collective_coords
                                }
                                cells_df = pd.concat([cells_df, pd.DataFrame([new_row])], ignore_index=True)
                                
                                # Mark this nucleus as processed
                                processed_nuclei.add(n_id)
                                newly_processed_nuclei += 1
                            
                            # Add to tile instance mask (in memory only)
                            tile_instance_mask[collective_mask > 0] = next_cell_id
                            
                            # Increment cell ID
                            next_cell_id += 1
                    else:
                        # Not a syncytium - treat as separate cells
                        for _, nuc in nuclei_inside_mask.iterrows():
                            n_id = nuc['id']
                            if n_id in nuclei_masks:
                                n_mask = nuclei_masks[n_id]
                                n_local_x = int(nuc['x'] - x_start)
                                n_local_y = int(nuc['y'] - y_start)
                                
                                # Check if this individual mask touches tile edge
                                n_edge_info = check_touches_edge(n_mask)
                                if n_edge_info["any"] and not (
                                    (n_edge_info["left"] and tile_at_edge["left"]) or
                                    (n_edge_info["top"] and tile_at_edge["top"]) or
                                    (n_edge_info["right"] and tile_at_edge["right"]) or
                                    (n_edge_info["bottom"] and tile_at_edge["bottom"])
                                ):
                                    # Skip if mask touches tile edge but not image boundary
                                    continue
                                
                                # Get all pixel coordinates in this mask
                                mask_coords = mask_to_coordinates(n_mask, x_start, y_start)
                                
                                # Add to cells dataframe (simplified structure)
                                new_row = {
                                    "nuclei_id": n_id,
                                    "cell_id": next_cell_id,
                                    "mask_area": np.sum(n_mask),
                                    "mask_coordinates": mask_coords
                                }
                                cells_df = pd.concat([cells_df, pd.DataFrame([new_row])], ignore_index=True)
                                
                                # Mark this nucleus as processed
                                processed_nuclei.add(n_id)
                                newly_processed_nuclei += 1
                                
                                # Add to tile instance mask (in memory only)
                                tile_instance_mask[n_mask > 0] = next_cell_id
                                
                                # Increment cell ID
                                next_cell_id += 1
            
            # Update progress for console 
            total_processed = len(processed_nuclei)
            progress_percent = total_processed/total_nuclei*100
            
            if newly_processed_nuclei > 0:
                tiles_since_save += 1
                
                # Log only once per tile that had new processing
                logger.info(f"Tile {tile_id}: {newly_processed_nuclei} nuclei. Progress: {total_processed}/{total_nuclei} ({progress_percent:.1f}%)")
                
                # Save periodically rather than after every tile
                if tiles_since_save >= save_interval:
                    cells_df.to_parquet(cells_df_path)
                    logger.info(f"Saved progress after processing {save_interval} tiles")
                    tiles_since_save = 0
        
        # Final save to ensure all data is written
        if tiles_since_save > 0:
            cells_df.to_parquet(cells_df_path)
            logger.info(f"Final save after processing {tiles_since_save} additional tiles")
        
        # Final brief log
        elapsed_time = time.time() - start_time
        logger.info(f"Completed in {elapsed_time:.2f}s. Processed {total_processed}/{total_nuclei} nuclei ({progress_percent:.1f}%)")
        
        return cells_df_path
    
    except Exception as e:
        logger.error(f"Error in nucleus-centric cell tracking: {str(e)}")
        return None

def run_nucleus_centric_segmentation(experiment_name, nuclei_parquet_path, 
                                    membrane_image_path, output_dir,
                                    membrane_tiles_dir=None, print_callback=None):
    """
    Run the nucleus-centric segmentation pipeline for a single experiment.
    
    Args:
        experiment_name: Name of the experiment
        nuclei_parquet_path: Path to nuclei center of mass data
        membrane_image_path: Path to the full membrane image
        output_dir: Directory to save results
        membrane_tiles_dir: Optional directory with existing tiles
        print_callback: Optional callback for progress reporting
        
    Returns:
        Path to cells dataframe
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get full image dimensions
        with Image.open(membrane_image_path) as img:
            full_width, full_height = img.size
        
        # Create tiles if needed
        if membrane_tiles_dir is None or not os.path.exists(membrane_tiles_dir):
            if print_callback:
                print_callback(f"creating membrane tiles for {experiment_name}")
            
            membrane_tiles_dir = os.path.join(output_dir, "membrane_tiles")
            os.makedirs(membrane_tiles_dir, exist_ok=True)
            
            from FusionX.helpers.membrane_tiler import tile_membrane_image
            n_tiles = tile_membrane_image(membrane_image_path, membrane_tiles_dir)
            
            if print_callback:
                print_callback(f"created {n_tiles} membrane tiles for {experiment_name}")
        
        # Process all tiles with nucleus tracking
        if print_callback:
            print_callback(f"running nucleus-centric cell segmentation for {experiment_name}")
        
        cells_df_path = process_tiles_with_nuclei_tracking(
            membrane_tiles_dir,
            nuclei_parquet_path,
            output_dir,
            full_width,
            full_height
        )
        
        if cells_df_path:
            cells_df = pd.read_parquet(cells_df_path)
            cell_count = len(cells_df["cell_id"].unique())
            nuclei_count = len(cells_df["nuclei_id"].unique())
            
            if print_callback:
                print_callback(f"segmented {cell_count} cells containing {nuclei_count} nuclei for {experiment_name}")
        else:
            if print_callback:
                print_callback(f"failed to segment cells for {experiment_name}")
        
        return cells_df_path
    
    except Exception as e:
        logger.error(f"Error running nucleus-centric segmentation: {str(e)}")
        if print_callback:
            print_callback(f"error running nucleus-centric segmentation: {str(e)}")
        return None

def batch_process_experiments(experiments_dict, nuclei_data_paths, analysis_folders, print_callback=None):
    """
    Process all experiments with nucleus-centric cell segmentation.
    
    Args:
        experiments_dict: Dictionary of experiments
        nuclei_data_paths: Dictionary mapping exp_name to path of nuclei data
        analysis_folders: Dictionary of analysis folders
        print_callback: Optional function for printing progress
        
    Returns:
        Number of experiments successfully processed
    """
    try:
        success_count = 0
        
        for exp_name in nuclei_data_paths.keys():
            if exp_name not in analysis_folders:
                continue
            
            # Set up paths
            nuclei_parquet_path = nuclei_data_paths[exp_name]
            output_dir = os.path.join(analysis_folders[exp_name], "nucleus_centric_cells")
            
            # Find membrane image path
            membrane_image_path = os.path.join(analysis_folders[exp_name], f"{exp_name}_membrane.tif")
            
            # Check if paths exist
            if not os.path.exists(membrane_image_path) or not os.path.exists(nuclei_parquet_path):
                continue
            
            # Set up membrane tiles directory
            membrane_tiles_dir = os.path.join(analysis_folders[exp_name], "membrane_tiles")
            
            # Process this experiment
            result_path = run_nucleus_centric_segmentation(
                exp_name,
                nuclei_parquet_path,
                membrane_image_path,
                output_dir,
                membrane_tiles_dir,
                print_callback
            )
            
            if result_path:
                success_count += 1
            
        return success_count
    
    except Exception as e:
        logger.error(f"Error in batch processing experiments: {str(e)}")
        return 0
