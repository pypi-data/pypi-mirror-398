import time
import requests
from http.client import IncompleteRead
from dataset_down.exception.IncompleteReadException import IncompleteReadException
from dataset_down.exception.InterruptExcepiton import InterruptException
from dataset_down.log.logger import get_logger

logger = get_logger(__name__)
def retry_with_backoff(max_retries=3, base_delay=1, max_delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_count = 0
            delay = base_delay
            exception = None
            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    exception = e
                    if isinstance(e, IncompleteRead):
                        logger.error(f"IncompleteRead: {e}")
                    elif isinstance(e, requests.exceptions.ConnectionError):
                        logger.warning(f"ConnectionError: {e}")
                    elif isinstance(e, requests.exceptions.ReadTimeout):
                        logger.warning(f"ReadTimeout: {e}")
                    elif isinstance(e, requests.exceptions.ChunkedEncodingError):
                        logger.error(f"ChunkedEncodingError: {e}")
                    elif isinstance(e, IncompleteReadException):
                        logger.error(f"IncompleteReadException: {e}")
                    elif isinstance(e, InterruptException):
                        logger.critical(f"InterruptException: {e}")
                        break
                    elif isinstance(e, requests.exceptions.RequestException):
                        if str(e).__contains__("Unauthorized"):
                            logger.critical(f"{e}")
                            break
                        logger.error(f"RequestException: {e}")
                    else:
                        if str(e).__contains__("Access Denied"):
                            logger.critical(f"{e}")
                            break
                        logger.error(f"Unexpected error: {e}")
                        
                    time.sleep(delay)
                    retry_count += 1
                    delay = min(delay * 1.5, max_delay)    
            raise Exception(
                f"function {func.__name__} failed after {retry_count} retries,msg: {exception}"
            )
        return wrapper
    return decorator