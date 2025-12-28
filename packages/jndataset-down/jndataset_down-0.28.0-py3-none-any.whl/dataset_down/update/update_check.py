from datetime import timedelta
import datetime
import os 
import json
import sys
from dataset_down.config.constants import NAME
from dataset_down.update.sdk_version import LatestVersionInfo, SDKVersion
from dataset_down.utils.file import get_file_content
from dataset_down.utils.retryable import retry_with_backoff
from dataset_down.utils.time_utils import get_datetime_from_formatted_str
from dataset_down.utils.time_utils import get_current_time
from dataset_down.utils.time_utils import get_current_formatted_time
from dataset_down.config.path_config import get_version_path




def get_now_version():
    return SDKVersion.get_now_version()

def get_version_from_local():
    try:
        version_json = get_file_content(get_version_path())
        version_dict = json.loads(version_json)
        return SDKVersion(**version_dict)
    except Exception as e:
        print(f"failed to get content from {get_version_path()}, error: {e}")
        return None

def get_last_version_update_time():
    try:
        if not os.path.exists(get_version_path()):
            return None
        version_cache_local = get_version_from_local()
        if version_cache_local:
            return version_cache_local.last_version_check_time
    except Exception:
        pass
    return None


def get_version_cache_expiration_time(last_update_time: datetime) -> datetime:
    return last_update_time + timedelta(days=1)



@retry_with_backoff(max_retries=3, base_delay=3, max_delay=5)    
def update_check():
    try:
        latestVersion, isLatestVersion, needUpdate = SDKVersion.check_newest_version()
        if  not isLatestVersion and needUpdate:
            print(f'A newer SDK version ({latestVersion}) is available. Attempting to upgrade via "pip install --upgrade {NAME}"')
            SDKVersion.update_sdk_to_latest()
            print(f'\nSDK updated successfully. Please re-run your command.\n')
            sys.exit(0)
    except Exception as e:
        raise Exception(f"Update SDK error: {e}")
    
    
    