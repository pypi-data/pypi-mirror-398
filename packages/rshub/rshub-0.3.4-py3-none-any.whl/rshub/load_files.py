import io
import json
import logging
import os
import tempfile

import h5py
import numpy as np
import requests
from scipy.io import loadmat
from tqdm import tqdm

from urllib.parse import urljoin
from .check_authenticity import return_task_path
from .output_manager import FunctionOutputManager


# This file contains the following functions that can be called by users:
# 1. load_error_message
# 2. list_files
# 3. load_outputs

class load_file:
    # def __init__(self, token, project_name, task_name, fGHz = '1.41', scenario_flag = 'snow', 
    #              algorithm = 'qms',output_var = 'tb', inc_ang = 40, var = None, filename = None,
    #              size_threshold_mb=50, chunk_size=8192, show_progress=True):
    def __init__(self, token, project_name, task_name, scenario_flag, algorithm, output_var,
                size_threshold_mb=50, chunk_size=8192, show_progress=True):
        self.url = 'https://rshub.zju.edu.cn/'
        self.token = token
        self.project_name = project_name
        self.task_name = task_name
        self.size_threshold_mb = size_threshold_mb
        self.chunk_size = chunk_size
        self.show_progress = show_progress
        self.scenario_flag = scenario_flag
        self.algorithm = algorithm
        self.output_var = output_var
        self.data = None  # Stores loaded data
        
        result = return_task_path(self.token,self.project_name,self.task_name)
        self.task_path = result['path']
        if result['error_message'] is not None and result['task_status']!="failed":
           raise ValueError(f"You cannot download the file: {result['error_message']}")
            
    def load_error_message(self):
        try:
            task_path = self.task_path
            full_url = self.url + 'projects/' + task_path + '/Job/error.txt'
            
            response = requests.get(full_url)
            
            # Raise an exception for bad HTTP responses
            response.raise_for_status()
            
            # Get the error file contents
            error_content = response.text
            
            # Return a structured error dictionary
            print(f"message: {error_content}")
    
        except requests.RequestException as e:
            # Handle different types of request errors
            print(f"Error retrieving file: {e}")
            logging.error(f"Request Error: {e}")
            return None
        
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error processing error file: {e}")
            logging.error(f"Unexpected Error: {e}")
            return None
        
    def list_files(self):
        try:
            task_path = self.task_path
            full_url = self.url + 'projects/list-files'

            csv_path = urljoin(self.url, 'projects/output_info.csv')
            manager = FunctionOutputManager(csv_file=csv_path)
            try:
                filestruct = manager.get_extension(
                    self.scenario_flag, self.algorithm, self.output_var)
            except Exception as e:  # Catch any other unexpected error
                logging.error("Unexpected error resolving output extension", exc_info=e)
                raise

            output_extension = filestruct['extension']
            self.outputdir = filestruct['output_dir']
            
            data = {'path': task_path}
            
            response = requests.get(full_url, params=data)
            
            # Raise an exception for bad HTTP responses
            response.raise_for_status()
            
            # Get the error file contents
            content = response.json()
            url_part =  [item['url'] for item in content 
                      if os.path.splitext(item['name'])[1] == output_extension]
            
            filenames = []
            for url_item in url_part:
                parts=url_item.split('/')[-1]
                # full_url = urljoin(self.url,url_item)
                filenames.append(parts)        
            
            # Return a structured error dictionary
            return filenames
    
        except requests.RequestException as e:
            # Handle different types of request errors
            print(f"Error retrieving file: {e}")
            logging.error(f"Request Error: {e}")
            return None
        
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error processing error file: {e}")
            logging.error(f"Unexpected Error: {e}")
            return None        

    def load_parameters(self):
        """Load the task's parameter JSON into memory."""
        # Try common filenames in order
        param_candidates = ["parameters.json", "parameter.json"]
        for filename in param_candidates:
            param_url = f"{self.url}projects/{self.task_path}/{filename}"
            try:
                return self.load_output_from_method(param_url, force_method='memory')
            except Exception as e:
                logging.error("Failed to load parameter file", exc_info=e)
        print("Error loading parameter.json/parameters.json")
        return None
            
    def load_output_from_method(self, full_url, force_method=None, var =None):
            
        def convert_item(item):
            """Convert h5py items to appropriate Python types"""
            if isinstance(item, h5py.Dataset):
                data = item[()]
                # Handle string datasets
                if item.dtype.kind in ['S', 'U']:  # bytes or unicode strings
                    if data.ndim == 0:
                        return str(data)
                    else:
                        return np.array([str(x) for x in data.flatten()]).reshape(data.shape)
                return data
            elif isinstance(item, h5py.Group):
                return {key: convert_item(val) for key, val in item.items()}
            else:
                return item
        
        def load_h5_files(object):
            with h5py.File(object, 'r') as f:
                data = {key: convert_item(val) for key, val in f.items()}
            return data
        
        def load_mat_files(object):
            mat_data = loadmat(object)
            data = {var: mat_data[var] for var in mat_data if not var.startswith('__')} 
            return data
        
        def load_from_memory(url):
            
            """Load small H5 files directly into memory"""
            print("Loading small file directly into memory...")
            response = requests.get(url)
            response.raise_for_status()
            
            # Create file-like object in memory
            object = io.BytesIO(response.content)
            
            try:
                extension = os.path.splitext(url)[1].lower()
                if extension == '.h5':
                    data = load_h5_files(object)
                elif extension == '.mat':
                    data = load_mat_files(object)
                elif extension == '.json':
                    data = json.loads(object.getvalue().decode('utf-8'))
                else:
                    raise ValueError(f"Unsupported file extension for in-memory load: {extension}")
                print('Sucessfully loaded')
                return data
            finally:
                object.close()
        
        def load_from_disk(url,show_progress=True):
            """Download large H5 files to disk then load"""
            print("Downloading large H5 file to temporary location...")
            
            # Get file size for progress bar
            response = requests.head(url)
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.h5') as temp_file:
                if show_progress and total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, 
                            desc="Downloading", ncols=100) as pbar:
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            temp_file.write(chunk)
                            pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        temp_file.write(chunk)
                
                temp_filename = temp_file.name
            
            try:
                # Load the h5 file
                print("Loading files from disk...")
                extension = os.path.splitext(url)
                extension = extension[1]
                data={}
                if extension == '.h5':
                    print("Loading h5 file")
                    data = load_h5_files(temp_filename)
                elif extension == '.mat':
                    print("Loading mat file")
                    data = load_mat_files(temp_filename)  
                return data
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_filename)
                    print("Temporary file cleaned up.")
                except:
                    print(f"Warning: Could not delete temporary file {temp_filename}")
        
        try:
            extension = os.path.splitext(full_url)[1].lower()
            response = requests.head(full_url)
            response.raise_for_status()
            
            file_size = int(response.headers.get('content-length', 0))
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"File size: {file_size_mb:.2f} MB")
            
            if extension == '.json':
                self.data = load_from_memory(full_url)
            elif force_method == 'memory':
                self.data = load_from_memory(full_url)
            elif force_method == 'disk':
                self.data = load_from_disk(full_url)
            else: 
                if file_size == 0:
                    print("Warning: Could not determine file size. Attempting in-memory loading...")
                    self.data = load_from_memory(full_url)
                elif file_size_mb <= self.size_threshold_mb:
                    print(f"File is small (<= {self.size_threshold_mb} MB), loading into memory...")
                    self.data = load_from_memory(full_url)
                else:
                    print(f"File is large (> {self.size_threshold_mb} MB), downloading to disk...")
                    self.data = load_from_disk(full_url, self.show_progress)    
            if var is None:
                return self.data
            
            variable = var.split()
            print(f"Variables Loaded:{variable}")
            
            if len(variable) == 1 and variable[0] in self.data:
                return self.data[variable[0]]
            
            return {var:self.data[var] for var in variable if var in self.data}
            
        except requests.exceptions.RequestException as e:
            print(f"Error accessing file: {e}")
            return None
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return None
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            return None
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            return None
        except Exception as e:
            print(f"Error loading the file: {e}")
            return None 
    
    def download_only(self,file,url,download_path):
        save_path = os.path.join(download_path,file)
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Check HTTP errors
            
            # Get total file size for progress bar
            total_size = int(response.headers.get('content-length', 0))
            
            with open(save_path, 'wb') as f, tqdm(
                desc=file,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
            return (True, file)
        
        except Exception as e:
            return (False, f"{file}: {str(e)}")
        
    # Main function    
    def load_outputs(self,filename = None, fGHz = None, inc_ang = None, var = None,
                force_method=None, download_path=None):
        
        if download_path is not None:
            d_only = True
            
        else:
            if not isinstance(fGHz,(str)):
                fGHz=str(fGHz)
        
            if not isinstance(inc_ang,(str)):
                inc_ang=str(inc_ang)
            
            csv_path = urljoin(self.url, 'projects/output_info.csv')
            manager = FunctionOutputManager(csv_file=csv_path)
            try:
                self.file = manager.generate_filename(
                    self.scenario_flag, self.algorithm, self.output_var,fGHz=fGHz, inc_angle=inc_ang)
            except Exception as e:  # Catch any other unexpected error
                logging.error("Unexpected error generating filename", exc_info=e)
                raise
            
            extension = self.file['extension']
            d_only = self.file['download_only']
            output_dir = self.file['output_dir']
            
            if filename is None:
                filename = self.file['file']  
        
            if not filename.endswith(extension):
                filename = filename + extension
            
            full_url = f"{self.url}projects/{self.task_path}/{output_dir}/{filename}"
        
        if d_only is True:
            if download_path is None:
                raise ValueError(f"Please provide a download path")
                
            # Find all files matching "output_*" in current directory
            # files = glob.glob(filename)
            files = self.list_files()

            # Copy files to download directory (or process them)
            for file in files:
                
                full_url = f"{self.url}projects/{self.task_path}/{self.outputdir}/{file}"
                
                self.download_only(file,full_url,download_path)
                print(f"Downloaded {file}")

            print(f"Total files downloaded: {len(files)}")
        else:
            data = self.load_output_from_method(full_url, 
                force_method=force_method,  
                var=var)
            return data
                    
            
if __name__ == "__main__":
    # Test the function
    test_url = "https://your-h5-file-url-here.h5"
    
    # Load with automatic size detection
    try:
        data =load_file(test_url)
        if data:
            print("Successfully loaded H5 file!")
            print(f"Keys in file: {list(data.keys())}")
            
            # Display some info about each key
            for key, value in data.items():
                if isinstance(value, np.ndarray):
                    print(f"{key}: {value.shape} {value.dtype}")
                else:
                    print(f"{key}: {type(value)}")
        else:
            print("Failed to load H5 file.")
    except Exception as e:
        print(f"Main Error: {e}")    
        

        
