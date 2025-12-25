import os
import logging
import subprocess
import time

logger = logging.getLogger(__name__)

def run_cellpose_inference(nuclei_image_path, output_dir, diameter=0):
    """
    Run Cellpose inference on a nuclei image.
    
    Args:
        nuclei_image_path: Path to the input nuclei image
        output_dir: Directory to save the segmentation output
        diameter: Cell diameter parameter for Cellpose (0 for auto-detection)
        
    Returns:
        Path to the segmented mask file or None if failed
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Log the start of Cellpose inference
        logger.info(f"Starting Cellpose inference on {nuclei_image_path}")
        
        # Prepare the Cellpose command
        cmd = [
            "cellpose",
            "--image_path", nuclei_image_path,
            "--pretrained_model", "cyto3",
            "--save_tif",
            "--no_npy",
            "--use_gpu",
            "--diameter", str(diameter),
            "--savedir", output_dir
        ]
        
        # Record the start time for performance logging
        start_time = time.time()
        
        # Run Cellpose and capture all output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Capture stdout and stderr
        stdout, stderr = process.communicate()
        
        # Log all output from Cellpose to our log file
        if stdout:
            for line in stdout.splitlines():
                if line.strip():  # Skip empty lines
                    logger.info(f"Cellpose: {line.strip()}")
        
        # Log any errors
        if stderr:
            for line in stderr.splitlines():
                if line.strip():
                    logger.error(f"Cellpose error: {line.strip()}")
        
        # Check return code
        if process.returncode != 0:
            logger.error(f"Cellpose inference failed with return code {process.returncode}")
            return None
        
        # Calculate the time taken
        elapsed_time = time.time() - start_time
        logger.info(f"Cellpose inference completed in {elapsed_time:.2f} seconds")
        
        # Determine the output file path
        base_name = os.path.basename(nuclei_image_path)
        mask_filename = os.path.splitext(base_name)[0] + "_cp_masks.tif"
        mask_path = os.path.join(output_dir, mask_filename)
        
        # Verify that the output file exists
        if not os.path.exists(mask_path):
            logger.error(f"Cellpose output file not found: {mask_path}")
            return None
        
        logger.info(f"Segmentation saved to {mask_path}")
        return mask_path
        
    except Exception as e:
        logger.error(f"Error in Cellpose inference: {str(e)}")
        return None
