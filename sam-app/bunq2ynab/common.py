import json 

from logger import configure_logger

LOGGER = configure_logger(__name__)

def log_request(action, method, headers, data):
    LOGGER.debug("{0} {1}".format(action, method))
    for k, v in headers.items():
        LOGGER.debug("  {0}: {1}".format(k, v))
    if data:
        LOGGER.debug(json.dumps(data, indent=2))

def log_reply(reply):
    LOGGER.debug("Status: {0}".format(reply.status_code))
    for k, v in reply.headers.items():
        LOGGER.debug("  {0}: {1}".format(k, v))
    if reply.headers["Content-Type"].startswith("application/json"):
        LOGGER.debug(json.dumps(reply.json(), indent=2))
    else:
        LOGGER.debug(reply.text)