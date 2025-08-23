"""Constants for Prometheus Lambda functions."""

# Default configuration values
DEFAULT_AWS_REGION = 'us-east-1'
DEFAULT_SERVICE_NAME = 'aps'
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1  # seconds

# API endpoints and paths
API_VERSION_PATH = '/api/v1'

# Security patterns to block
DANGEROUS_PATTERNS = [
    ';', '&&', '||', '`', '$(', '${',
    'file://', '/etc/', '/var/log',
    'http://', 'https://'
]
