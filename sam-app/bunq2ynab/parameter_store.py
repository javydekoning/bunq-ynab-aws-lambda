import boto3
from errors import ParameterNotFoundError
from logger import configure_logger

LOGGER = configure_logger(__name__)

class ParameterStore:
    """Class used for modeling Parameters
    """

    def __init__(self):
        self.client = boto3.client('ssm')

    def fetch_parameter(self, name, with_decryption=False):
        """Gets a Parameter from Parameter Store (Returns the Value)
        """
        try:
            LOGGER.debug('Fetching Parameter %s', name)
            response = self.client.get_parameter(
                Name=name,
                WithDecryption=with_decryption
            )
            return response['Parameter']['Value']
        except self.client.exceptions.ParameterNotFound:
            raise ParameterNotFoundError(
                'Parameter {0} Not Found'.format(name)
            )

    def put_parameter(self, name, value):
        """Puts a Parameter into Parameter Store
        """
        try:
            current_value = self.fetch_parameter(name)
            assert current_value == value
            LOGGER.debug('No need to update parameter %s with value %s since they are the same', name, value)
        except (ParameterNotFoundError, AssertionError):
            LOGGER.debug('Putting SSM Parameter %s with value %s', name, value)
            self.client.put_parameter(
                Name=name,
                Value=value,
                Type='String',
                Overwrite=True
            )