from jsonschema.validators import Draft7Validator
from jsonschema import ValidationError  # Leave these here so other modules can use them.
from . import jsonschema
from jsonschema import RefResolver
from importlib.resources import as_file, files as resource_container
from . import jsonschemafiles


def compile(schema: str | dict) -> Draft7Validator:
    """
    Returns the correct validator for the given schema.

    :param schema: a JSON schema (required).
    :return: a validator object.
    """
    with as_file(resource_container(jsonschemafiles)) as path:
        resolver = RefResolver(f'{path.as_uri()}/', referrer=schema)
        return Draft7Validator(schema=schema, resolver=resolver)



WSTL_ACTION_SCHEMA_VALIDATOR = compile(jsonschema.WSTL_ACTION_SCHEMA)
WSTL_SCHEMA_VALIDATOR = compile(jsonschema.WSTL_SCHEMA)
CJ_TEMPLATE_SCHEMA_VALIDATOR = compile(jsonschema.CJ_TEMPLATE_SCHEMA)
NVPJSON_SCHEMA_VALIDATOR = compile(jsonschema.NVPJSON_SCHEMA)
