from unittest import TestCase
from heaserver.service.jsonschemavalidator import WSTL_ACTION_SCHEMA_VALIDATOR, WSTL_SCHEMA_VALIDATOR, \
    CJ_TEMPLATE_SCHEMA_VALIDATOR, NVPJSON_SCHEMA_VALIDATOR, ValidationError


class WSTLActionSchemaValidatorTestCase(TestCase):
    def test_valid(self) -> None:
        """Checks if the WeSTL action schema validator does not raise an error when given valid JSON."""
        WSTL_ACTION_SCHEMA_VALIDATOR.validate({
            'name': 'openFile',
            'description': 'Open the selected file',
            'type': 'unsafe',
            'action': 'read',
            'target': 'foo bar',
            'prompt': 'Open',
            'rel': ['foo', 'bar']
        })

    def test_missing_required(self) -> None:
        """
        Checks if the WeSTL action schema validator raises ``ValidationError`` when given JSON that is missing a
        required property.
        """
        self.assertRaises(ValidationError, WSTL_ACTION_SCHEMA_VALIDATOR.validate, {
            'description': 'Open the selected file',
            'type': 'unsafe',
            'action': 'read',
            'target': 'foo bar',
            'prompt': 'Open',
            'rel': ['foo', 'bar']
        })

    def test_bad_type(self) -> None:
        """
        Checks if the WeSTL action schema validator raises ``ValidationError`` when given JSON with a property of an
        invalid type.
        """
        self.assertRaises(ValidationError, WSTL_ACTION_SCHEMA_VALIDATOR.validate, {
            'name': 'openFile',
            'description': 'Open the selected file',
            'type': 'unsafe',
            'action': 'read',
            'target': 'foo bar',
            'prompt': 'Open',
            'rel': ['foo', 'bar'],
            'inputs': 1
        })

    def test_empty(self) -> None:
        """
        Checks if the WeSTL action schema validator raises ``ValidationError`` when given an empty dictionary (``{}``).
        """
        self.assertRaises(ValidationError, WSTL_ACTION_SCHEMA_VALIDATOR.validate, {})


class WSTLSchemaValidatorTestCase(TestCase):
    def test_valid(self) -> None:
        """Checks if the WeSTL schema validator does not raise an error when given valid JSON."""
        WSTL_SCHEMA_VALIDATOR.validate({
            'wstl': {
                'title': 'Foo Bar'
            }
        })

    def test_missing_required(self) -> None:
        """
        Checks if the WeSTL schema validator raises ``ValidationError`` when given JSON that is missing the "wstl"
        property.
        """
        self.assertRaises(ValidationError, WSTL_SCHEMA_VALIDATOR.validate, {
            'notWstl': {
                'title': 'Foo Bar'
            }
        })

    def test_bad_type(self) -> None:
        """
        Checks if the WeSTL schema validator raises ``ValidationError`` when given JSON with a property of an
        invalid type.
        """
        self.assertRaises(ValidationError, WSTL_SCHEMA_VALIDATOR.validate, {
            'wstl': {
                'title': 'Foo Bar',
                'data': [{
                    'subdata': {
                        'foo': 'bar'
                    }
                }]
            }
        })

    def test_empty(self) -> None:
        """
        Checks if the WeSTL schema validator raises ``ValidationError`` when given an empty dictionary (``{}``).
        """
        self.assertRaises(ValidationError, WSTL_SCHEMA_VALIDATOR.validate, {})


class CJTemplateSchemaValidatorTestCase(TestCase):
    def test_valid(self) -> None:
        """Checks if the Collection+JSON template schema validator does not raise an error when given valid JSON."""
        CJ_TEMPLATE_SCHEMA_VALIDATOR.validate({
            'template': {
                'data': [{
                    'name': 'foo',
                    'value': 'bar'
                }]
            }
        })

    def test_missing_required_data_property(self) -> None:
        """
        Checks if the Collection+JSON template schema validator raises ``ValidationError`` when given Collection+JSON
        with data that is missing the "name" property.
        """
        self.assertRaises(ValidationError, CJ_TEMPLATE_SCHEMA_VALIDATOR.validate, {
            'template': {
                'data': [{
                    'value': 'bar'
                }]
            }
        })

    def test_bad_type(self) -> None:
        """
        Checks if the Collection+JSON template schema validator raises ``ValidationError`` when given JSON with a
        property of an invalid type.
        """
        self.assertRaises(ValidationError, CJ_TEMPLATE_SCHEMA_VALIDATOR.validate, {
            'template': {
                'data': 'The quick brown fox jumps over the lazy dog'
            }
        })

    def test_empty(self) -> None:
        """
        Checks if the Collection+JSON template schema validator raises ``ValidationError`` when given an empty
        dictionary (``{}``).
        """
        self.assertRaises(ValidationError, CJ_TEMPLATE_SCHEMA_VALIDATOR.validate, {})


class NVPJSONSchemaValidatorTestCase(TestCase):
    def test_valid(self) -> None:
        """Checks if the name-value-pair JSON schema validator does not raise an error when given valid JSON."""
        NVPJSON_SCHEMA_VALIDATOR.validate({
            'foo': 'bar'
        })

    def test_not_json(self) -> None:
        """
        Checks if the name-value-pair JSON schema validator raises ``ValidationError`` when not given a dictionary.
        """
        self.assertRaises(ValidationError, NVPJSON_SCHEMA_VALIDATOR.validate, 'foo')
