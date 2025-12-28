import requests
import json
from dataset_down.utils.http_utils import http_common_header
from dataset_down.utils.retryable import retry_with_backoff


class AuthApi(object):
    def __init__(self, host: str):
        self.host = host
    
    @retry_with_backoff(max_retries=3,base_delay=1,max_delay=5)
    def get_token(self, ak: str, sk: str ) -> dict:
        req = {"ak": ak, "sk": sk}
        ret = requests.post(self.host, data = json.dumps(req),headers= http_common_header() ,timeout= 3)
        ret.raise_for_status()
        if ret.status_code == 200:
            ret_code = ret.json()["code"]
            if ret_code == 0:
                data = ret.json()["data"]
                type = data["type"]
                token = data["token"]
                return type + ' ' + token
            else:
                raise Exception(f"failed to get token, ret_code: {ret_code}")
        else:
            raise Exception(f"failed to get token, ret_code: {ret.status_code}")