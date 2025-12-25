from collections.abc import Mapping
import logging
import re
from typing import Any, Sequence, overload
from heaobject.root import HEAObject, get_all_heaobject_subclasses
from heaobject.scrubber import scrubbed
from inspect import isabstract

from yarl import URL
from heaserver.service.oidcclaimhdrs import ACCESS_TOKEN, EMAIL, NAME, FAMILY_NAME, GIVEN_NAME, SESSION_STATE, \
    PREFERRED_USERNAME


# A tuple of regexes that will be replaced with '******' or (regex, replacement string) tuples.
_regex_patterns: tuple[str | tuple[str, str], ...] = ((r'(access_token=)[^&\s]+', r'\1******'),  # access_token query parameter.
                                                      (r'(account_id=)[^&\s]+', r'\1******'),  # account_id query parameter.
                                                      (r'(heaobject\.account\.AWSAccount\^)[^\']+', r'\1******'),  # scrub AWS account DesktopObject ids.
                                                      (r'(heaobject\.folder\.AWSS3BucketItem\^)[^\']+', r'\1******'),  # scrub AWS bucket names.
                                                      (r"^arn:(?P<Partition>[^:\n]*):(?P<Service>[^:\n]*):(?P<Region>[^:\n]*):(?P<AccountID>[^:\n]*):(?P<ResourceType>[^:/\n]*[:/])?(?P<Resource>.*)$", r"arn:\1:\2:\3:******:\5******"))

_regex_compiled_patterns = tuple((re.compile(pattern_sub[0]), pattern_sub[1]) if isinstance(pattern_sub, tuple)
                                 else re.compile(pattern_sub) for pattern_sub in _regex_patterns)

# Put anything here that should be considered sensitive keys but is not marked as such in HEAObject attribute metadata
# or might be a dictionary key.
_sensitive_keys_set = set(['headers', 'credentials', 'Authorization', 'token', 'Arn', 'Resource', 'Path', 'UserId',
                           'Account', 'bucket_id', 'path', 's3_uri', 'resource_type_and_id', 'firstName', 'username',
                           'lastName', 'userId', 'userName', 'access_token']) | \
    {ACCESS_TOKEN, EMAIL, NAME, FAMILY_NAME, GIVEN_NAME, SESSION_STATE, PREFERRED_USERNAME}


for cls in get_all_heaobject_subclasses(lambda x: not isabstract(x)):
    instance: HEAObject = cls()
    for attr_name, attr_metadata in instance.get_all_attribute_metadata().items():
        if attr_metadata.sensitive:
            _sensitive_keys_set.add(attr_name)


class SensitiveDataFilter(logging.Filter):
    """
    A logging filter that masks sensitive data in log messages. It looks for the keys defined in the sensitive_keys
    class variable in the record arguments (if they are a Mapping) and the log message itself.

    Subclass this filter and override the `patterns` and `sensitive_keys` attributes to customize the patterns and keys
    to be masked. The default regex patterns and sensitive keys are defined in the patterns and sensitive_keys
    constants.

    Sequence arguments are converted to lists, and Mapping arguments are converted to dicts.

    This class is based on https://dev.to/camillehe1992/mask-sensitive-data-using-python-built-in-logging-module-45fa.
    """
    patterns = _regex_compiled_patterns
    sensitive_keys = frozenset(_sensitive_keys_set)
    __sensitive_key_regexes = dict[str, tuple[re.Pattern[str], str]]()
    __ends_with_sensitive_keys = tuple('.' + k for k in sensitive_keys)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.args = self.__mask_sensitive_all_args(record.args)
            record.msg = self.__mask_sensitive_msg(record.msg)
            return True
        except:
            return True

    @overload
    def __mask_sensitive_all_args(self, args: None) -> None:
        pass

    @overload
    def __mask_sensitive_all_args(self, args: Mapping[str, object]) -> Mapping[str, object]:
        pass

    @overload
    def __mask_sensitive_all_args(self, args: tuple[object, ...]) -> tuple[object, ...]:
        pass

    def __mask_sensitive_all_args(self, args: tuple[object, ...] | Mapping[str, object] | None) -> tuple[object, ...] | Mapping[str, object] | None:
        """
        Masks sensitive data in all of the given log record arguments.

        :param args: the log record arguments, which can be a tuple or list.
        :return: the masked log record arguments.
        """
        if not isinstance(args, tuple):
            return self.__mask_sensitive_args(args)
        else:
            return tuple([self.__mask_sensitive_msg(arg) for arg in args])

    @overload
    def __mask_sensitive_args(self, args: None) -> None:
        pass

    @overload
    def __mask_sensitive_args(self, args: Mapping[str, object]) -> dict[str, object]:
        pass

    @overload
    def __mask_sensitive_args(self, args: Sequence[object]) -> list[object]:
        pass

    def __mask_sensitive_args(self, args: Sequence[object] | Mapping[str, object] | None) -> list[object] | dict[str, object] | None:
        """
        Masks sensitive data in the given log record arguments.

        :param args: the log record arguments, which can be a mapping, tuple, or list.
        :return: the masked log record arguments.
        """
        if isinstance(args, Mapping):
            new_args: dict[str, object] = {}
            for key in args.keys():
                # Dot-separated key names may be generated by Representor objects and should also be checked. Because
                # the key names come from python attributes, and attribute names cannot have periods in them, we don't
                # need to worry about false positives from periods with other meanings.
                if key in self.sensitive_keys or key.endswith(self.__ends_with_sensitive_keys):
                    new_args[key] = "******"
                else:
                    # mask sensitive data in dict values
                    new_args[key] = self.__mask_sensitive_msg(args[key])
            return new_args
        elif args is None:
            return args
        else:
            # when there are multiple args in record.args
            return list(self.__mask_sensitive_msg(arg) for arg in args)

    def __mask_sensitive_msg(self, message: object) -> object:
        """
        Masks sensitive data in the given log message.

        :param message: the log message, which can be a string or a dict.
        :return: the masked log message.
        """
        if not isinstance(message, str):
            if isinstance(message, (Mapping, Sequence)):
                return self.__mask_sensitive_args(message)
            if isinstance(message, URL):
                return URL(str(self.__mask_sensitive_msg(str(message))))
            return message
        for pattern_sub in self.patterns:
            if isinstance(pattern_sub, tuple):
                pattern, replace = pattern_sub
            else:
                pattern = pattern_sub
                replace = '******'
            message = pattern.sub(replace, message)
        for key in self.sensitive_keys:
            if key not in self.__sensitive_key_regexes:
                pattern_str = rf"'{key}': '[^']+'"
                replace = f"'{key}': '******'"
                self.__sensitive_key_regexes[key] = (re.compile(pattern_str), replace)
            pattern, replace = self.__sensitive_key_regexes[key]
            message = pattern.sub(replace, message)
        return message


PROD_LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'sensitive_data_filter': {
            '()': SensitiveDataFilter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['sensitive_data_filter'],
            'level': 'NOTSET',
            'formatter': 'default',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'botocore.endpoint': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.parsers': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.loaders': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.httpsession': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.hooks': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.utils': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.configprovider': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.regions': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.retries.standard': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.credentials': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer.tasks': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer.utils': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'boto3.s3.transfer': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.command': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.serverSelection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.topology': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aiormq.connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.exchange': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.channel': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.robust_connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.queue': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aiosqlite': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        }
    }
}


DEBUG_LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'sensitive_data_filter': {
            '()': SensitiveDataFilter,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['sensitive_data_filter'],
            'level': 'NOTSET',
            'formatter': 'default',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'botocore.endpoint': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.parsers': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.loaders': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.httpsession': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.hooks': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.utils': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.configprovider': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.regions': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.retries.standard': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore.credentials': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer.tasks': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer.utils': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'boto3.s3.transfer': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.command': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.serverSelection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pymongo.topology': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aiormq.connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.exchange': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.channel': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.robust_connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.connection': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aio_pika.queue': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'aiosqlite': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        }
    }
}


class ScrubbingLogger(logging.Logger):
    """
    Logger that scrubs sensitive HEAObject attributes from log messages when they're passed as arguments or in a list
    or tuple that's passed as an argument.
    """

    def makeRecord(self, *args, **kwargs) -> logging.LogRecord:
        record = super().makeRecord(*args, **kwargs)
        if isinstance(record.args, tuple):
            def scrub_if_needed(obj: object) -> object:
                if isinstance(obj, HEAObject):
                    return scrubbed(obj)
                elif isinstance(obj, (list, tuple)):
                    return type(obj)(scrub_if_needed(item) for item in obj)
                else:
                    return obj
            record.args = tuple(scrub_if_needed(obj) for obj in record.args)

        return record
