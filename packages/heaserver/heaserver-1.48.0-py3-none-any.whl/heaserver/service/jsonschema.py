"""
JSON schemas for validation. Schema files should be in the heaserver.service.jsonschemafiles package. See that package
for documentation.
"""
from pkgutil import get_data
from json import loads


def _get_json_schema(schema_file: str) -> str:
    data = get_data(__package__, schema_file)
    assert data is not None, f'Schema file {schema_file} not loaded'
    return loads(data)


WSTL_ACTION_SCHEMA = _get_json_schema('jsonschemafiles/wstlaction.json')

WSTL_SCHEMA = _get_json_schema('jsonschemafiles/wstl.json')

CJ_TEMPLATE_SCHEMA = _get_json_schema('jsonschemafiles/cjtemplate.json')

NVPJSON_SCHEMA = _get_json_schema('jsonschemafiles/nvpjson.json')
