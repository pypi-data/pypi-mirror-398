import os
import shutil
import logging

logger = logging.getLogger(__name__)

def clean_up_experiment_files(analysis_folders):
    results = {
        "parquet_files": 0,
        "nuclei_files": 0,
        "csv_files": 0,
        "subfolders_deleted": 0
    }
    
    current_working_dir = os.getcwd()
    
    for exp_name, analysis_folder in analysis_folders.items():
        validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        source_parquet = os.path.join(validation_dir, "cells_nuclei_count.parquet")
        target_parquet = os.path.join(analysis_folder, f"{exp_name}_cell_nuclei_count.parquet")
        
        if os.path.exists(source_parquet):
            try:
                shutil.copy2(source_parquet, target_parquet)
                logger.info(f"Copied and renamed parquet file for {exp_name}")
                results["parquet_files"] += 1
            except Exception as e:
                logger.error(f"Error copying parquet file for {exp_name}: {str(e)}")
        
        source_csv = os.path.join(validation_dir, f"{exp_name}_FusionX_report.csv")
        target_csv_pwd = os.path.join(current_working_dir, f"{exp_name}_FusionX_report.csv")
        
        if os.path.exists(source_csv):
            try:
                shutil.move(source_csv, target_csv_pwd)
                logger.info(f"Moved CSV report for {exp_name} to current working directory")
                results["csv_files"] += 1
            except Exception as e:
                logger.error(f"Error moving CSV report to current working directory for {exp_name}: {str(e)}")
        
        nuclei_dir = os.path.join(analysis_folder, "nuclei_segmentation")
        source_nuclei = os.path.join(nuclei_dir, "nuclei_center_of_mass.tif")
        target_nuclei = os.path.join(analysis_folder, f"{exp_name}_nuclei_instances_COM.tif")
        
        if os.path.exists(source_nuclei):
            try:
                shutil.copy2(source_nuclei, target_nuclei)
                logger.info(f"Copied and renamed nuclei file for {exp_name}")
                results["nuclei_files"] += 1
            except Exception as e:
                logger.error(f"Error copying nuclei file for {exp_name}: {str(e)}")
        
        for item in os.listdir(analysis_folder):
            item_path = os.path.join(analysis_folder, item)
            if os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)
                    logger.info(f"Deleted subfolder: {item_path}")
                    results["subfolders_deleted"] += 1
                except Exception as e:
                    logger.error(f"Error deleting subfolder {item_path}: {str(e)}")
    
    return results
