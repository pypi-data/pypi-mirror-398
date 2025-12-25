
import requests
from pathlib import Path
import os
from FusionX.helpers.console_print import print_message

def download_cellx(url,output_path, existing_size, headers):
    with requests.get(url, headers=headers, stream=True, timeout=20) as r:
        if r.status_code == 206 or r.status_code == 200:
            with open(output_path, "ab") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            print_message(f"Download completed successfully. File saved as: {output_path}")
        else:
            print_message(f"Server error: {r.status_code}")
            print_message(f"Try to delete {output_path} if it exist and try running FusionX again")



def save_cellx(url, local_filename, folder):
    hiden_folder_name = Path(os.path.join(os.path.expanduser('~'),folder))
    output_path = Path(os.path.join(hiden_folder_name,local_filename))
    if not output_path.exists():
        os.makedirs(hiden_folder_name, exist_ok=True)
        print_message(f"Starting to download CellX model from: {url}")
        try:
          existing_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
          headers = {"Range": f"bytes={existing_size}-"}
          download_cellx(url,output_path, existing_size, headers)

        except requests.exceptions.ConnectionError as e:
            print_message(f"An error occurred during the download: {e}")
            print_message("trying to resume download")
            download_cellx(url,output_path, existing_size, headers)
            
        except Exception as e:
            print_message(f"An unexpected error occurred: {e}")
            print_message(f"Try to delete {output_path} if it exist and try running FusionX again")
    else:
      print_message("CellX model is already downloaded, starting FusionX")