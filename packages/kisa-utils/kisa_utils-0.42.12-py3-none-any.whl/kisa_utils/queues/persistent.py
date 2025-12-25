from kisa_utils.db import Handle
from kisa_utils.queues.callables import queueCallsInThreads
from kisa_utils.response import Response, Error, Ok
from kisa_utils.dataStructures import KDict
from kisa_utils.storage import Path
from kisa_utils import dates
from kisa_utils.functionUtils import enforceRequirements
from kisa_utils.structures.utils import Value

from typing import Callable

class __PersistentQueueSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if not args:
            raise Exception(f'invalid instantiation of {cls}')
        id = args[0]
        storageLocation = kwargs.get('storageLocation', '')

        if not id.isalnum():
            raise ValueError('persistent queue ID should be an alphanumeric value ie a-zA-Z0-9 with no special characters or spaces')

        idKey = f'{storageLocation}:{id}'

        if idKey not in cls._instances:
            cls._instances[idKey] = super().__call__(*args, **kwargs)

        return cls._instances[idKey]

class PersistentQueue(metaclass=__PersistentQueueSingleton):
    __openedQueues:dict = {} # name: PersistentQueue

    __allowedDataTypes = str|int|float|dict|KDict|list|tuple|set

    __dataTypeCasts = {
        'str': str,
        'int': int,
        'float': float,
        'dict': dict,
        'KDict': KDict,
        'list': list,
        'tuple': tuple,
        'set': set
    }

    __defaultDirectoryName:str = '.kisaPersistentQueues'
    __defaultStorageLocation:str = Path.join(Path.HOME, __defaultDirectoryName)

    __schema = {
        'data': '''
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tstamp    VARCHAR(30) NOT NULL,
            dataType  VARCHAR(30) NOT NULL,
            data      JSON NOT NULL
        ''',
    }


    def __init__(self, id:str, /, *, storageLocation:str=''):
        '''
        create a new thread-safe PersistentQueue
        Args:
            id(str): the Queue ID. queue sharing an ID will all reference the same underwlying queue
            storageLocation(str): if provided, the location to store the queue. if not provided, data is stored in the default location. use `obj.defaultStorageLocation` to get the default storage directory
        '''

        if storageLocation:
            if not Path.exists(storageLocation):
                raise Exception(f'could not find storage directory: `{storageLocation}`')
        else:
            storageLocation = self.__defaultStorageLocation
            if not Path.exists(storageLocation) and not Path.createDirectory(storageLocation):
                raise Exception(f'failed to create storage directory: `{storageLocation}`')

        self.__length:int = 0
        self.id = id

        self.dbPath = Path.join(storageLocation, self.id)

        # ensure thread safety throughout the running program
        self.append = queueCallsInThreads(self.append, group=self.id)
        self.peek = queueCallsInThreads(self.peek, group=self.id)
        self.pop = queueCallsInThreads(self.pop, group=self.id)
        self.process = queueCallsInThreads(self.process, group=self.id)
        
        self.__load__ = queueCallsInThreads(self.__load__, group = "pqueue__load__")

        if not (resp := self.__load__()):
            raise Exception(f'P-QUEUE DB LOAD ERROR: {resp.log}')

    @property
    def defaultStorageLocation(self):
        '''
        get the default storage location
        '''
        return self.__defaultStorageLocation

    @property
    def allowedDataTypes(self):
        '''
        get data types allowed in the queue
        '''
        return self.__allowedDataTypes

    @property
    def length(self) -> int:
        '''
        get number of items in the queue
        '''
        return self.__length

    def __len__(self) -> int:
        return self.length

    def __load__(self) -> Response:
        '''
        load underlying queue database
        '''

        with Handle(self.dbPath, tables=self.__schema, returnKISAResponse=True) as handle:
            if not (resp := handle.fetch('data', ['count(*)'],'',[])):
                return resp
            
            self.__length = resp.data[0][0]

        return Ok()

    def __resolveIndex(self, index:int) -> Response:
        '''
        resolve index and determine if its legitimate
        '''
        if index<0:
            index = self.__length + index

        if not (0 <= index < self.__length):
            return Error(f'invalid index given for persistent queue of length {self.__length}')

        return Ok(index)

    @enforceRequirements
    def append(self, data:__allowedDataTypes, /) -> Response:
        '''
        append to the queue
        Args:
            data(__allowedDataTypes): the data to insert, use `obj.allowedDataTypes` to get the list of allowed data types
        '''

        try:
            dataType = type(data).__name__
        except:
            return Error(f'failed to get data-type of `{data}`')


        with Handle(self.dbPath, readonly=False, returnKISAResponse=True) as handle:
            if not (resp := handle.insert('data', [
                None,
                dates.currentTimestamp(),
                dataType,
                data
            ])):
                return resp
            
        self.__length += 1
        return Ok(self.__length)

    @enforceRequirements
    def peek(self, index:int, /) -> Response:
        '''
        get data at `index` without popping it from the queue
        '''
        if not (resp := self.__resolveIndex(index)): return resp
        index = resp.data

        with Handle(self.dbPath, returnKISAResponse=True) as handle:
            if not (resp := handle.fetch('data', ['dataType', 'data'],'1 order by id',[],limit=1, offset=index, parseJson=True)):
                return resp
            
            dataType, data = resp.data[0]

        try:
            data = self.__dataTypeCasts[dataType](data)
        except:
            return Error(f'failed to convert value to data-type `{dataType}`. the database was most likely corrupted')

        return Ok(data)

    @enforceRequirements
    def pop(self, index:int = 0, /) -> Response:
        '''
        get data at `index` and remove it from the queue
        '''
        if not (resp := self.__resolveIndex(index)): return resp
        index = resp.data

        with Handle(self.dbPath, readonly=False, returnKISAResponse=True) as handle:
            if not (resp := handle.fetch('data', ['id','dataType', 'data'],'1 order by id',[],limit=1, offset=index, parseJson=True)):
                return resp
            
            rowId, dataType, data = resp.data[0]

            try:
                data = self.__dataTypeCasts[dataType](data)
            except:
                return Error(f'failed to convert value to data-type `{dataType}`. the database was most likely corrupted')

            if not (resp := handle.delete('data','id=?',[rowId])):
                return resp

            self.__length -= 1

        return Ok(data)

    @enforceRequirements
    def process(self, index:int, handler:Callable[...,Response], /, *, popOnHandlerSuccess:bool=True, popOnHandlerError:bool=False) -> Response:
        '''
        process item at `index` by passing it as an argument to `handler`
        Args:
            index(int): the index to process
            handler(Callable): a function/method that takes a single argument and returns a `Response` object
            popOnHandlerSuccess(bool): a bool indicating if the item should be poppoed if `handler` returns as `Ok` object
            popOnHandlerError(bool): a bool indicating if the item should be poppoed if `handler` returns as `Error` object

        Returns:
            `Ok` object with a KDict containing the processed item along with if or not it was popped if all goes well, `Error` object otherwise
        '''

        if not (resp := self.peek(index)):
            return resp

        item = resp.data
        try:
            handlerResp = handler(item)
        except Exception as e:
            return Error(str(e))

        if not isinstance(handlerResp, Response):
            return Error(f'{handler.__name__} did not return a {Response} object!')

        popped:bool = False

        if handlerResp and popOnHandlerSuccess:
            if not (resp := self.pop(index)):
                ...
            popped = True

        if not handlerResp and popOnHandlerError and not popped:
            if not (resp := self.pop(index)):
                ...
            popped = True

        if (popOnHandlerSuccess or popOnHandlerError) and not popped:
            # what do we do in such a case?
            ...

        return Ok(KDict({
            'item': item,
            'popped': popped
        }))

    @enforceRequirements
    def processAll(self, handler:Callable[...,Response], /, *, popOnHandlerSuccess:bool=True, popOnHandlerError:bool=False) -> Response:
        '''
        process item at `index` by passing it as an argument to `handler`
        Args:
            handler(Callable): a function/method that takes a single argument and returns a `Response` object
            popOnHandlerSuccess(bool): a bool indicating if the item should be poppoed if `handler` returns as `Ok` object
            popOnHandlerError(bool): a bool indicating if the item should be poppoed if `handler` returns as `Error` object

        Returns:
            `Ok` object with a KDict containing processedCount,PoppedCount,failedCount,failedLogs if all goes well, `Error` object otherwise
        '''

        index = 0

        results = KDict({
            'processedCount': 0,
            'PoppedCount': 0,
            'failedCount': 0,
            'failedLogs': [],
        })

        while index < len(self):
            if not (resp := self.process(index, handler, popOnHandlerSuccess=popOnHandlerSuccess, popOnHandlerError=popOnHandlerError)):
                results.processedCount += 1
                results.failedCount += 1
                index += 1
                results.failedLogs.append(KDict({
                    'item': self.peek(index).data,
                    'error': resp.log
                }))
                continue

            results.processedCount += 1

            popped = resp.data.popped
            if popped:
                results.PoppedCount += 1
            else:
                index += 1

        return Ok(results)