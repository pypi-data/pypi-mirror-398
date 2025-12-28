import json
import os
from dataset_down.config import constants
from dataset_down.config.path_config import get_config_dir,get_config_path
from dataset_down.utils.file import get_file_content



def get_env(env_name) -> str:
    return os.environ.get(env_name)


def set_env(env_name, env_value):
    os.environ[env_name] = env_value
    
    
    

def get_config(ak=None, sk=None, auth=False):
    if ak is not None and sk is not None:
        return LoginConfig(ak, sk)
    if not os.path.exists(get_config_path()):
        ak_env_value = get_env(constants.AK_ENV_NAME)
        sk_env_value = get_env(constants.SK_ENV_NAME)
        if ak_env_value is not None and sk_env_value is not None:
            return LoginConfig(ak_env_value, sk_env_value)
        # need login
        if auth is True and not ak_env_value:
            raise Exception(
                'Please login with ak/sk, try "dataset-down login"'
            )
        return None
    config_json = get_file_content(get_config_path())
    config_dict = json.loads(config_json)
    return LoginConfig(config_dict["ak"], config_dict["sk"])





class LoginConfig(object):
    def __init__(self, ak, sk):
        if ak is None or sk is None:
            raise ValueError("ak and sk must not be empty")
        self.ak = ak.strip()
        self.sk = sk.strip()

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def store_to_local(self):
        if not os.path.exists(get_config_dir()):
            os.makedirs(get_config_dir(), mode=0o700)
        config_json = self.to_json()
        set_env(constants.AK_ENV_NAME, self.ak)
        set_env(constants.SK_ENV_NAME, self.sk)
        with open(get_config_path(), mode="w", encoding="utf-8") as f:
            f.write(config_json)