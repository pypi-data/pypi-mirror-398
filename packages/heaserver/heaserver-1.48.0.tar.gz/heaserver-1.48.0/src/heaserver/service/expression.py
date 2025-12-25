"""
An expression evaluator, customized for HEA. It's like the built-in eval function, but safe. Only the following names,
operators, and functions will be made available:

Names:
    All HEAObject classes, subclasses, packages, and modules in the heaobject library that do not begin
    with an underscore.
    All attributes of the provided HEAObject, provided by the get_attributes method.

Operators:
    All math, boolean, and equality operators.

Functions:
    is_heaobject(cls: HEAObject): returns whether the object is an instance of the provided class.

Examples:
    >>> from heaobject.folder import AWSS3Folder
    >>> from heaserver.service.expression import get_eval_for
    >>> obj = AWSS3Folder()
    >>> obj.display_name = 'foobar'
    >>> obj.description = 'this is a description'
    >>> eval_ = get_eval_for(obj).eval
    >>> print(eval_('isheaobject(heaobject.folder.AWSS3Folder)'))
    >>> print(eval_('display_name == "foobar"'))
    >>> print(eval_('id is not None'))
    >>> print(eval_('id is None or display_name is None'))
    >>> print(eval_('"this" in description'))

"""
import warnings

from simpleeval import SimpleEval, NameNotDefined, FunctionNotDefined, FeatureNotAvailable, AssignmentAttempted
from typing import Protocol, Any
import heaobject
from heaobject.root import HEAObject, HEAObjectDict, from_dict
from collections.abc import Mapping
import importlib, pkgutil, inspect, heaobject


class EvalProtocol(Protocol):
    """
    A protocol for objects with an eval method accepting one parameter, an expression string.
    """
    def eval(self, expr: str):
        """
        Evaluates the provided expression.

        :param expr: the expression string.
        :return: the value of the expression.
        :raises EvaluatorExpression: if a parsing error occurs.
        """
        ...


class EvaluatorException(ValueError):
    """
    Raised when a parsing error occurs evaluating the expression.
    """
    pass


class Evaluator:
    """
    An expression evaluator, customized for HEA.
    """
    def __init__(self, wrapped: EvalProtocol):
        self.__wrapped = wrapped

    def eval(self, expr: str) -> Any:
        """
        Evaluates the provided expression.

        :param expr: the expression string. Cannot be None or the empty string.
        :return: the value of the expression.
        :raises EvaluatorExpression: if a parsing error occurs.
        """
        if expr is None:
            raise EvaluatorException(f'Expression cannot be None')
        elif not expr:
            raise EvaluatorException(f'Expression cannot be the empty string')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error')
                return self.__wrapped.eval(expr)
        except (NameNotDefined, FunctionNotDefined, FeatureNotAvailable) as e:
            raise EvaluatorException(str(e)) from e
        except AssignmentAttempted as e:
            raise EvaluatorException(f'Assignment {expr} attempted')


def get_eval_for(obj: HEAObject | HEAObjectDict, extra_functions: Mapping[str, Any] | None = None, extra_names: Mapping[str, Any] | None = None) -> EvalProtocol:
    """
    Creates an expression evaluator, customized for HEA. Loads the provided HEAObject, as well as any provided extra
    names.

    :param obj: the HEAObject to load into the evaluator (required).
    :param extra_functions: a mapping of function names to functions to make available to the evaluator. It automatically
    adds the isheaobject function, which returns whether the object is an instance of the provided class. Passing a
    function with the same name will override the default isheaobject function.
    :param extra_names: any extra names to make available to the evaluator.
    :return: an object implementing the EvalProtocol protocol.

    Attempts at variable assignment will be ignored, but a warning will be generated. The type of warning is undefined
    beyond being a UserWarning.
    """
    names: dict[str, Any] = {}
    names[heaobject.__name__] = heaobject
    for module in pkgutil.iter_modules(heaobject.__path__, prefix='heaobject.'):
        module_ = importlib.import_module(module.name)
        if not any(module_part.startswith('_') for module_part in module.name.split('.')):
            names[module.name] = module_
        for name, cls in inspect.getmembers(module_):
            if inspect.isclass(cls) and issubclass(cls, HEAObject):
                names[name] = cls

    hea_obj, obj_dict = (obj, obj.to_dict()) if isinstance(obj, HEAObject) else (from_dict(obj), obj)
    names.update(obj_dict)
    if extra_names:
        names.update(extra_names)

    def isheaobject(cls: type[HEAObject]):
        if issubclass(cls, HEAObject):
            return isinstance(hea_obj, cls)
        else:
            raise ValueError(f'cls {cls} is not a HEAObject')

    functions = {'isheaobject': isheaobject}
    functions.update(extra_functions or {})

    return Evaluator(SimpleEval(functions=functions, names=names))

