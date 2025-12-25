"""Data loading and download module for building energy analysis datasets.

.. module:: batem.core.dataloader

This module provides utilities for downloading and managing datasets from external
repositories, specifically designed for building energy analysis applications.
It supports downloading data from Zenodo repositories and organizing files
according to project configuration.

Functions
---------

.. autosummary::
   :toctree: generated/

   load_data

Key Features
------------

* Zenodo API integration for dataset discovery and download
* Automatic directory creation based on project configuration
* File existence checking to avoid redundant downloads
* Progress reporting during download operations
* Support for multiple file downloads from single records
* Integration with project configuration system (setup.ini)
* Error handling for network and API failures

The module is designed for building energy analysis, research data management,
and automated dataset acquisition for building energy modeling and simulation.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
import os
import requests
from .library import Setup


def load_data(zenodo_record_id: str, folder: str = 'data', skip_if_offline: bool = True) -> None:
    """Download datasets from a Zenodo record to the specified folder.

    This function downloads all files from a Zenodo record (identified by record ID)
    to a local directory. It automatically creates the target directory if it doesn't
    exist and skips files that are already present locally.

    :param zenodo_record_id: The Zenodo record ID to download from
    :type zenodo_record_id: str
    :param folder: The folder name in the project configuration to download to, defaults to 'data'
    :type folder: str, optional
    :param skip_if_offline: If True, skip Zenodo API call if network is unavailable and files exist locally, defaults to True
    :type skip_if_offline: bool, optional
    :raises Exception: If the Zenodo API request fails or returns an error status (unless skip_if_offline=True and files exist)
    :raises KeyError: If the specified folder is not found in the project configuration
    """
    output_dir_path = Setup.folder_path(folder)
    output_dir = str(output_dir_path)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Try to fetch record metadata from Zenodo API
    api_url = f"https://zenodo.org/api/records/{zenodo_record_id}"
    record = None
    try:
        response: requests.Response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            record = response.json()
            print(f"Found record: {record['metadata']['title']}")
        else:
            if skip_if_offline:
                print(f"Warning: Could not fetch Zenodo record (status {response.status_code}). Checking local files...")
            else:
                raise Exception(f"Failed to fetch record: {response.status_code} - {response.text}")
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        if skip_if_offline:
            print(f"Warning: Could not connect to Zenodo ({type(e).__name__}). Checking local files...")
        else:
            raise Exception(f"Failed to connect to Zenodo: {e}")

    # If we couldn't get record info and skip_if_offline is True, check if files exist locally
    if record is None:
        if skip_if_offline:
            # List existing files in the directory
            existing_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
            if existing_files:
                print(f"Zenodo unavailable, but found {len(existing_files)} existing file(s) in {output_dir}")
                print("Assuming files are complete. To force download, set skip_if_offline=False")
                return
            else:
                raise Exception(f"Cannot download from Zenodo (offline) and no local files found in {output_dir}")
        else:
            raise Exception("Failed to fetch record metadata from Zenodo")

    # Process files from the record
    files_to_download = []
    files_existing = []
    
    for file in record['files']:
        file_name = file['key']
        file_path = os.path.join(output_dir, file_name)
        
        if os.path.isfile(file_path):
            files_existing.append(file_name)
        else:
            files_to_download.append((file_name, file['links']['self']))

    # Report existing files
    if files_existing:
        print(f"Found {len(files_existing)} existing file(s) in {output_dir}:")
        for file_name in files_existing:
            print(f"  ✓ {file_name}")

    # Download missing files
    if files_to_download:
        print(f"Downloading {len(files_to_download)} missing file(s)...")
        for file_name, file_url in files_to_download:
            print(f"  Downloading {file_name}...")
            try:
                file_data = requests.get(file_url, timeout=300).content
                with open(os.path.join(output_dir, file_name), 'wb') as f:
                    f.write(file_data)
                print(f"  ✓ {file_name} downloaded")
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Failed to download {file_name}: {e}")
                raise Exception(f"Failed to download {file_name}: {e}")
    else:
        print(f"All files already present in folder: {output_dir}")
