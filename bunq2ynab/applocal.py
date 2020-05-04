import os
import argparse

from config import configuration
from logger import configure_logger
from bunq import bunqapi
from ynab import ynabapi
from bunq2ynab import sync

LOGGER = configure_logger(__name__)

# Add commandline switches:
parser = argparse.ArgumentParser()
parser.add_argument('-l', action='store_true', help="Run in list mode")
args = parser.parse_args()

# Set configuration file path
config_file_path = os.path.join(os.path.dirname(__file__), 'config.json')
config_location = 'file:' + config_file_path

# Initialize Config, Bunq and YNAB
config = configuration(config_location)
b = bunqapi(config_location)
y = ynabapi(config_location)

# Start program
if args.l:
    LOGGER.info('Running in LIST mode, no accounts will be synced.')
    b.list_users()
    y.list_budget()
else:
    for i in config.value['bunq2ynab']:
        for key, value in i.items():
            assert value, '{0} cannot be an empty string. Setup your sync pairs in your config'.format(
                key)

    try:
        LOGGER.info('Running in SYNC mode.')
        sync(config, b, y)
    except:
        LOGGER.info('Detected authorization error, resetting config')
        config.value['bunq']['install_token'] = ''
        config.value['bunq']['priv_key'] = ''
        config.value['bunq']['session_token'] = ''
        config.save(config.value)
