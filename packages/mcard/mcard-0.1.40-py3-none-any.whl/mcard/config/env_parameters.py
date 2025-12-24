"""Environment parameter management for MCard."""
import os
import logging
from dotenv import load_dotenv
from .config_constants import (
    ENV_HASH_ALGORITHM,
    ENV_DB_PATH,
    ENV_DB_MAX_CONNECTIONS,
    ENV_DB_TIMEOUT,
    ENV_SERVICE_LOG_LEVEL,
    ENV_API_PORT,
    ENV_API_KEY,
    ENV_HASH_CUSTOM_MODULE,
    ENV_HASH_CUSTOM_FUNCTION,
    ENV_HASH_CUSTOM_LENGTH,
    DEFAULT_DB_PATH,
    TEST_DB_PATH,
    DEFAULT_PAGE_SIZE,    
    DEFAULT_POOL_SIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_API_KEY,
    DEFAULT_API_PORT,
)

logger = logging.getLogger(__name__)

class EnvParameters:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvParameters, cls).__new__(cls)
            cls._instance.load_env_variables()
        return cls._instance

    def load_env_variables(self):
        """Load environment variables with appropriate defaults from config_constants."""
        # Load environment variables from .env file
        load_dotenv()

        # Debug: Print the current working directory and .env file path
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Loading .env file from: {os.path.abspath('.env')}")

        # Debug: Print environment variables before and after loading
        logger.debug(f"Environment before loading .env - MCARD_DB_PATH: {os.environ.get(ENV_DB_PATH, 'Not set')}")

        # Load the .env file
        env_path = os.path.abspath('.env')
        if os.path.exists(env_path):
            logger.debug(f"Loading .env file from: {env_path}")
            load_dotenv(env_path)
        else:
            logger.warning(f"No .env file found at: {env_path}")

        logger.debug(f"Environment after loading .env - MCARD_DB_PATH: {os.environ.get(ENV_DB_PATH, 'Not set')}")

        # Set the database path from environment or use default
        self.MCARD_DB_PATH = os.getenv(ENV_DB_PATH, DEFAULT_DB_PATH)
        logger.debug(f"Using database path: {self.MCARD_DB_PATH} (absolute: {os.path.abspath(self.MCARD_DB_PATH) if self.MCARD_DB_PATH else 'N/A'})")
        self.DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', DEFAULT_PAGE_SIZE))        
        self.TEST_DB_PATH = os.getenv('TEST_DB_PATH', TEST_DB_PATH)
        self.MCARD_SERVICE_LOG_LEVEL = os.getenv(ENV_SERVICE_LOG_LEVEL, 'DEBUG')
        self.DEFAULT_POOL_SIZE = int(os.getenv('DEFAULT_POOL_SIZE', DEFAULT_POOL_SIZE))
        self.DEFAULT_TIMEOUT = float(os.getenv(ENV_DB_TIMEOUT, DEFAULT_TIMEOUT))
        self.MCARD_HASH_ALGORITHM = os.getenv(ENV_HASH_ALGORITHM, 'sha256') # Default to sha256
        self.MCARD_HASH_CUSTOM_MODULE = os.getenv(ENV_HASH_CUSTOM_MODULE, 'custom_module')
        self.MCARD_HASH_CUSTOM_FUNCTION = os.getenv(ENV_HASH_CUSTOM_FUNCTION, 'custom_function')
        self.MCARD_HASH_CUSTOM_LENGTH = int(os.getenv(ENV_HASH_CUSTOM_LENGTH, 64))
        self.MCARD_API_PORT = int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))
        self.MCARD_STORE_MAX_CONNECTIONS = int(os.getenv(ENV_DB_MAX_CONNECTIONS, DEFAULT_POOL_SIZE))
        self.MCARD_API_KEY = os.getenv(ENV_API_KEY, DEFAULT_API_KEY)

        # File processing tunables
        self.MCARD_WRAP_WIDTH_DEFAULT = int(os.getenv('MCARD_WRAP_WIDTH_DEFAULT', 1000))
        self.MCARD_WRAP_WIDTH_KNOWN = int(os.getenv('MCARD_WRAP_WIDTH_KNOWN', 1200))
        self.MCARD_MAX_PROBLEM_TEXT_BYTES = int(os.getenv('MCARD_MAX_PROBLEM_TEXT_BYTES', 2 * 1024 * 1024))
        self.MCARD_READ_TIMEOUT_SECS = float(os.getenv('MCARD_READ_TIMEOUT_SECS', 30))

    def get_db_path(self):
        return self.MCARD_DB_PATH

    def get_test_db_path(self):
        return self.TEST_DB_PATH

    def get_log_level(self):
        return self.MCARD_SERVICE_LOG_LEVEL

    def get_default_page_size(self):
        """Get the default number of items per page for pagination.
        
        Returns:
            int: The default number of items to display per page,
                 as configured in the environment or default constants.
        """
        return self.DEFAULT_PAGE_SIZE

    def get_default_pool_size(self):
        return self.DEFAULT_POOL_SIZE

    def get_default_timeout(self):
        return self.DEFAULT_TIMEOUT

    def get_hash_algorithm(self):
        return self.MCARD_HASH_ALGORITHM

    def get_hash_custom_module(self):
        return self.MCARD_HASH_CUSTOM_MODULE

    def get_hash_custom_function(self):
        return self.MCARD_HASH_CUSTOM_FUNCTION

    def get_hash_custom_length(self):
        return self.MCARD_HASH_CUSTOM_LENGTH

    def get_api_port(self):
        return self.MCARD_API_PORT

    def get_store_max_connections(self):
        return self.MCARD_STORE_MAX_CONNECTIONS

    def get_api_key(self):
        return self.MCARD_API_KEY

    # File processing tunables getters
    def get_wrap_width_default(self) -> int:
        return self.MCARD_WRAP_WIDTH_DEFAULT

    def get_wrap_width_known(self) -> int:
        return self.MCARD_WRAP_WIDTH_KNOWN

    def get_max_problem_text_bytes(self) -> int:
        return self.MCARD_MAX_PROBLEM_TEXT_BYTES

    def get_read_timeout_secs(self) -> float:
        return self.MCARD_READ_TIMEOUT_SECS
