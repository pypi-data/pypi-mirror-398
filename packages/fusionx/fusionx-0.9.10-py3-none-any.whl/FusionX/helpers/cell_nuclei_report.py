import os
import pandas as pd
import csv
import logging

logger = logging.getLogger(__name__)

def create_cell_nuclei_report(input_parquet_path, output_csv_path):
    """
    Create a CSV report from cells_nuclei_count.parquet.
    
    Args:
        input_parquet_path: Path to the cells_nuclei_count.parquet file
        output_csv_path: Path where the CSV report will be saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Reading parquet file from: {input_parquet_path}")
        df = pd.read_parquet(input_parquet_path)
        
        required_columns = ['cell_id', 'nuclei_id']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Required columns not found. Available columns: {df.columns.tolist()}")
            return False
        
        df['cell_id'] = df['cell_id'].astype(int)
        df['nuclei_id'] = df['nuclei_id'].astype(int)
        
        cell_data = {}
        nuclei_counts = {}
        
        grouped = df.groupby('cell_id')
        
        for cell_id, group in grouped:
            nuclei_ids = sorted([int(nid) for nid in group['nuclei_id'].tolist()])
            
            nuclei_ids_str = ','.join(str(nid) for nid in nuclei_ids)
            
            cell_data[int(cell_id)] = {
                'nuclei_ids': nuclei_ids_str,
                'nuclei_count': len(nuclei_ids)
            }
            
            nuclei_count = len(nuclei_ids)
            if nuclei_count not in nuclei_counts:
                nuclei_counts[nuclei_count] = {
                    'cell_count': 0,
                    'total_nuclei': 0
                }
            
            nuclei_counts[nuclei_count]['cell_count'] += 1
            nuclei_counts[nuclei_count]['total_nuclei'] += nuclei_count
        
        sorted_nuclei_counts = sorted(nuclei_counts.items())
        
        total_cells = sum(count_data['cell_count'] for _, count_data in sorted_nuclei_counts)
        total_nuclei = sum(count_data['total_nuclei'] for _, count_data in sorted_nuclei_counts)
        
        sorted_cell_data = sorted(cell_data.items())
        
        logger.info(f"Writing CSV report to: {output_csv_path}")
        with open(output_csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow([
                'nuclei_per_cell', 'cell_count', 'total_nuclei', '', '', 
                'cell_id', 'nuclei_ids', 'nuclei_count'
            ])
            
            row_count = max(len(sorted_nuclei_counts) + 1, len(sorted_cell_data))
            
            for row_idx in range(row_count):
                if row_idx < len(sorted_nuclei_counts):
                    nuclei_per_cell, count_data = sorted_nuclei_counts[row_idx]
                    summary_cols = [
                        int(nuclei_per_cell),
                        int(count_data['cell_count']),
                        int(count_data['total_nuclei'])
                    ]
                elif row_idx == len(sorted_nuclei_counts):
                    summary_cols = [
                        'TOTAL',
                        int(total_cells),
                        int(total_nuclei)
                    ]
                else:
                    summary_cols = ['', '', '']
                
                if row_idx < len(sorted_cell_data):
                    cell_id, data = sorted_cell_data[row_idx]
                    cell_cols = [
                        int(cell_id),
                        f'"{data["nuclei_ids"]}"',
                        int(data['nuclei_count'])
                    ]
                else:
                    cell_cols = ['', '', '']
                
                writer.writerow(summary_cols + ['', ''] + cell_cols)
        
        logger.info(f"Successfully created report at {output_csv_path}")
        
        logger.info("\nSummary of nuclei distribution:")
        
        logger.info(f"Total cells: {total_cells}")
        logger.info(f"Total nuclei: {total_nuclei}")
        
        for nuclei_count, count_data in sorted_nuclei_counts:
            percentage = (count_data['cell_count'] / total_cells) * 100
            logger.info(f"Cells with {nuclei_count} nuclei: {count_data['cell_count']} ({percentage:.1f}%)")
        
        return True, {
            "total_cells": total_cells,
            "total_nuclei": total_nuclei,
            "cells_by_nuclei_count": dict(sorted_nuclei_counts)
        }
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return False, {"error": str(e)}

def batch_create_cell_nuclei_reports(analysis_folders, print_callback=None):
    """
    Create cell nuclei reports for all experiments
    
    Args:
        analysis_folders: Dictionary mapping experiment names to analysis folder paths
        print_callback: Optional function for printing progress
        
    Returns:
        Dictionary with results for each experiment
    """
    results = {}
    
    if print_callback is None:
        print_callback = lambda msg: logger.info(msg)
    
    for exp_name, analysis_folder in analysis_folders.items():
        validation_dir = os.path.join(analysis_folder, "segmentation_validation")
        
        if not os.path.exists(validation_dir):
            logger.warning(f"Validation directory not found for {exp_name}, skipping")
            continue
            
        cells_nuclei_count_path = os.path.join(validation_dir, "cells_nuclei_count.parquet")
        
        if not os.path.exists(cells_nuclei_count_path):
            logger.warning(f"cells_nuclei_count.parquet not found for {exp_name}, skipping")
            continue
        
        output_csv_path = os.path.join(validation_dir, f"{exp_name}_FusionX_report.csv")
        
        print_callback(f"Creating cell nuclei report for {exp_name}")
            
        success, report_data = create_cell_nuclei_report(
            cells_nuclei_count_path,
            output_csv_path
        )
        
        if success:
            results[exp_name] = {
                "status": "success",
                "report_path": output_csv_path,
                **report_data
            }
            print_callback(f"Cell nuclei report created: {output_csv_path}")
        else:
            results[exp_name] = {
                "status": "error",
                "error": report_data.get("error", "Unknown error")
            }
            print_callback(f"Failed to create cell nuclei report for {exp_name}")
    
    return results
