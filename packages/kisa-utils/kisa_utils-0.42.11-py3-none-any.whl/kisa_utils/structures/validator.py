'''
this modules handle data structure validation to ensure that
data is passed in expected formats/structures
'''

from typing import Any, get_args, get_origin, Callable
from types import UnionType
from kisa_utils.structures.utils import Value
from kisa_utils.response import Response, Ok, Error
from kisa_utils.dataStructures import KDict

def validate(instance:Any, structure:Any, path:str='$') -> dict:
    '''
    validate payload/instance against a pre-defined structure
    Args:
        instance(Any): the isntance/value to validate
        structure(Any): the structure against which to validate the `instance`
        path(str): the path to the instance in the structure. this is intended for internal use
    
    Returns:
    ```
    {
        "status": bool,
        "log": str
    }
    ```
    '''
    
    result = {'status':False, 'log':''}

    if not isinstance(structure, UnionType) and get_origin(structure):
        structure = get_origin(structure)

    # union types such as int|float...
    if isinstance(structure, UnionType):
        if not isinstance(instance, tuple([get_origin(t) or t for t in get_args(structure)])):
            expectedTypes = [str(_).split("'")[1] for _ in tuple([(get_args(t) or t) for t in get_args(structure)])]
            result['log'] = f'E06: types not similar:: {path}, expected one of {"|".join(expectedTypes)} but got {str(type(instance))[7:-1]}'
            return result

    # when the structure is a block type/class eg dict,list,tuple,etc
    elif type(structure)==type(type) or isinstance(structure, Value) or get_args(type):
        _structure = structure._valueType if isinstance(structure, Value) else (get_args(structure) or structure)

        if instance != _structure and not isinstance(instance, _structure):
            result['log'] = f'E01: types not similar:: {path}, expected {str(_structure)[7:-1] if type(structure)==type(type) else structure.__name__} but got {str(type(instance))[7:-1]}'
            return result

        if isinstance(structure, Value):
            if not (response:=structure.validate(instance)):
                result['log'] = f'E01-01: {path}:: validator error({response.log})'
                return result

        result['status'] = True
        return result
    else:
        if isinstance(structure, Callable):
            if not callable(instance):
                result['log'] = f'E07: types not similar:: {path}, expected a Callable but got {str(type(instance))[7:-1]}'
            else:
                result['status'] = True

            return result

        # checking in both directions as dict and KDict can fail when you check 
        # `isinstance(dict, KDict)` but will pass when the arguments switch positions
        if (not isinstance(instance,type(structure))) and (not isinstance(structure, type(instance))):
            result['log'] = f'E02: types not similar:: {path}, expected {str(type(structure))[7:-1]} but got {str(type(instance))[7:-1]}'
            return result

        if isinstance(structure,(dict, KDict)):
            _path = path
            for key in structure:
                path = f'{_path}->{key}'
                if key not in instance:
                    result['log'] = f'E03: missing key:: {path}'
                    return result
                res = validate(instance[key],structure[key], path=path)
                if not res['status']:
                    return res
        elif isinstance(structure,(list,tuple)):
            _path = path
            for index,item in enumerate(structure):
                path = f'{_path}->[#{index}]'
                if len(instance)<=index:
                    expectedTypes = str(type(item))[7:-1] if not isinstance(item,type) else str(item)[7:-1]
                    if isinstance(item, UnionType):
                        expectedTypes = "|".join([str(_).split("'")[1] for _ in get_args(item)])

                    result['log'] = f'E04: missing item at index:: {path}, expects {expectedTypes}'
                    return result
                res = validate(instance[index],item, path=path)
                if not res['status']:
                    return res

    result['status'] = True
    return result

def validateWithResponse(instance:Any, structure:Any) -> Response:
    '''
    validate payload/instance against a pre-defined structure
    Args:
        instance(Any): the isntance/value to validate
        structure(Any): the structure against which to validate the `instance`
    '''
    response = validate(instance, structure)
    if response['status']: return Ok()
    return Error(response['log'])