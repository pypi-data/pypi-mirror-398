import warnings

from heaobject.folder import AWSS3Folder, AWSS3ItemInFolder
from heaserver.service.expression import get_eval_for, EvaluatorException
from unittest import TestCase
from typing import Any
from typing import NamedTuple


class BoolExpressionTuple(NamedTuple):
    expr: str
    value: bool


class ExceptionExpressionTuple(NamedTuple):
    expr: str
    value: type[Exception]

# Object passed in is an AWSS3Folder.
TEST_EXPRESSIONS = [
        BoolExpressionTuple(expr='isheaobject(heaobject.folder.AWSS3Folder)', value=True),
        BoolExpressionTuple('display_name == "foobar"', True),
        BoolExpressionTuple('id is not None', True),
        BoolExpressionTuple('id is None or display_name is None', False),
        BoolExpressionTuple('"this" in description', True)
    ]

# Object passed in is an AWSS3Folder; an AWSS3ItemInFolder is passed in as an extra name obj2.
TEST_EXPRESSIONS_WITH_EXTRA = [
        BoolExpressionTuple(expr='isheaobject(heaobject.folder.AWSS3ItemInFolder)', value=False),
        BoolExpressionTuple('"this" in obj2.description if obj2.description else False', False),
        BoolExpressionTuple('display_name == obj2.display_name', True),
        BoolExpressionTuple('description == obj2.description', False),
        BoolExpressionTuple('display_name is None and description is None', False)
    ]

TEST_EXPRESSIONS_THROWING_EXCEPTIONS = [
    ExceptionExpressionTuple('notaname is None', EvaluatorException),
    ExceptionExpressionTuple('4 of None', SyntaxError),
    ExceptionExpressionTuple('notaname of None', SyntaxError),
    ExceptionExpressionTuple('isinstance(obj2, heaobject.folder.AWSS3Folder)', EvaluatorException),
    ExceptionExpressionTuple('def foo: pass', SyntaxError),
    ExceptionExpressionTuple('def foo: print(notaname)', SyntaxError),
    ExceptionExpressionTuple('def foo(): pass', EvaluatorException),
    ExceptionExpressionTuple('class Foo: pass', EvaluatorException),
    ExceptionExpressionTuple('class Foo: a = notaname', EvaluatorException),
    ExceptionExpressionTuple('foo = "bar"', EvaluatorException),
    ExceptionExpressionTuple('if 4 == 3: print(5)', EvaluatorException),
    ExceptionExpressionTuple('while True: print("hello world")', EvaluatorException)
]

class TestEvaluator(TestCase):

    def setUp(self) -> None:
        obj = AWSS3Folder()
        obj.display_name = 'foobar'
        obj.description = 'this is a description'

        self.eval_ = get_eval_for(obj).eval

    def test_empty_string(self):
        with self.assertRaises(EvaluatorException):
            self.eval_('')

    def test_None_expression(self):
        with self.assertRaises(EvaluatorException):
            self.eval_(None)

def _my_test_generator(expr: str, expected: Any):
    def test_(self):
        self.assertEqual(expected, self.eval_(expr))
    return test_


for test_case in TEST_EXPRESSIONS:
    test_case_name = test_case.expr if test_case.expr else 'empty_expression'
    setattr(TestEvaluator, f'test_{test_case_name}', _my_test_generator(test_case.expr, test_case.value))


class TestEvaluatorDict(TestCase):

    def setUp(self) -> None:
        obj = AWSS3Folder()
        obj.display_name = 'foobar'
        obj.description = 'this is a description'

        self.eval_ = get_eval_for(obj.to_dict()).eval


for test_case in TEST_EXPRESSIONS:
    test_case_name = test_case.expr if test_case.expr else 'empty_expression'
    setattr(TestEvaluatorDict, f'test_{test_case_name}', _my_test_generator(test_case.expr, test_case.value))


class TestEvaluatorWithExtra(TestCase):

    def setUp(self) -> None:
        obj = AWSS3Folder()
        obj.display_name = 'foobar'
        obj.description = 'this is a description'

        obj2 = AWSS3ItemInFolder()
        obj2.display_name = 'foobar'

        self.eval_ = get_eval_for(obj, extra_names={'obj2': obj2}).eval


def _my_test_generator_with_extra(expr: str, expected: Any):
    def test_(self: TestEvaluatorWithExtra):
        self.assertEqual(expected, self.eval_(expr))
    return test_


for test_case in TEST_EXPRESSIONS_WITH_EXTRA:
    setattr(TestEvaluatorWithExtra, f'test_{test_case.expr}', _my_test_generator_with_extra(test_case.expr, test_case.value))


class TestEvaluatorWithExtraDict(TestCase):

    def setUp(self) -> None:
        obj = AWSS3Folder()
        obj.display_name = 'foobar'
        obj.description = 'this is a description'

        obj2 = AWSS3ItemInFolder()
        obj2.display_name = 'foobar'

        self.eval_ = get_eval_for(obj.to_dict(), extra_names={'obj2': obj2}).eval


for test_case in TEST_EXPRESSIONS_WITH_EXTRA:
    setattr(TestEvaluatorWithExtraDict, f'test_{test_case.expr}', _my_test_generator_with_extra(test_case.expr, test_case.value))



class TestEvaluatorThrowingExceptions(TestCase):
    def setUp(self) -> None:
        obj = AWSS3Folder()
        obj.display_name = 'foobar'
        obj.description = 'this is a description'

        obj2 = AWSS3ItemInFolder()
        obj.display_name = 'foobar'

        self.eval_ = get_eval_for(obj, extra_names={'obj2': obj2}).eval


def _my_test_generator_throwing_exceptions(expr: str, expected: type[Exception]):
    def test_(self):
        with self.assertRaises(expected):
            self.eval_(expr)
    return test_


for test_case in TEST_EXPRESSIONS_THROWING_EXCEPTIONS:
    setattr(TestEvaluatorThrowingExceptions, f'test_{test_case.expr}', _my_test_generator_throwing_exceptions(test_case.expr, test_case.value))


class TestEvaluatorThrowingExceptionsDict(TestCase):
    def setUp(self) -> None:
        obj = AWSS3Folder()
        obj.display_name = 'foobar'
        obj.description = 'this is a description'

        obj2 = AWSS3ItemInFolder()
        obj.display_name = 'foobar'

        self.eval_ = get_eval_for(obj.to_dict(), extra_names={'obj2': obj2}).eval


for test_case in TEST_EXPRESSIONS_THROWING_EXCEPTIONS:
    setattr(TestEvaluatorThrowingExceptionsDict, f'test_{test_case.expr}', _my_test_generator_throwing_exceptions(test_case.expr, test_case.value))
