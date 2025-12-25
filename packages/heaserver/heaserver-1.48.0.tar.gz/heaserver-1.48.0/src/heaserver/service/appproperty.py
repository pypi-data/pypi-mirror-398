"""
Application properties that are loaded into the aiohttp app context when heaserver.service.runner.start is called.

HEA_REGISTRY - The base URL for the registry service.
HEA_WSTL_BUILDER_FACTORY - A zero-argument callable for getting the service's design-time WeSTL document.
HEA_DB - The database object to use.
HEA_COMPONENT - This service's base URL.
HEA_CLIENT_SESSION - A aiohttp.ClientSession instance.
HEA_MESSAGE_BROKER_PUBLISHER - The message broker publisher instance.
HEA_MESSAGE_BROKER_SUBSCRIBER - The message broker subscriber instance.
HEA_BACKGROUND_TASKS - A heaserver.service.background.BackgroundTaskManager instance.
HEA_CACHE - A cache instance for the service.
HEA_ATTRIBUTE_ENCRYPTION_KEY_GETTER - a heaserver.service.crypt.EncryptionDecryptionKeyGetter instance, currently used
    for attribute encryption and decryption, as well as configuration property decryption.
"""

HEA_REGISTRY = 'HEA_registry'
HEA_WSTL_BUILDER_FACTORY = 'HEA_WeSTL_builder_factory'
HEA_DB = 'HEA_db'
HEA_COMPONENT = 'HEA_component'
HEA_CLIENT_SESSION = 'HEA_client_session'
HEA_MESSAGE_BROKER_PUBLISHER = 'HEA_message_broker_publisher'
HEA_MESSAGE_BROKER_SUBSCRIBER = 'HEA_message_broker_subscriber'
HEA_BACKGROUND_TASKS = 'HEA_background_tasks'
HEA_CACHE = 'HEA_cache'
HEA_ATTRIBUTE_ENCRYPTION_KEY_GETTER = 'HEA_attribute_encryption_key_getter'
