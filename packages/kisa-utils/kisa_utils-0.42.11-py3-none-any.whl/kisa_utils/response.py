import json as _j; encodeJSON = _j.JSONEncoder().encode
from typing import Any
import inspect

# we inherit from <tuple> simply to make sure the response object is accepted 
# as a return value for a Flask view-function
class Response(tuple):
    def __new__(cls, status:bool, /, *, log:str='', data:Any=None):
        return super().__new__(cls, ())  # Create an empty tuple

    def __init__(self, status:bool, /, *, log:str='', data:Any=None) -> None:
        '''
        create a Response object
        Args:
            status(bool): the response status
            log(str): the log in case the status is `False`
            data(Any): any data to be passed on when status = `True`
        '''

        stack = inspect.stack()

        if stack[0].filename != stack[1].filename:
            raise Exception(f'the `Response` object can not be initiated directly. please use one of `Ok` or `Error`')
        
        if not isinstance(status,bool):
            raise TypeError(f'`status` expected to be a bool')

        if not isinstance(log,str):
            raise TypeError(f'`log` expected to be a string')

        log = log.strip()

        if (not status) and (not log):
            raise ValueError(f'not effective `log` provided for `status` of False')

        if (not status) and data:
            raise ValueError(f'`data` provided for `status` of False')

        self.__status = status
        self.__log = log
        self.__data = data

    # to enable an instance to be used in cmoparison statements
    def __bool__(self): return self.__status

    # to enable the isntance to be acknowleged as a valid Flask view-function response
    # **************************************************************************
    def __len__(self): return 2

    def __getitem__(self, index):
        if isinstance(index, int):
            if index > 1:
                raise ValueError('only indices 0 and 1 accepted')
            return {'status':self.__status, 'log':self.__log, 'data':self.__data} if 0==index else 200
        
        if (value := {
            'status': self.__status,
            'log': self.__log,
            'data': self.__data,
        }.get(index, self)) != self:
            return value

        if not isinstance(self.__data, dict) or (index not in self.__data):
            return self.__data

        return self.__data[index]
        
    def __getattr__(self, attr):
        return self[attr]

    def __iter__(self):
        return iter([self[0], self[1]])
    # **************************************************************************

    @property
    def status(self) -> bool:
        '''
        return the status of the response object
        '''
        return self.__status

    @property
    def log(self) -> str: 
        '''
        return the log of the response object
        '''
        return self.__log

    @property
    def data(self) -> Any: 
        '''
        return the data of the response object
        '''
        return self.__data

    @property
    def asDict(self) -> dict: 
        '''
        return the dict-representation of the response object

        Returns:
            ```
            {
                'status': bool, 
                'log':str, 
                'data':Any
            }
            ```
        '''
        return {'status':self.__status, 'log':self.__log, 'data':self.__data}

    @property
    def asJSON(self): 
        '''
        return the json-representation of the response object

        Returns:
            ```
            # json-representation of this
            {
                'status': bool, 
                'log':str, 
                'data':Any
            }
            ```
        '''
        return encodeJSON(self.asDict)
    
    def __repr__(self):
        return f'Reponse(status={self.__status}, log="{self.__log}", data={self.__data})'

def Ok(data:Any=None) -> Response:
    '''
    create an Ok response ie a Response object with status set to `True`
    Args:
        data(Any): the data to pass to the Response object
    '''
    return Response(True, data=data)

def Error(log:str) -> Response:
    '''
    create an Error response ie a Response object with status set to `False`
    Args:
        log(str): the log to pass to the Response object
    '''
    return Response(False, log=log)

if __name__=='__main__':
    r = Ok(74); print(r['xx'], r.xx, r['xy'], r.data, r)
    r = Ok({'xx':50}); print(r['xx'], r.xx, r['xy'], r['data'], r)
    r = Ok({'xx':{'a':13}}); print(r['xx']['a'], r.xx['a'], r['data'], r)