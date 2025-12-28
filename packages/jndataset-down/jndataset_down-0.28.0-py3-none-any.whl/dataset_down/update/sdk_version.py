
import os
import json
import subprocess
import requests 
import sys
from dataset_down.config.path_config import get_config_dir, get_version_path
from dataset_down.config.constants import SERVER_URL,VERSION,NAME
from dataset_down.utils.http_utils import http_common_header
from dataset_down.client.AuthClient import auth_client


def http_authorization_header() -> dict:
        try:
            header_dict = http_common_header()
            token = auth_client.get_token()
            header_dict['Authorization'] = token
        except Exception as e:
            print(f"{e}")
            sys.exit(-1)
        return header_dict


class SDKVersion(object):
    def __init__(self, last_version_check_time, latest_version_data) -> None:
        self.last_version_check_time = last_version_check_time
        self.latest_version_data = latest_version_data

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def store_to_local(self):
        if not os.path.exists(get_config_dir()):
            os.makedirs(get_config_dir(), mode=0o700)
        cache_json = self.to_json()
        try:
            with open(get_version_path(), mode="w", encoding="utf-8") as f:
                f.write(cache_json)
        except Exception as e:
            raise Exception(
                f"failed to store data:{cache_json} to {get_version_path()}: {e}"
            ) from e
    
    @staticmethod
    def get_now_version():
        return VERSION
    
    
    @staticmethod
    def check_newest_version():
        url = f'{SERVER_URL}version/check'
        data = {
            "name": NAME,
            "curVersion": VERSION
        }
        try:
            resp = requests.post(url, data=json.dumps(data),headers=http_authorization_header(),timeout=10)
            resp.raise_for_status()
            if resp.status_code == 200:
                code = resp.json()['code']
                if code == 0:
                    data = resp.json()['data']
                    latestVersion = data['latestVersion']
                    isLatestVersion = data['isLatestVersion']
                    needUpdate = data['needUpdate']
                    return (latestVersion, isLatestVersion, needUpdate)
            raise Exception("check version failed")        
        except Exception as e:
            raise e 
        
    @staticmethod
    def update_sdk_to_latest(use_official_url = True):
        official_url = "https://pypi.org/simple" if use_official_url else None
        try:
            command = ["pip", "install", "--upgrade", NAME]
            if official_url:
                command.extend(["--index-url", official_url])
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"update sdk from pip failed: {e}")
            
        
        
        
class LatestVersionInfo(object):
    def __init__(self, latest_version, is_latest_version,need_update):
        self.latest_version = latest_version
        self.is_latest_version = is_latest_version
        self.need_update = need_update
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)