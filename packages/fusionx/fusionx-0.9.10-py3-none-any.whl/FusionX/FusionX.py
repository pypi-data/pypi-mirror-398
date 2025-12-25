import os
import logging
import sys
import atexit
import time
from FusionX.helpers.logging_setup import setup_logging
from FusionX.helpers.file_handlers import find_experiment_files
from FusionX.helpers.image_handlers import create_analysis_folders, process_experiment_images
from FusionX.helpers.console_print import print_message, print_progress, finish_progress, show_cursor, hide_cursor, finalize
from FusionX.helpers.cellpose_inference import run_cellpose_inference
from FusionX.helpers.nuclei_analysis import analyze_nuclei_mask, calculate_center_of_mass
from FusionX.helpers.membrane_tiler import tile_membrane_image
from FusionX.helpers.nuclei_in_tiles import process_all_tiles
from FusionX.helpers.nucleus_centric_cellx import batch_process_experiments
from FusionX.helpers.validation import batch_comprehensive_validation
from FusionX.helpers.nuclei_recovery import batch_recover_unassigned_nuclei
from FusionX.helpers.cell_nuclei_assignment import batch_process_assignments
from FusionX.helpers.cell_nuclei_report import batch_create_cell_nuclei_reports
from FusionX.helpers.visualization import batch_visualize_experiments
from FusionX.helpers.clean_up import clean_up_experiment_files
import requests
from pathlib import Path

# Disable tqdm globally to prevent those progress bars
from functools import partialmethod
from tqdm import tqdm
# Monkey patch tqdm to prevent output
tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)




def save_cellx(url, local_filename, folder):

    hiden_folder_name = Path(os.path.join(os.path.expanduser('~'),folder))
    output_path = Path(os.path.join(hiden_folder_name,local_filename))
    if not output_path.exists():
        os.makedirs(hiden_folder_name, exist_ok=True)
        print_message(f"Starting to download CellX model from: {url}")
        try:
            # Send a GET request to the URL. We use stream=True to handle large files.
            with requests.get(url, stream=True) as r:
                # Raise an exception for bad status codes (4xx or 5xx)
                r.raise_for_status() 
                
                # Open the local file in binary write mode
                with open(output_path, 'wb') as f:
                    # Iterate over the response content in chunks
                    for chunk in r.iter_content(chunk_size=8192):
                        # Write the chunk to the local file
                        f.write(chunk)

            print_message(f"Download completed successfully. File saved as: {output_path}")

        except requests.exceptions.RequestException as e:
            print_message(f"An error occurred during the download: {e}")
        except Exception as e:
            print_message(f"An unexpected error occurred: {e}")
    else:
      print_message("CellX model is already downloaded, starting FusionX")
    


def silent_callback(message):
    logger = logging.getLogger(__name__)
    logger.debug(message)

def clear_console():
    os.system('clear' if os.name == 'posix' else 'cls')

def main():
    # Register finalize function to ensure cursor is restored
    atexit.register(finalize)
    
    clear_console()
    
    # Redirect stdout during imports to suppress any print statements
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    logger = setup_logging()
    
    # Restore stdout for our controlled messages
    sys.stdout = original_stdout
    
    try:
        # Hide cursor at the beginning
        hide_cursor()
        
        print_message("Welcome to FusionX")
        save_cellx("https://zenodo.org/records/17849583/files/CellX.pth", "CellX.pth", ".cellx")
        
        experiments = find_experiment_files()
        
        if not experiments:
            logger.error("No experiment files found.")
            show_cursor()  # Make sure to show cursor before exit
            return
        
        total_experiments = len(experiments)
        print_message(f"Number of experiment in this path: {total_experiments}")
        
        analysis_folders = create_analysis_folders(experiments)
        
        # Preprocessing - Show incremental progress
        processed_images = {}
        for idx, exp_name in enumerate(experiments.keys(), 1):
            # Update progress bar with current state
            print_progress(f"Preprocessing experiments: {idx}/{total_experiments}")
                
            exp_processed = process_experiment_images({exp_name: experiments[exp_name]}, 
                                                    {exp_name: analysis_folders[exp_name]})
            processed_images.update(exp_processed)
            
            # Small delay to make progress visible
            time.sleep(0.5)
        
        finish_progress()
        
        # Nuclei segmentation
        valid_experiments = [exp for exp in processed_images if 'nuclei' in processed_images[exp]]
        total_valid = len(valid_experiments)
        
        if total_valid == 0:
            logger.warning("No valid nuclei images to segment.")
            show_cursor()  # Make sure to show cursor before exit
            return
        
        segmented_masks = {}
        nuclei_data_paths = {}
            
        # Show incremental progress for nuclei segmentation
        for idx, exp_name in enumerate(valid_experiments, 1):
            # Update progress to show which experiment is being processed
            print_progress(f"Segmenting nuclei: {idx}/{total_valid}")
            
            segmentation_folder = os.path.join(analysis_folders[exp_name], "nuclei_segmentation")
            os.makedirs(segmentation_folder, exist_ok=True)
            
            nuclei_image = processed_images[exp_name]['nuclei']
            
            mask_path = run_cellpose_inference(nuclei_image, segmentation_folder)
            
            if mask_path:
                segmented_masks[exp_name] = mask_path
                nuclei_data_paths[exp_name] = os.path.join(segmentation_folder, 'nuclei_center_of_mass.parquet')
                
                # Calculate center of mass (silently)
                analysis_results = analyze_nuclei_mask(mask_path)
                if analysis_results:
                    calculate_center_of_mass(mask_path, segmentation_folder)
            
            # Add delay to make progress visible
            time.sleep(0.5)
        
        finish_progress()
        
        # Create membrane tiles (silently)
        for exp_name, files in processed_images.items():
            if 'membrane' in files:
                membrane_tiles_dir = os.path.join(analysis_folders[exp_name], "membrane_tiles")
                os.makedirs(membrane_tiles_dir, exist_ok=True)
                
                membrane_image = files['membrane']
                tile_membrane_image(membrane_image, membrane_tiles_dir)
        
        # Process nuclei in tiles (silently)
        for exp_name, nuclei_parquet_path in nuclei_data_paths.items():
            if exp_name in analysis_folders:
                membrane_tiles_dir = os.path.join(analysis_folders[exp_name], "membrane_tiles")
                
                if os.path.exists(membrane_tiles_dir) and os.path.exists(nuclei_parquet_path):
                    process_all_tiles(membrane_tiles_dir, nuclei_parquet_path, analysis_folders[exp_name])
        
        # Cell segmentation - Show incremental progress
        print_progress(f"Segmenting cells: 1/{total_valid}")
        
        # Define a counter-based callback for incremental progress
        cell_exp_counter = [0]  # Use a list for mutable reference
        
        def cell_progress_callback(message):
            # If the message indicates a new experiment
            if "segmented" in message and "cells" in message:
                cell_exp_counter[0] += 1
                idx = min(cell_exp_counter[0], total_valid)
                print_progress(f"Segmenting cells: {idx}/{total_valid}")
                time.sleep(0.5)  # Small delay to make progress visible
        
        batch_process_experiments(
            experiments,
            nuclei_data_paths,
            analysis_folders,
            cell_progress_callback
        )
        
        # Ensure the final state is shown
        print_progress(f"Segmenting cells: {total_valid}/{total_valid}")
        time.sleep(0.5)
        finish_progress()
        
        # Validation - Show incremental progress
        validation_exp_counter = [0]
        
        def validation_progress_callback(message):
            # If the message indicates a new experiment validation
            if "validating" in message.lower() or "validation complete" in message.lower():
                validation_exp_counter[0] += 1
                idx = min(validation_exp_counter[0], total_valid)
                print_progress(f"Validating segmentations: {idx}/{total_valid}")
                time.sleep(0.5)  # Small delay to make progress visible
        
        print_progress(f"Validating segmentations: 1/{total_valid}")
        
        batch_comprehensive_validation(
            analysis_folders,
            nuclei_data_paths,
            validation_progress_callback
        )
        
        # Ensure the final state is shown
        print_progress(f"Validating segmentations: {total_valid}/{total_valid}")
        time.sleep(0.5)
        finish_progress()
        
        # Nuclei recovery (silently)
        # Temporarily redirect stdout during this operation to suppress tqdm
        sys.stdout = open(os.devnull, 'w')
        
        batch_recover_unassigned_nuclei(
            analysis_folders,
            nuclei_data_paths,
            silent_callback,
            confidence_threshold=0.6
        )
        
        # Restore stdout
        sys.stdout = original_stdout
        
        # Cell-nuclei assignments (silently)
        # Temporarily redirect stdout during this operation to suppress tqdm
        sys.stdout = open(os.devnull, 'w')
        
        batch_process_assignments(
            analysis_folders,
            silent_callback
        )
        
        # Restore stdout
        sys.stdout = original_stdout
        
        # Export results - Show incremental progress
        export_exp_counter = [0]
        
        def export_progress_callback(message):
            if "creating" in message.lower() or "visualizations created" in message.lower():
                export_exp_counter[0] += 1
                idx = min(export_exp_counter[0], total_valid)
                print_progress(f"Exporting results: {idx}/{total_valid}")
                time.sleep(0.5)  # Small delay to make progress visible
        
        print_progress(f"Exporting results: 1/{total_valid}")
        
        batch_create_cell_nuclei_reports(
            analysis_folders,
            export_progress_callback
        )
        
        batch_visualize_experiments(
            analysis_folders,
            export_progress_callback
        )
        
        # Ensure the final state is shown
        print_progress(f"Exporting results: {total_valid}/{total_valid}")
        time.sleep(0.5)
        finish_progress()
        
        # Clean up
        print_message("Cleaning up")
        
        clean_up_experiment_files(analysis_folders)
        
        print_message("Thank you for using FusionX")
        
        # Show cursor again at the end
        show_cursor()
        
    except Exception as e:
        # Make sure stdout is restored in case of exception
        sys.stdout = original_stdout
        finish_progress()
        # Make sure cursor is shown even in case of error
        show_cursor()
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
