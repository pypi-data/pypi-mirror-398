import unittest
from heaserver.service.jsonschemavalidator import ValidationError, WSTL_SCHEMA_VALIDATOR
import json
from pkgutil import get_data
from heaserver.service import wstl, jsonschema


class TestDocumentData(unittest.TestCase):

    def __init__(self, methodName: str = 'runTest'):
        super().__init__(methodName=methodName)
        self.maxDiff = None

    def setUp(self):
        self.expected_wstl = {
            'wstl': {
                'actions': [],
                'title': 'Registry components'
            }
        }

    def tearDown(self):
        self.expected_wstl = None

    def test_get_design_time_document(self):
        wstl_builder = wstl.RuntimeWeSTLDocumentBuilder(self.expected_wstl)
        self.assertEqual(self.expected_wstl, wstl_builder.design_time_document)

    def test_get_run_time_document(self):
        wstl_builder = wstl.RuntimeWeSTLDocumentBuilder(self.expected_wstl)
        self.assertEqual(self.expected_wstl, wstl_builder())

    def test_load(self):
        self.assertIsNotNone(wstl.builder('servicetest'))

    def test_find(self):
        wstl_builder = wstl.builder('servicetest')
        self.assertEqual({
            "name": "component-get-open-choices",
            "type": "safe",
            "target": "item read cj",
            "prompt": "Open as..."
        },
            wstl_builder.find_action('component-get-open-choices'))

    def test_get_run_time_wstl_from_builder(self):
        self.assertEqual(self.expected_wstl, wstl.builder('servicetest')())

    def test_get_run_time_wstl_from_builder_factory(self):
        self.assertEqual(self.expected_wstl,
                         wstl.builder_factory('servicetest')()())

    def test_validate_run_time_wstl_1(self):
        jsn = json.loads(get_data(__package__, 'wstl_1.json'))
        try:
            WSTL_SCHEMA_VALIDATOR.validate(jsn)
        except ValidationError as e:
            self.fail(e)

    def test_validate_run_time_wstl_string_boolean(self):
        jsn = json.loads(get_data(__package__, 'wstl_2.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_validate_run_time_wstl_notsafe(self):
        jsn = json.loads(get_data(__package__, 'wstl_3.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_validate_run_time_wstl_missing_name(self):
        jsn = json.loads(get_data(__package__, 'wstl_4.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_validate_run_time_wstl_just_data(self):
        jsn = json.loads(get_data(__package__, 'wstl_5.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_validate_run_time_wstl_actions_not_an_array(self):
        jsn = json.loads(get_data(__package__, 'wstl_6.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_validate_run_time_wstl_wrong_content(self):
        jsn = json.loads(get_data(__package__, 'wstl_7.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_validate_run_time_wstl_wrong_related(self):
        jsn = json.loads(get_data(__package__, 'wstl_8.json'))
        with self.assertRaises(ValidationError):
            WSTL_SCHEMA_VALIDATOR.validate(jsn)

    def test_add_design_time_action_check_design_time_schema(self):
        wstl_builder = wstl.RuntimeWeSTLDocumentBuilder(self.expected_wstl)
        jsn = json.loads(get_data(__package__, 'wstl_9.json'))
        wstl_builder.add_design_time_action(jsn)
        self.assertEqual(
            [jsn], wstl_builder.design_time_document['wstl']['actions'])

    def test_add_design_time_action_check_run_time_schema(self):
        wstl_builder = wstl.RuntimeWeSTLDocumentBuilder(self.expected_wstl)
        jsn = json.loads(get_data(__package__, 'wstl_9.json'))
        wstl_builder.add_design_time_action(jsn)
        self.assertEqual([], wstl_builder()['wstl']['actions'])

    def test_validate_with_duplicate_action(self):
        wstl_ = {
            'wstl': {
                'actions': [
                    {
                        'name': 'foo'
                    },
                    {
                        'name': 'foo'
                    }
                ],
                'title': 'Registry components'
            }
        }
        self.assertRaises(ValueError, wstl.validate, wstl_)

    def test_add_duplicate_action(self):
        wstl_ = {
            'wstl': {
                'actions': [
                    {
                        'name': 'foo'
                    }
                ],
                'title': 'Registry components'
            }
        }
        builder = wstl.RuntimeWeSTLDocumentBuilder(design_time_wstl=wstl_)
        self.assertRaises(
            ValueError, builder.add_design_time_action, {'name': 'foo'})

    def test_related(self):
        wstl_ = {
            "wstl": {
                "related": {
                    "typeList": []
                }
            }
        }
        self.assertTrue(WSTL_SCHEMA_VALIDATOR.is_valid(wstl_))

    def test_empty_related(self):
        wstl_ = {
            'wstl': {
                'related': {

                }
            }
        }
        self.assertRaises(
            ValidationError, WSTL_SCHEMA_VALIDATOR.validate, wstl_)

    def test_related_not_array(self):
        wstl_ = {
            'wstl': {
                'related': {
                    'foo': 'bar'
                }
            }
        }
        self.assertRaises(
            ValidationError, WSTL_SCHEMA_VALIDATOR.validate, wstl_)

    def test_merge_run_time(self):
        base = json.loads(get_data(__package__, 'wstl_10a.json'))
        head = json.loads(get_data(__package__, 'wstl_10b.json'))
        expected = json.loads(get_data(__package__, 'wstl_11.json'))
        self.assertEqual(expected, wstl.merge(base, head))
