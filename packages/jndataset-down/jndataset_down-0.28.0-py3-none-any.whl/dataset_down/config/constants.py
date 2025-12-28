import os 

VERSION = "0.28.0"
NAME = "jndataset-down"
# 默认的配置路径
DEFAULT_CONFIG_DIR = os.path.join(os.path.expanduser("~"), f".{NAME}")

# 默认配置文件名称
DEFAULT_CLI_CONFIG_FILE_NAME = "config.json"

DEFAULT_CLI_TOKEN_FILE_NAME = "token.json"

# version
DEFAULT_CLI_VERSION_FILE_NAME = "version.json"

DEFAULT_CLI_DATASET_FILE_NAME = "dataset.json"

AK_ENV_NAME = "DATASET_SDK_DOWN_AK"
SK_ENV_NAME = "DATASET_SDK_DOWN_SK"

#SERVER_URL = "http://120.92.51.36:31801/api/sdk-srv/v5/api/data/sdkService/"
#GET_TOKEN_URL = "http://120.92.51.36:31801/api/user-srv/userAccessKey/v1/getAccessToken"

BFF_URL = "https://www.beaicloud.com/api/data-bff/"
SERVER_URL = "https://www.beaicloud.com/api/sdk-srv/v5/api/data/sdkService/"
GET_TOKEN_URL = "https://www.beaicloud.com/api/user-srv/userAccessKey/v1/getAccessToken"

#BFF_URL = "https://platform-aiintegration-dev.baai.ac.cn/api/data-bff/"
#SERVER_URL = "http://platform-aiintegration-dev.baai.ac.cn/api/sdk-srv/v5/api/data/sdkService/"
#GET_TOKEN_URL = "http://platform-aiintegration-dev.baai.ac.cn/api/user-srv/userAccessKey/v1/getAccessToken"

#BFF_URL = "https://platform-aiintegration-mutitest.baai.ac.cn/api/data-bff/"
#SERVER_URL = "https://platform-aiintegration-mutitest.baai.ac.cn/api/sdk-srv/v5/api/data/sdkService/"
#GET_TOKEN_URL = "https://platform-aiintegration-mutitest.baai.ac.cn/api/user-srv/userAccessKey/v1/getAccessToken"


DOWNLOAD_URL = "download/"
OPERATE_URL = "operate/"

TIMEOUT = (5, None)
UPLOAD_TIMEOUT = (600, None)

