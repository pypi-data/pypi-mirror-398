"""
Constants for microservice defaults.
"""
from yarl import URL
import logging

DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_PORT = 8080
DEFAULT_BASE_URL = URL(f'http://localhost:{DEFAULT_PORT}')
DEFAULT_REGISTRY_URL = 'http://localhost:8080'
