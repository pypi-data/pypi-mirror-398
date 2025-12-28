
import os
import json
import threading
from dataset_down.api.AuthApi import AuthApi
from dataset_down.config.constants import GET_TOKEN_URL,AK_ENV_NAME,SK_ENV_NAME,NAME
from dataset_down.config.login_config import LoginConfig,get_env
from dataset_down.config.path_config import get_config_dir, get_token_path,get_config_path
from dataset_down.utils.file import get_file_content

token_lock = threading.Lock()

class AuthClient(object):
    def __init__(self, host :str):
        self.host = host
        self.api = AuthApi(self.host)
        
    def login(self, ak: str, sk: str) -> dict:
        login_config = get_login_config(ak,sk)
        self.get_token_from_remote(login_config.ak,login_config.sk)
        login_config.store_to_local()
        
    
    
    def get_token_from_remote(self,ak: str = None,sk: str = None):
        login_config = get_login_config(ak,sk)
        token = self.api.get_token(login_config.ak,login_config.sk)
        save_token_to_local(token)
        return token
    
    
    
    def get_token(self,ak:str = None,sk:str = None):
        token = get_token_from_local()
        if not token or len(token) == 0:
            return self.get_token_from_remote(ak,sk)
        return token
        
        



auth_client = AuthClient(host=GET_TOKEN_URL)
    

def get_login_config(ak: str,sk: str) -> LoginConfig:
    if ak is not None and sk is not None:
        return LoginConfig(ak, sk)
    if not os.path.exists(get_config_path()):
        ak_env_value = get_env(AK_ENV_NAME)
        sk_env_value = get_env(SK_ENV_NAME)
        if ak_env_value is not None and sk_env_value is not None:
            return LoginConfig(ak_env_value, sk_env_value)
        else:
            raise Exception(
                f'Please login with ak/sk, try {NAME} login '
            )
    config_json = get_file_content(get_config_path())
    config_dict = json.loads(config_json)
    return LoginConfig(config_dict["ak"], config_dict["sk"])

def save_token_to_local(token: str) -> None:
    with token_lock:
        try:
            if not os.path.exists(get_config_dir()):
                    os.makedirs(get_config_dir(), mode=0o700)
            with open(get_token_path(), "w") as f:
                f.write(token)
        except Exception as e:
            print(e)
    
        
def get_token_from_local() -> str:
    with token_lock:
        if not os.path.exists(get_token_path()):
            return None
        token = get_file_content(get_token_path())
        if token is None or token == "":
            return None
        return token 