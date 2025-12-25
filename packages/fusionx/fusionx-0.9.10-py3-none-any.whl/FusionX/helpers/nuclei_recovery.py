import os
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import cv2
from PIL import Image
import time
import gc
from tqdm import tqdm
from collections import defaultdict

logger = logging.getLogger(__name__)

def calculate_histogram_window(img_array, percentile_low=1, percentile_high=99):
    """
    Calculate min and max values for display windowing based on histogram percentiles.
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
            
        return min_val, max_val
        
    except Exception as e:
        logger.error(f"Error calculating histogram window: {str(e)}")
        return 0, 255  # Default full range

def apply_display_window(img_array, min_val, max_val):
    """
    Apply display windowing to an image for better visibility.
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

def load_and_normalize_image(image_path, global_min_val=None, global_max_val=None):
    """
    Load and properly normalize an image for CellX
    """
    try:
        # Open image
        image = cv2.imread(image_path)
        if image is None:
            # Try with PIL and convert
            pil_img = Image.open(image_path)
            image = np.array(pil_img)
            if len(image.shape) == 2:  # Grayscale
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Handle different color channels
        if len(image.shape) == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        
        # Calculate and apply histogram windowing if not already done
        if global_min_val is None or global_max_val is None:
            global_min_val, global_max_val = calculate_histogram_window(image)
        
        # Apply display windowing for better visibility
        normalized_image = apply_display_window(image, global_min_val, global_max_val)
        
        return normalized_image, global_min_val, global_max_val
        
    except Exception as e:
        logger.error(f"Error loading image {image_path}: {str(e)}")
        return None, None, None

def fix_binary_mask(seg, small_hole_size=10):
    """
    Process a binary segmentation mask to fix small holes
    """
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

def check_touches_edge(mask, margin=1):
    """
    Check if a mask touches the edge of the image
    """
    height, width = mask.shape
    
    # Check each edge
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

def is_at_image_edge(x_start, y_start, width, height, full_width, full_height):
    """
    Check if a crop is at the edge of the full image
    """
    is_at_left = (x_start == 0)
    is_at_top = (y_start == 0)
    is_at_right = (x_start + width >= full_width)
    is_at_bottom = (y_start + height >= full_height)
    
    return {
        "left": is_at_left,
        "top": is_at_top,
        "right": is_at_right,
        "bottom": is_at_bottom,
        "any": is_at_left or is_at_top or is_at_right or is_at_bottom
    }

def find_nuclei_in_crop(nuclei_com_df, x_start, y_start, width, height):
    """
    Find nuclei that fall within the crop region
    """
    # Calculate crop boundaries
    x_end = x_start + width
    y_end = y_start + height
    
    # Find nuclei within the crop
    nuclei_in_crop = nuclei_com_df[
        (nuclei_com_df['x'] >= x_start) & 
        (nuclei_com_df['x'] < x_end) & 
        (nuclei_com_df['y'] >= y_start) & 
        (nuclei_com_df['y'] < y_end)
    ]
    
    return nuclei_in_crop

def find_nuclei_in_mask(mask, nuclei_df, x_offset, y_offset):
    """
    Find nuclei inside a mask
    """
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
    
    return pd.DataFrame(nuclei_inside) if nuclei_inside else pd.DataFrame()

def crop_membrane_image(membrane_image_path, x, y, crop_size, membrane_width, membrane_height, 
                       global_min_val=None, global_max_val=None):
    """
    Crop the membrane image around the specified point
    Handle boundary conditions properly
    """
    try:
        # Convert to integers
        x, y = int(x), int(y)
        half_size = crop_size // 2
        
        # Calculate initial crop coordinates
        x_start = x - half_size
        y_start = y - half_size
        width = crop_size
        height = crop_size
        
        # Adjust if near boundaries
        if x_start < 0:
            x_start = 0
        if y_start < 0:
            y_start = 0
        if x_start + width > membrane_width:
            width = membrane_width - x_start
        if y_start + height > membrane_height:
            height = membrane_height - y_start
        
        # Load the full image
        img, new_min_val, new_max_val = load_and_normalize_image(
            membrane_image_path, global_min_val, global_max_val
        )
        if img is None:
            return None, None, None, None, None
            
        # Crop the image
        crop_img = img[y_start:y_start+height, x_start:x_start+width]
        
        # Calculate scale factors for CellX (which needs 1024x1024)
        y_scale = 1024 / height
        x_scale = 1024 / width
        
        # Return the crop and info
        return crop_img, (y_scale, x_scale), (x_start, y_start, width, height), new_min_val, new_max_val
        
    except Exception as e:
        logger.error(f"Error cropping membrane image: {str(e)}")
        return None, None, None, None, None

def calculate_iou(mask1, mask2):
    """
    Calculate Intersection over Union between two masks
    """
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    if union == 0:
        return 0
    return intersection / union

def check_all_pairs_iou(masks_dict, threshold=0.4):
    """
    Check if IoU between all pairs of masks exceeds threshold.
    """
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

def mask_to_coordinates(mask, x_offset=0, y_offset=0):
    """
    Convert binary mask to list of coordinates
    """
    # Find all non-zero coordinates in the mask
    y_indices, x_indices = np.where(mask > 0)
    
    # Add offsets to get global coordinates
    global_x = x_indices + x_offset
    global_y = y_indices + y_offset
    
    # Convert to list of dictionaries for the expected format
    return [{'x': int(x), 'y': int(y)} for x, y in zip(global_x, global_y)]

def initialize_cellx_predictor():
    """
    Initialize the CellX predictor
    """
    try:
        from FusionX.segment_anything_custom import SamPredictor, sam_model_registry
        
        logger.info("Initializing CellX predictor...")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        # Model is in ~/.cellx
        home_dir = os.path.expanduser("~")
        model_path = os.path.join(home_dir, ".cellx", "CellX.pth")
        
        if not os.path.exists(model_path):
            logger.error(f"CellX model not found at {model_path}")
            return None
        
        sam = sam_model_registry["vit_b"](checkpoint=model_path)
        sam.to(device=device)
        
        predictor = SamPredictor(sam)
        logger.info("CellX predictor initialized successfully")
        return predictor
        
    except ImportError:
        logger.error("Could not import segment_anything_custom. Make sure it's installed.")
        return None
    except Exception as e:
        logger.error(f"Error initializing CellX predictor: {str(e)}")
        return None

def run_inference_for_nucleus(predictor, image, y, x, scale_factors=None):
    """
    Run CellX inference for a single nucleus with improved handling
    """
    try:
        if scale_factors:
            y_scale, x_scale = scale_factors
            scaled_y = int(y * y_scale)
            scaled_x = int(x * x_scale)
            
            # Run inference with scaled coordinates
            coords_array = np.array([[(scaled_x, scaled_y)]])
        else:
            # No scaling needed, use coordinates directly
            coords_array = np.array([[(x, y)]])
        
        # Convert to tensor format
        coords_torch = torch.tensor(coords_array, dtype=torch.float32).to(predictor.device)
        
        # Create labels (all 1's for positive points)
        labels_torch = torch.ones((1, 1), dtype=torch.long).to(predictor.device)
        
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
        
        # Upscale to 1024x1024
        pred_1024 = F.interpolate(
            low_res_probs,
            size=(1024, 1024),
            mode='bilinear',
            align_corners=False
        )
        
        # Get the mask at 1024x1024
        mask_1024 = pred_1024.detach().cpu().numpy().squeeze() > 0.7
        mask_1024 = mask_1024.astype(np.uint8)
        
        # Process the mask
        mask_1024 = fix_binary_mask(mask_1024)
        
        # If original image is not 1024x1024, resize back to original dimensions
        orig_height, orig_width = image.shape[:2]
        if orig_height != 1024 or orig_width != 1024:
            final_mask = cv2.resize(mask_1024, (orig_width, orig_height), interpolation=cv2.INTER_NEAREST)
        else:
            final_mask = mask_1024
        
        # Get confidence score
        confidence = round(score.item(), 3)
        
        return final_mask, confidence
        
    except Exception as e:
        logger.error(f"Error in single nucleus inference: {str(e)}")
        return None, None

def batch_cellx_inference(predictor, image, nuclei_coords, needs_scaling=False):
    """
    Run inference with multiple nuclei points with improved implementation
    """
    try:
        # Store original dimensions
        orig_height, orig_width = image.shape[:2]
        
        if needs_scaling:
            # Scale the image
            scaled_image = cv2.resize(image, (1024, 1024), interpolation=cv2.INTER_LINEAR)
            
            # Scale coordinates
            y_scale = 1024 / orig_height
            x_scale = 1024 / orig_width
            
            scaled_coords = []
            for y, x in nuclei_coords:
                scaled_y = int(y * y_scale)
                scaled_x = int(x * x_scale)
                scaled_coords.append((scaled_x, scaled_y))  # (x, y) format for SAM
            
            # Set the image
            predictor.set_image(scaled_image)
            
            # Convert to numpy array
            coords_array = np.array([[coord for coord in scaled_coords]])
        else:
            # No scaling needed
            coords_array = np.array([[
                (x, y) for y, x in nuclei_coords
            ]])
            
            # Set the image if it's already 1024x1024
            if orig_height == 1024 and orig_width == 1024:
                predictor.set_image(image)
            else:
                # We still need to scale for CellX
                scaled_image = cv2.resize(image, (1024, 1024), interpolation=cv2.INTER_LINEAR)
                predictor.set_image(scaled_image)
        
        # Convert to tensor format
        coords_torch = torch.tensor(coords_array, dtype=torch.float32).to(predictor.device)
        
        # Create labels (all 1's for positive points)
        labels_torch = torch.ones((1, len(nuclei_coords)), dtype=torch.long).to(predictor.device)
        
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
        
        # Upscale to 1024x1024
        pred_1024 = F.interpolate(
            low_res_probs,
            size=(1024, 1024),
            mode='bilinear',
            align_corners=False
        )
        
        # Get the mask at 1024x1024
        mask_1024 = pred_1024.detach().cpu().numpy().squeeze() > 0.7
        mask_1024 = mask_1024.astype(np.uint8)
        
        # Process the mask
        mask_1024 = fix_binary_mask(mask_1024)
        
        # Resize back to original dimensions if needed
        if orig_height != 1024 or orig_width != 1024:
            final_mask = cv2.resize(mask_1024, (orig_width, orig_height), interpolation=cv2.INTER_NEAREST)
        else:
            final_mask = mask_1024
        
        # Get confidence score
        confidence = round(score.item(), 3)
        
        return final_mask, confidence
        
    except Exception as e:
        logger.error(f"Error in batch CellX inference: {str(e)}")
        return None, None

def process_unassigned_nucleus(nucleus_id, nucleus_x, nucleus_y, predictor, membrane_image_path, 
                              membrane_width, membrane_height, nuclei_com_df, min_val=None, max_val=None, 
                              confidence_threshold=0.6):
    """
    Process a single unassigned nucleus and return results if successful
    """
    try:
        logger.info(f"Processing unassigned nucleus {nucleus_id} at ({nucleus_x}, {nucleus_y})")
        
        # Start with initial crop size
        crop_size = 1024
        iteration = 0
        masks_touch_boundary = True
        max_iterations = 3
        result = None
        
        while masks_touch_boundary and iteration < max_iterations:
            # Increase crop size after first iteration
            if iteration > 0:
                crop_size = int(crop_size * 1.2)  # Increase by 20%
                logger.info(f"  Expanding crop to {crop_size}x{crop_size}")
            
            iteration += 1
            
            # Crop the membrane image
            crop_img, scale_factors, crop_coords, min_val, max_val = crop_membrane_image(
                membrane_image_path, nucleus_x, nucleus_y, crop_size, 
                membrane_width, membrane_height, min_val, max_val
            )
            
            if crop_img is None or crop_coords is None:
                logger.error(f"  Failed to crop image for nucleus {nucleus_id}")
                continue
            
            x_start, y_start, width, height = crop_coords
            
            # Find all nuclei in this crop
            nuclei_in_crop = find_nuclei_in_crop(nuclei_com_df, x_start, y_start, width, height)
            
            if len(nuclei_in_crop) == 0:
                logger.warning(f"  No nuclei found in crop for nucleus {nucleus_id}")
                continue
            
            # Check if crop is at image edge
            crop_at_edge = is_at_image_edge(x_start, y_start, width, height, membrane_width, membrane_height)
            
            # Run inference for the target nucleus
            local_y = int(nucleus_y - y_start)
            local_x = int(nucleus_x - x_start)
            
            # Scale the image for CellX if needed
            needs_scaling = (height != 1024 or width != 1024)
            if needs_scaling:
                # Scale once per crop
                scaled_crop = cv2.resize(crop_img, (1024, 1024), interpolation=cv2.INTER_LINEAR)
                predictor.set_image(scaled_crop)
            else:
                predictor.set_image(crop_img)
            
            # Run inference with the proper scaling
            mask, confidence = run_inference_for_nucleus(
                predictor, crop_img, local_y, local_x, scale_factors
            )
            
            if mask is None:
                logger.error(f"  Inference failed for nucleus {nucleus_id}")
                continue
            
            # Check if mask touches edge
            edge_info = check_touches_edge(mask)
            
            # If mask touches non-image boundary, expand crop and try again
            masks_touch_boundary = False
            if edge_info["any"]:
                masks_touch_boundary = (
                    (edge_info["left"] and not crop_at_edge["left"]) or
                    (edge_info["top"] and not crop_at_edge["top"]) or
                    (edge_info["right"] and not crop_at_edge["right"]) or
                    (edge_info["bottom"] and not crop_at_edge["bottom"])
                )
            
            if masks_touch_boundary:
                logger.info(f"  Mask touches non-image boundary, will expand crop")
                continue
            
            # Find nuclei inside this mask
            nuclei_in_mask = find_nuclei_in_mask(mask, nuclei_in_crop, x_start, y_start)
            
            if len(nuclei_in_mask) == 0:
                logger.warning(f"  No nuclei found inside mask for nucleus {nucleus_id}")
                continue
            
            # Check confidence threshold ONLY for single-nucleated cells
            if len(nuclei_in_mask) == 1 and confidence < confidence_threshold:
                logger.info(f"  Single-nucleated cell for nucleus {nucleus_id} has low confidence ({confidence:.3f} < {confidence_threshold})")
                return {'status': 'low_confidence', 'nucleus_id': nucleus_id}
            
            # Check syncytia case - multiple nuclei
            if len(nuclei_in_mask) > 1:
                logger.info(f"  Found {len(nuclei_in_mask)} nuclei in mask, checking for syncytium")
                
                # Run inference for each nucleus individually
                nuclei_masks = {}
                nuclei_confidences = {}
                for _, nuc in nuclei_in_mask.iterrows():
                    n_id = nuc['id']
                    n_local_y = int(nuc['y'] - y_start)
                    n_local_x = int(nuc['x'] - x_start)
                    
                    n_mask, n_confidence = run_inference_for_nucleus(
                        predictor, crop_img, n_local_y, n_local_x, scale_factors
                    )
                    
                    if n_mask is not None:
                        nuclei_masks[n_id] = n_mask
                        nuclei_confidences[n_id] = n_confidence
                
                # Check if this is a syncytium (high IoU between all masks)
                high_iou = check_all_pairs_iou(nuclei_masks, threshold=0.4)
                
                if high_iou:
                    logger.info(f"  Detected syncytium with {len(nuclei_in_mask)} nuclei")
                    
                    # Run collective inference with all nuclei
                    coords = []
                    for _, nuc in nuclei_in_mask.iterrows():
                        n_local_y = int(nuc['y'] - y_start)
                        n_local_x = int(nuc['x'] - x_start)
                        coords.append((n_local_y, n_local_x))
                    
                    collective_mask, collective_confidence = batch_cellx_inference(
                        predictor, crop_img, coords, needs_scaling
                    )
                    
                    if collective_mask is not None:
                        # Convert mask to coordinates
                        mask_coords = mask_to_coordinates(collective_mask, x_start, y_start)
                        
                        # Get all nuclei IDs
                        nuclei_ids = nuclei_in_mask['id'].tolist()
                        
                        # Return result
                        result = {
                            'status': 'success_syncytia',
                            'nuclei_ids': nuclei_ids,
                            'mask_area': np.sum(collective_mask),
                            'mask_coordinates': mask_coords,
                            'confidence': collective_confidence
                        }
                        break
                else:
                    logger.info(f"  Not a syncytium (IoU < 0.4), processing individually")
                    
                    # Process the main nucleus
                    if nucleus_id in nuclei_masks:
                        n_mask = nuclei_masks[nucleus_id]
                        n_confidence = nuclei_confidences[nucleus_id]
                        
                        # Check confidence threshold ONLY for single-nucleated cells
                        if n_confidence < confidence_threshold:
                            logger.info(f"  Single-nucleated cell for nucleus {nucleus_id} has low confidence ({n_confidence:.3f} < {confidence_threshold})")
                            return {'status': 'low_confidence', 'nucleus_id': nucleus_id}
                        
                        # Convert mask to coordinates
                        mask_coords = mask_to_coordinates(n_mask, x_start, y_start)
                        
                        # Return result
                        result = {
                            'status': 'success_single',
                            'nucleus_id': nucleus_id,
                            'mask_area': np.sum(n_mask),
                            'mask_coordinates': mask_coords,
                            'confidence': n_confidence
                        }
                        break
            else:
                # Simple case: just one nucleus in the mask
                logger.info(f"  Single nucleus in mask, confidence: {confidence:.3f}")
                
                # Convert mask to coordinates
                mask_coords = mask_to_coordinates(mask, x_start, y_start)
                
                # Return result
                result = {
                    'status': 'success_single',
                    'nucleus_id': nucleus_id,
                    'mask_area': np.sum(mask),
                    'mask_coordinates': mask_coords,
                    'confidence': confidence
                }
                break
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing nucleus {nucleus_id}: {str(e)}")
        return None

def batch_recover_unassigned_nuclei(analysis_folders, nuclei_data_paths, print_progress_fn=None, 
                                   max_nuclei_per_exp=None, confidence_threshold=0.6):
    """
    Batch process unassigned nuclei for multiple experiments
    
    Args:
        analysis_folders: Dictionary of experiment names to analysis folder paths
        nuclei_data_paths: Dictionary of experiment names to nuclei data paths
        print_progress_fn: Optional function for printing progress
        max_nuclei_per_exp: Maximum number of nuclei to process per experiment (for testing)
        confidence_threshold: Confidence threshold for single-nucleated cells (default: 0.6)
        
    Returns:
        Dictionary with results per experiment
    """
    results = {}
    stats = defaultdict(int)
    
    if print_progress_fn is None:
        print_progress_fn = lambda msg: logger.info(msg)
    
    # Initialize CellX predictor
    predictor = initialize_cellx_predictor()
    if predictor is None:
        logger.error("Failed to initialize CellX predictor, aborting nuclei recovery")
        return results
    
    for exp_name, analysis_folder in analysis_folders.items():
        # Skip if no nuclei data
        if exp_name not in nuclei_data_paths:
            logger.warning(f"No nuclei data for {exp_name}, skipping recovery")
            continue
        
        print_progress_fn(f"recovering unassigned nuclei for {exp_name}")
        
        # Define paths for segmentation validation folder
        segmentation_validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        
        # Check if folder exists
        if not os.path.exists(segmentation_validation_dir):
            logger.warning(f"Segmentation validation directory not found for {exp_name}, skipping recovery")
            continue
        
        # Define paths for input files
        nuclei_leftout_path = os.path.join(segmentation_validation_dir, "nuclei_center_of_mass_leftout.parquet")
        final_count_path = os.path.join(segmentation_validation_dir, "final_count.parquet")
        
        # Check if files exist
        if not os.path.exists(nuclei_leftout_path) or not os.path.exists(final_count_path):
            logger.warning(f"Missing input files for {exp_name}, skipping recovery")
            continue
        
        # Define output files
        nuclei_leftout_final_path = os.path.join(segmentation_validation_dir, "nuclei_center_of_mass_leftout_final.parquet")
        final_cell_count_path = os.path.join(segmentation_validation_dir, "final_cell_count.parquet")
        
        # Define membrane image path
        membrane_image_path = os.path.join(analysis_folder, f"{exp_name}_membrane.tif")
        if not os.path.exists(membrane_image_path):
            # Try alternate naming
            membrane_image_path = os.path.join(analysis_folder, "membrane.tif")
            if not os.path.exists(membrane_image_path):
                logger.warning(f"Membrane image not found for {exp_name}, skipping recovery")
                continue
        
        # Load dataframes
        try:
            nuclei_leftout_df = pd.read_parquet(nuclei_leftout_path)
            final_count_df = pd.read_parquet(final_count_path)
            nuclei_com_df = pd.read_parquet(nuclei_data_paths[exp_name])
            
            # Make copies for output
            nuclei_leftout_final_df = nuclei_leftout_df.copy()
            final_cell_count_df = final_count_df.copy()
            
            # Load membrane image dimensions
            with Image.open(membrane_image_path) as img:
                membrane_width, membrane_height = img.size
            
            # Track stats for this experiment
            exp_stats = {
                "total_unassigned_initial": len(nuclei_leftout_df),
                "total_newly_assigned": 0,
                "low_confidence_discarded": 0,
                "recovered_syncytia": 0
            }
            
            # Initialize tracking
            successfully_processed_nuclei_ids = []
            low_confidence_nuclei_ids = []
            min_val = None
            max_val = None
            
            # Limit for testing if needed
            if max_nuclei_per_exp is not None:
                nuclei_to_process = nuclei_leftout_df.head(max_nuclei_per_exp)
            else:
                nuclei_to_process = nuclei_leftout_df
            
            # Process each nucleus
            for _, nucleus in tqdm(nuclei_to_process.iterrows(), 
                                  desc=f"Processing nuclei for {exp_name}",
                                  total=len(nuclei_to_process)):
                
                nucleus_id = nucleus['id']
                
                # Extract x, y coordinates
                if isinstance(nucleus['x'], (int, float)):
                    x, y = nucleus['x'], nucleus['y']
                else:
                    # Handle center_of_mass format
                    if 'center_of_mass' in nucleus.index:
                        if isinstance(nucleus['center_of_mass'], tuple):
                            x, y = nucleus['center_of_mass']
                        else:
                            x, y = eval(nucleus['center_of_mass'])
                    else:
                        logger.warning(f"Cannot determine coordinates for nucleus {nucleus_id}, skipping")
                        continue
                
                # Process the nucleus
                result = process_unassigned_nucleus(
                    nucleus_id, x, y, predictor, membrane_image_path,
                    membrane_width, membrane_height, nuclei_com_df, 
                    min_val, max_val, confidence_threshold
                )
                
                if result is None:
                    continue
                
                # Handle the result
                if result['status'] == 'low_confidence':
                    low_confidence_nuclei_ids.append(nucleus_id)
                    exp_stats["low_confidence_discarded"] += 1
                
                elif result['status'] == 'success_syncytia':
                    # Get all nuclei IDs
                    nuclei_ids = result['nuclei_ids']
                    
                    # Check if any of these nuclei are already assigned
                    already_assigned = final_cell_count_df[
                        final_cell_count_df['nuclei_id'].isin(nuclei_ids)
                    ]
                    
                    if not already_assigned.empty:
                        # Remove existing assignments
                        logger.info(f"  Removing {len(already_assigned)} existing assignments")
                        final_cell_count_df = final_cell_count_df[
                            ~final_cell_count_df['nuclei_id'].isin(nuclei_ids)
                        ]
                    
                    # Generate new cell ID
                    new_cell_id = final_cell_count_df['cell_id'].max() + 1 if not final_cell_count_df.empty else 1
                    
                    # Add all nuclei to this cell
                    new_rows = []
                    for nuc_id in nuclei_ids:
                        new_rows.append({
                            "nuclei_id": nuc_id,
                            "cell_id": new_cell_id,
                            "mask_area": result['mask_area'],
                            "mask_coordinates": result['mask_coordinates']
                        })
                        # Mark this ID as successfully processed
                        if nuc_id not in successfully_processed_nuclei_ids:
                            successfully_processed_nuclei_ids.append(nuc_id)
                    
                    # Add to final count
                    final_cell_count_df = pd.concat([
                        final_cell_count_df, 
                        pd.DataFrame(new_rows)
                    ], ignore_index=True)
                    
                    # Update stats
                    exp_stats["total_newly_assigned"] += len(nuclei_ids)
                    exp_stats["recovered_syncytia"] += 1
                
                elif result['status'] == 'success_single':
                    # Check if already assigned
                    already_assigned = final_cell_count_df[
                        final_cell_count_df['nuclei_id'] == result['nucleus_id']
                    ]
                    
                    if not already_assigned.empty:
                        # Remove existing assignment
                        logger.info(f"  Removing existing assignment for nucleus {result['nucleus_id']}")
                        final_cell_count_df = final_cell_count_df[
                            final_cell_count_df['nuclei_id'] != result['nucleus_id']
                        ]
                    
                    # Generate new cell ID
                    new_cell_id = final_cell_count_df['cell_id'].max() + 1 if not final_cell_count_df.empty else 1
                    
                    # Add to final count
                    new_row = {
                        "nuclei_id": result['nucleus_id'],
                        "cell_id": new_cell_id,
                        "mask_area": result['mask_area'],
                        "mask_coordinates": result['mask_coordinates']
                    }
                    
                    final_cell_count_df = pd.concat([
                        final_cell_count_df, 
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                    
                    # Mark as successfully processed
                    successfully_processed_nuclei_ids.append(result['nucleus_id'])
                    
                    # Update stats
                    exp_stats["total_newly_assigned"] += 1
            
            # Update leftout dataframe by removing successfully processed nuclei
            successfully_processed_ids = set(successfully_processed_nuclei_ids)
            nuclei_leftout_final_df = nuclei_leftout_final_df[
                ~nuclei_leftout_final_df['id'].isin(successfully_processed_ids)
            ]
            
            # Save results
            nuclei_leftout_final_df.to_parquet(nuclei_leftout_final_path)
            final_cell_count_df.to_parquet(final_cell_count_path)
            
            # Update stats
            exp_stats["total_still_unassigned"] = len(nuclei_leftout_final_df)
            results[exp_name] = exp_stats
            
            # Update global stats
            for key, value in exp_stats.items():
                stats[key] += value
            
            logger.info(f"Nuclei recovery for {exp_name} complete:")
            logger.info(f"  Initial unassigned: {exp_stats['total_unassigned_initial']}")
            logger.info(f"  Newly assigned: {exp_stats['total_newly_assigned']}")
            logger.info(f"  Low confidence: {exp_stats['low_confidence_discarded']}")
            logger.info(f"  Still unassigned: {exp_stats['total_still_unassigned']}")
            logger.info(f"  Recovered syncytia: {exp_stats['recovered_syncytia']}")
            
        except Exception as e:
            logger.error(f"Error processing experiment {exp_name}: {str(e)}")
            results[exp_name] = {"error": str(e)}
    
    # Log overall stats
    logger.info("Completed nuclei recovery across all experiments:")
    logger.info(f"  Total initial unassigned: {stats['total_unassigned_initial']}")
    logger.info(f"  Total newly assigned: {stats['total_newly_assigned']}")
    logger.info(f"  Total low confidence: {stats['low_confidence_discarded']}")
    logger.info(f"  Total recovered syncytia: {stats['recovered_syncytia']}")
    
    # Clean up GPU memory
    logger.info("Cleaning up GPU resources...")
    try:
        # Delete the predictor to free up its resources
        if predictor is not None:
            del predictor.model
            del predictor
        
        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("GPU memory cleanup completed")
    except Exception as e:
        logger.warning(f"Error during GPU memory cleanup: {str(e)}")
    
    return results
