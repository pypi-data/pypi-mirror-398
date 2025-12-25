import configparser

from yarl import URL

from .defaults import DEFAULT_PORT, DEFAULT_BASE_URL
from .crypt import EncryptionDecryptionKeyGetter, SecretDecryption
from heaobject.encryption import Encryption
import os


class Configuration(EncryptionDecryptionKeyGetter):
    """
    Configuration information for the service.
    """
    def __init__(self,
                 base_url: str | URL = DEFAULT_BASE_URL,
                 port: int | str = DEFAULT_PORT,
                 config_file: str | None = None,
                 config_str: str | None = None):
        """
        Initializes the configuration object.

        :param base_url: the base URL of the service. Required.
        :param port: the port the service will listen on. Required.
        :param config_file: an optional INI file with configuration data.
        :param config_str: an optional configuration INI file as a string. Parsed after any config_file.
        """
        self.__base_url = URL(base_url) if base_url else DEFAULT_BASE_URL
        self.__port = int(port) if port else DEFAULT_PORT
        self.__parsed_config = configparser.ConfigParser()
        self.__config_file = config_file
        self.__config_str = config_str
        if config_file:
            self.__parsed_config.read(config_file)
        if config_str:
            self.__parsed_config.read_string(config_str)
        self.__parsed_config.read_dict({})

    @property
    def port(self) -> int:
        """
        The port this service will listen on.
        :return: a port number.
        """
        return self.__port

    @property
    def base_url(self) -> URL:
        """
        This service's base URL.
        :return: a URL.
        """
        return self.__base_url

    @property
    def parsed_config(self) -> configparser.ConfigParser:
        """
        Any configuration information parsed from an INI file or INI string.
        :return: a configparser.ConfigParser object.
        """
        result = configparser.ConfigParser()
        result.read_dict(self.__parsed_config)
        return result

    @property
    def config_file(self) -> str | None:
        """
        The path to a config file.
        :return: the config file path string, or None.
        """
        return self.__config_file

    @property
    def config_str(self) -> str | None:
        """
        A string containing an INI file, if provided in the constructor.
        :return: a config file string, or None.
        """
        return self.__config_str

    @property
    def default_section(self) -> configparser.SectionProxy | None:
        """
        The default section of the parsed configuration.

        :return: a configparser.SectionProxy object.
        """
        return self.__parsed_config['DEFAULT'] if 'DEFAULT' in self.__parsed_config else None

    @property
    def registry_url(self) -> str | None:
        """
        The registry URL, if specified in the configuration.

        :return: the registry URL string, or None.
        """
        return self.__get_default_section_property('Registry')

    @property
    def encryption_key_file(self) -> str | None:
        """
        The path to the encryption key file, if specified in the configuration. A ~ is expanded to the user's home
        directory for Windows compatibility.

        :return: the encryption key file path string, or None.
        """
        prop = self.__get_default_section_property('EncryptionKeyFile')
        return os.path.expanduser(prop) if prop else None

    @property
    def encryption_key_env_var(self) -> str | None:
        """
        The encryption key, if specified in the configuration as a property
        value. The encryption key should NOT be stored in the configuration
        file in production settings!

        :return: the encryption key as a str, or None.
        """
        return self.__get_default_section_property('EncryptionKey')

    def get_attribute_encryption_key(self) -> bytes | None:
        """
        Gets the encryption key from the encryption key file, if specified,
        or from the environment variable, if specified. If stored as an
        environment variable, it is returned as UTF-8 encoded bytes.

        :return: the encryption key as bytes, or None.
        """
        key_file = self.encryption_key_file
        if key_file and os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read().strip()
        else:
            env_var = self.encryption_key_env_var
            if env_var:
                return env_var.encode('utf-8')
        return None

    def get_attribute_encryption(self) -> Encryption | None:
        """
        Gets the attribute encryption instance if an encryption key is available.

        :return: an Encryption instance, or None.
        """
        key = self.get_attribute_encryption_key()
        return Encryption(key) if key else None

    def get_secret_decryption_key(self) -> bytes | None:
        """
        Gets the decryption key. In this implementation, it is the same as the encryption key.

        :return: the decryption key as bytes, or None.
        """
        return self.get_attribute_encryption_key()

    def get_secret_decryption(self) -> SecretDecryption | None:
        """
        Gets a SecretDecryption instance if an encryption key is available.

        :return: a SecretDecryption instance, or None.
        """
        encryption_key = self.get_attribute_encryption_key()
        if encryption_key:
            return SecretDecryption(encryption_key)
        return None

    def __get_default_section_property(self, property_name: str) -> str | None:
        """
        Gets a property from the default section of the configuration.

        :param property_name: the property name.
        :return: the property value as a string, or None.
        """
        default_section = self.default_section
        return default_section.get(property_name) if default_section else None
