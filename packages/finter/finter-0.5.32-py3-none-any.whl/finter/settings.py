import hashlib
import logging
import os
import sys
import traceback
import uuid

from dotenv import load_dotenv

from finter.api.user_api import UserApi
from finter.rest import ApiException

home_dir = os.path.expanduser("~")
dotenv_path = os.path.join(home_dir, ".env")
load_dotenv(dotenv_path)

logger = logging.getLogger("finter_sdk")
logger.setLevel(logging.INFO)
logger.propagate = False  # 상위 logger로 전파 방지

# 기존 핸들러 모두 제거
logger.handlers.clear()

# stdout 핸들러 추가
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)


def check_configuration():
    from finter.configuration import Configuration

    configuration = Configuration()
    if configuration.api_key["Authorization"] == "Token ":
        error_message = (
            "API Key is not set. Your now using finter Open Version.\n\n"
            "You can set the API Key in one of the following ways:\n"
            "- By setting an environment variable directly in your environment:\n"
            "    import os\n"
            "    os.environ['FINTER_API_KEY'] = 'YOUR_API_KEY'\n\n"
            "- By adding the following line to a .env file located in the project root:\n"
            "    FINTER_API_KEY='YOUR_API_KEY'"
        )
        if not hasattr(check_configuration, "has_logged"):
            logger.info(error_message)
            check_configuration.has_logged = True
    return configuration


def get_api_client():
    from finter import __version__
    from finter.api_client import ApiClient

    api_client = ApiClient(check_configuration())
    # Add finter version to request headers for server-side version checking
    api_client.default_headers['X-Finter-Version'] = __version__
    api_client.user_agent = f"finter/{__version__}"

    return api_client


def log_section(title):
    original_formatter = log_handler.formatter

    log_handler.setFormatter(logging.Formatter("%(message)s"))

    separator = "=" * 40
    header = f"\n{separator} {title} {separator}"
    logger.info(header)

    log_handler.setFormatter(original_formatter)


def log_warning(message):
    original_formatter = log_handler.formatter

    log_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.warning(message)

    log_handler.setFormatter(original_formatter)


def log_with_user_event(
    event_message, source, method, category, log_type=None, log_message=None
):
    if log_message:
        if log_type == "error":
            logger.error(log_message)
        elif log_type == "warning":
            logger.warning(log_message)
        elif log_type == "info":
            logger.info(log_message)
        else:
            pass
    user_event(event_message, source=source, method=method, category=category)


def log_with_traceback(message):
    logger.error(message)
    logger.error(traceback.format_exc())


def user_event(name, source="", method="", category=""):
    def _random_hash():
        random_uuid = uuid.uuid4()
        uuid_bytes = str(random_uuid).encode()
        hash_object = hashlib.sha256(uuid_bytes)
        return hash_object.hexdigest()

    params = {
        "name": name,
        "source": source,
        "method": method,
        "category": category,
        "rand": _random_hash(),
    }
    try:
        UserApi().log_usage_retrieve(**params)
    except ApiException as e:
        logger.error("Exception when calling UserApi->log_usage_retrieve: %s\n" % e)
