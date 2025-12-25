import inspect
import typing
from typing import Any, Callable, get_origin, Generic, overload
from types import UnionType
from kisa_utils.response import Response

from typing import ParamSpec, TypeVar, Type
P = ParamSpec('P')
T = TypeVar('T')

class Value(Generic[T]):
    @overload
    def __init__(self, valueType:Type[T], validator:Callable[[T], Response],/) -> None: ...

    @overload
    def __init__(self, valueType:Type[T] | TypeVar, validator:Callable[[T], Response],/) -> None: ...

    def __init__(self, valueType, validator, /) -> None:
        '''
        create a value definition to be used by `kisa_utils.structures.validator.validate`

        Args:
            valueType(Any): The type of the value eg `int` or `int|float`
            validator(Callable): Callable, the function to call for each value instance. 
                    the function should
                    - take a single argument; this will be the instance value
                    - return a standard KISA response object
        '''

        if not (isinstance(valueType, UnionType) or type(valueType)==type(type)):
            raise TypeError(f'Invalid `valueType` given expected Type|UnionType')

        if not validator:
            raise TypeError(f'invalid/no `validator` given')

        if not (inspect.isfunction(validator) or inspect.ismethod(validator)):
            raise TypeError('Invalid `validator` given. Expected function|method')
        

        if 1 != len(inspect.signature(validator).parameters):
            raise TypeError(f'validator should take only 1 argument (not counting `self` for methods)')
        
        reply = validator(
            valueType() if type(valueType)==type(type) \
            else (
                (
                    _:=list(typing.get_args(valueType))[0]
                ) 
                and (
                    get_origin(_) or _
                )
            )()
        )

        if not isinstance(reply, Response):
            raise TypeError(f'`validator` must return kutils.response.Response object')

        typesTuple = valueType

        self._valueType = typesTuple
        self._validator = validator
    
    def validate(self, valueInstance:Any, /) -> Response:
        '''
        attempt to validate the `valueInstance` against the value `validator` passed to the constructor
        '''
        return self._validator(valueInstance)

    @property
    def __name__(self) -> str:
        '''
        get the name of the value-type
        '''
        if not isinstance(self._valueType, UnionType):
            _type = (get_origin(self._valueType) or self._valueType).__name__
        else:
            types = self._valueType.__args__
            _type = '|'.join(_.__name__ for _ in types)
        
        return _type 

    def __str__(self) -> str:  return self.__name__
    def __repr__(self) -> str:  return self.__name__
