import inspect
from functools import wraps
import os
from types import UnionType
from kisa_utils.response import Response, Ok, Error
from kisa_utils.storage import Path
from kisa_utils.structures.validator import Value, validateWithResponse
import copy
from typing import Any, get_args, Callable

class Definition:
    @staticmethod
    def __class_getitem__(structure:Any) -> Any:
        return structure

def private(func:Callable) -> Callable:
    '''
    decorator to ensure a function is used only in the same module as that in which its defined
    * if multiple decorators are used, this has to be the closest to the function being decorated
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        expectedModule = inspect.getfile(func)
        stack = inspect.stack()
        stackCallerModules = [(s.function,s.filename) for s in stack if ('<frozen' not in s.filename)]

        callingModule = stackCallerModules[1][1]
        # print(Path.getMyAbsolutePath())
        # from pprint import pprint; pprint(stackCallerModules)
        # print(expectedModule, callingModule, expectedModule == callingModule)
        if expectedModule != callingModule:
            raise Exception(f"can't call private function `{func.__name__}` from external module")

        return func(*args, **kwargs)
    return wrapper

def protected(func:Callable) -> Callable:
    '''
    decorator to ensure a function is used only in the same module as that in which its defined as well as modules written in child paths

    Note:
        function is only allowed to be used in;
        * the module in which its defined
        * submodules starting in the defining module's path
    Note:
    * if multiple decorators are used, this has to be the closest to the function being decorated
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        expectedModule = inspect.getfile(func)
        stack = inspect.stack()
        stackCallerModules = [(s.function,s.filename) for s in stack if ('<frozen' not in s.filename)]

        callingModule = stackCallerModules[1][1]
        # print(expectedModule, callingModule)
        if not callingModule.startswith(os.path.dirname(expectedModule)):
            raise Exception(f"can't call protected function `{func.__name__}` from path outside definition module path")

        return func(*args, **kwargs)
    return wrapper

# ------------------------------------------------------------------------------
from typing import ParamSpec, TypeVar
P = ParamSpec('P')
T = TypeVar('T')

def enforceRequirements(func:Callable[P, T]) -> Callable[P, T]:
    '''
    force decorated function to observe the following
    - have type hints for all `args`, and `kwargs` as well as the `return` type-hint
    - have all args passed either as POSITION-ONLY or KEYWORD-ONLY
    - have a non-empty docstring
    - ensure all arguments are given values of the right type when the function is called
    - return the right data-type as specified by the return type-hint when invoked
    '''
    signature = inspect.signature(func)
    typeHints = func.__annotations__
    if 1:
        parameters = signature.parameters

        if not (func.__doc__ and func.__doc__.strip()):
            raise ValueError(
                f"function/method `{func.__name__}` has no docString!")

        if -1 == typeHints.get("return", -1):
            raise TypeError(
                f"function/method `{func.__name__}` has no return type")

        registeredArgs = []
        registeredKwargs = {}

        argCount = 0
        for key, value in signature.parameters.items():
            argCount += 1
            if (key in ['self', 'cls']) and 1==argCount:
                registeredArgs.append((key, None))
                continue

            hint = typeHints.get(key, None)
            if not hint:
                raise TypeError(f"function/method `{func.__name__}`: parameter `{key}` has no type hint")

            if value.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError(
                    f"function/method `{func.__name__}` should take either positional-only or keyword-only parameters. `{key}` is neither")

            if value.kind == inspect.Parameter.POSITIONAL_ONLY:
                if value.default is not inspect.Parameter.empty:
                    if not (resp := validateWithResponse(value.default, typeHints[key])):
                        raise ValueError(f'arg `{key}` default value: {resp.log}')

                registeredArgs.append((key, typeHints[key] ))
            elif value.kind == inspect.Parameter.KEYWORD_ONLY:
                if value.default is not inspect.Parameter.empty:
                    if not (resp := validateWithResponse(value.default, typeHints[key])):
                        raise ValueError(f'kwarg `{key}` default value: {resp.log}')
                registeredKwargs[key] = typeHints[key]

            if str(value).startswith('*'):
                raise ValueError(
                    f'function/method `{func.__name__}`: *{key} or **{key} not allowed in function signature')

        expectectedReturnType = typeHints['return']

        # print(registeredArgs, registeredKwargs)

    @wraps(func)
    def w(*args:P.args, **kwargs:P.kwargs):
        for index, arg in enumerate(args):
            if (registeredArgs[index][0] in ['self', 'cls']) and 0==index: continue
            if not (resp := validateWithResponse(arg, registeredArgs[index][1])):
                log = f'arg `{registeredArgs[index][0]}`, arg-index {index}: {resp.log}'
                if Response == expectectedReturnType: return Error(log)
                raise ValueError(log)

        for kwarg in kwargs:
            if kwarg not in registeredKwargs:
                print(f'[VALIDATOR WARNING]: kwarg `{kwarg}` was not part of function `{func.__name__}` definition so its type hints cant be enforced')
                continue

            if not (resp := validateWithResponse(kwargs[kwarg], registeredKwargs[kwarg])):
                log = f'kwarg `{kwarg}`: {resp.log}'
                if Response == expectectedReturnType: return Error(log)
                raise ValueError(log)

        functionResp = func(*args, **kwargs)

        # if not isinstance(resp, expectectedReturnType):
        if not (resp := validateWithResponse(functionResp, expectectedReturnType)):
            if Response == expectectedReturnType: return Error(resp.log)

            raise TypeError(f'`{func.__name__}` return error: {resp.log}')

        return functionResp

    return w
