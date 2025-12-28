import os
import hashlib
from pathlib import Path



def create_empty_file(file_path: str):
    if os.path.exists(file_path):
        raise Exception(f"file {file_path} already exists")
    with open(file_path, 'w') as f:
        pass


def list_files_in_folder(folder_path: str):
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise Exception(f"path {folder_path} is not a dir or does not exist")
    folder_path = os.path.abspath(folder_path)
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.startswith('.'):
                continue
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list
            
        
    

def get_file_content(file_name):
    with open(file_name, encoding='utf-8') as f:
        content = f.read()
    return content


def sha256(file_path: str, buf_size: int = 131072):
    if not Path(file_path).is_file():
        raise Exception(f"file {file_path} does not exist")
    sha256_obj = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            sha256_obj.update(data)
    return sha256_obj.hexdigest()
    