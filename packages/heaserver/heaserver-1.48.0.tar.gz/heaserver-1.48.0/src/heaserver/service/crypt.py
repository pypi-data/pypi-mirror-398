"""
A module providing utilities for decrypting configuration properties and for encrypting and decrypting HEAObject
attributes.
"""
from typing import Optional, cast
from heaobject.encryption import Encryption
from aiohttp import web

from .requestproperty import HEA_ATTRIBUTE_ENCRYPTION_KEY
from .appproperty import HEA_ATTRIBUTE_ENCRYPTION_KEY_GETTER
import abc


class SecretDecryption():
    """
    A helper class for decrypting encrypted configuration properties.
    """

    def __init__(self, key: bytes) -> None:
        """
        Initializes the SecretDecryption instance with the given key.

        :param key: the decryption key as bytes.
        """
        self.__encryption = Encryption(key)

    @property
    def encrypted_config_property_prefix(self) -> str:
        """
        The prefix that indicates that a configuration property is encrypted.

        :return: the encrypted property prefix.
        """
        return '{crypt}'

    def is_config_property_encrypted(self, value: str | None) -> bool:
        """
        Determines whether a configuration property is encrypted.

        :param value: the configuration property value.
        :return: True if the property is encrypted, False otherwise.
        """
        return value is not None and value.startswith(self.encrypted_config_property_prefix)

    def decrypt_config_property(self, encrypted_value: str | None) -> str | None:
        """
        Decrypts a configuration property if it is encrypted. Encrypted configuration properties are expected to be
        prefixed with '{crypt}'.

        :param encrypted_value: the encrypted configuration property value.
        :return: the decrypted configuration property value, or the original value if it was not encrypted.
        """
        prefix = self.encrypted_config_property_prefix
        if encrypted_value and encrypted_value.startswith(prefix):
            return self.__encryption.decrypt(encrypted_value[len(prefix):]).decode('utf-8')
        return encrypted_value

    def decrypt(self, data: bytes | str) -> bytes:
        """
        Decrypts the given data using the configured decryption key.

        :param data: the data to decrypt, either as bytes or a string.
        :return: the decrypted data as bytes.
        """
        return self.__encryption.decrypt(data)

    @staticmethod
    def from_request(request: web.Request) -> Optional['SecretDecryption']:
        """
        Creates a SecretDecryption instance from the request, caching the key for the duration of the request.

        :param request: the aiohttp Request.
        :return: a SecretDecryption instance, or None if the decryption key is not available.
        """
        return get_secret_decryption_from_request(request)

    @staticmethod
    def from_app(app: web.Application) -> Optional['SecretDecryption']:
        """
        Creates a SecretDecryption instance from the app.

        :param app: the aiohttp Application.
        :return: a SecretDecryption instance, or None if the decryption key is not available.
        """
        return get_secret_decryption_from_app(app)


class EncryptionDecryptionKeyGetter(abc.ABC):
    """
    An interface for getting encryption and decryption keys for attribute encryption and decryption, as well as
    configuration property decryption.
    """

    @abc.abstractmethod
    def get_attribute_encryption_key(self) -> bytes | None:
        """
        Gets the symmetric encryption key used for attribute encryption and decryption, if available.

        :return: the encryption key as bytes, or None.
        """
        pass

    @abc.abstractmethod
    def get_attribute_encryption(self) -> Encryption | None:
        """
        Gets the attribute encryption instance if an encryption key is available.

        :return: an Encryption instance, or None.
        """
        pass

    @abc.abstractmethod
    def get_secret_decryption_key(self) -> bytes | None:
        """
        Gets the decryption key for encrypted configuration properties.

        :return: the decryption key as bytes, or None.
        """
        pass

    @abc.abstractmethod
    def get_secret_decryption(self) -> SecretDecryption | None:
        """
        Gets a SecretDecryption instance for decrypting configuration properties, if a decryption key is available.

        :return: a SecretDecryption instance, or None.
        """
        pass


def get_attribute_key_from_app(app: web.Application) -> bytes | None:
    """
    Gets the symmetric key for encrypting and decrypting HEAObject attributes. Unlike the request-based version,
    this does not cache the key.

    :param app: the aiohttp Application.
    :return: the key as bytes, or None.
    """
    encryption_key_getter = cast(EncryptionDecryptionKeyGetter, app[HEA_ATTRIBUTE_ENCRYPTION_KEY_GETTER])
    return encryption_key_getter.get_secret_decryption_key()


def get_attribute_key_from_request(request: web.Request) -> bytes | None:
    """
    Gets the symmetric key for encrypting and decrypting HEAObject attributes, caching the encryption key for the
    duration of the given request.

    :param request: the aiohttp Request.
    :return: the key as bytes, or None if the key is not available.
    """
    encryption_key = cast(bytes | None, request.get(HEA_ATTRIBUTE_ENCRYPTION_KEY))
    if encryption_key is None:
        encryption_key_getter = cast(EncryptionDecryptionKeyGetter, request.app[HEA_ATTRIBUTE_ENCRYPTION_KEY_GETTER])
        encryption_key = request[HEA_ATTRIBUTE_ENCRYPTION_KEY] = encryption_key_getter.get_attribute_encryption_key()
    return encryption_key


def get_attribute_encryption_from_app(app: web.Application) -> Encryption | None:
    """
    Gets the Encryption instance for encrypting and decrypting HEAObject attributes using the encryption key getter
    stored in the app.

    :param app: the aiohttp Application.
    :return: the Encryption instance, or None if the encryption key is not available.
    """
    encryption_key = get_attribute_key_from_app(app)
    return Encryption(encryption_key) if encryption_key else None


def get_attribute_encryption_from_request(request: web.Request) -> Encryption | None:
    """
    Gets the Encryption instance for encrypting and decrypting HEAObject attributes, caching the encryption key for
    the duration of the given request.

    :param request: the aiohttp Request.
    :return: the Encryption instance, or None if the encryption key is not available.
    """
    encryption_key = get_attribute_key_from_request(request)
    return Encryption(encryption_key) if encryption_key else None


def get_secret_decryption_from_app(app: web.Application) -> SecretDecryption | None:
    """
    Gets a SecretDecryption instance using the encryption key getter stored in the app.

    :param app: the aiohttp Application.
    :return: a SecretDecryption instance, or None if the decryption key is not available.
    """
    encryption_key = get_attribute_key_from_app(app)
    return SecretDecryption(encryption_key) if encryption_key else None


def get_secret_decryption_from_request(request: web.Request) -> SecretDecryption | None:
    """
    Gets a SecretDecryption instance using the encryption key getter stored in the app, caching the encryption key
    for the duration of the request.

    :param request: the aiohttp Request.
    :return: a SecretDecryption instance, or None if the decryption key is not available.
    """
    decryption_key = get_attribute_key_from_request(request)
    return SecretDecryption(decryption_key) if decryption_key else None
