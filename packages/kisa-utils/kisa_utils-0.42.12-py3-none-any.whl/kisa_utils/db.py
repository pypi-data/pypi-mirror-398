import os, sys
import sqlite3
from types import SimpleNamespace
import string
from typing import Generator, Any, Callable
import inspect
import traceback
import re
from threading import get_native_id as getCurrentThreadId, Lock
import random, time

from . import storage
from . import codes
from .response import Error, Ok, Response
from .functionUtils import enforceRequirements, Definition
from .structures.utils import Value
from . import structures
from .dataStructures import KDict

if sqlite3.sqlite_version_info[1]<38:
    sys.exit(f'we need sqlite3 v3.38.0+ to run this program. current version::{sqlite3.sqlite_version}')

MAX_FETCH_ITEMS = 16*1024
RETURN_KISA_RESPONSES:bool = False # ensure all Handles return KISA-Responses globally
PARSE_DICTS_TO_KDICTS:bool = True # ensure all dicts parsed on return data are KDicts

__EXT__ = 'sqlite3'

PY_NEGATIVE_ONE_ARRAY_INDEX_REGEX = re.compile(r'\[(\s)*-(\s)*1(\s)*\]')

# you want this to throw erros in user-defined functions
try:
    sqlite3.enable_callback_tracebacks(True)

except:
    # in PyPy implementation most likely
    pass

TRIGGERS:dict = {
    # eg
    # 'userActiveStateChange':{
    #     'table': 'users',
    #     'when': 'after', # before | after | instead of
    #     'action': 'update', # insert | update | delete
    #     'condition':'''
    #         old.active != new.active
    #     ''',
    #     'code':'''
    #         insert into logs values(
    #             datetime('now', '+03:00'), 
    #             new.addedBy, 
    #             "users.active: change "||old.active||"->"||new.active,
    #             "{}"
    #         )
    #     '''
    # },

}

JSON_SEPARATOR = '::'
JSON_ARRAY_APPEND_SYMBOL = '+' # arr[+]=N => arr.append(N)

RAM_DB_PATHS:list[str] = [':memory:', ':ram:',':RAM:']

# *********************************************************************
def _getNumberOfArgsAndKwargs(function:Callable) -> tuple[int]:
    '''
    utility function to get the number of args and kwargs that a function takes
    '''
    signature = inspect.signature(function)

    nArgs = sum(
        p.default == inspect.Parameter.empty and p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        for p in signature.parameters.values()
    )

    nKwargs = len(signature.parameters) - nArgs

    return nArgs, nKwargs

class Api:
    __lock = Lock()
    __openDatabases:dict = {
        # path:str -> {
        #     threadId:int -> instance:Api,
        #     ...
        # }
    }

    # make this class a singleton
    def __new__(cls, *args, **kwargs) -> 'Api':
        path = ''
        if args: path=args[0]
        else: path = kwargs.get(path, RAM_DB_PATHS[0])

        if path not in RAM_DB_PATHS:
            threadId = getCurrentThreadId()
            with Api.__lock:
                if path not in Api.__openDatabases:
                    Api.__openDatabases[path] = {}

                if threadId in Api.__openDatabases[path]:
                    instance = Api.__openDatabases[path][threadId]
                    # print(f'using existing db handle: {threadId} {path}')
                else:
                    instance = super().__new__(cls)
                    # print(f'new db handle: {threadId} {path}')
                    Api.__openDatabases[path][threadId] = instance
        else:
            instance = super().__new__(cls)

        return instance


    def __checkContext(method):
        '''
        this decorator will be used to enforce the calling of Api class instances
        from `with` contexts. this will ensure resources are always released as they
        should
        '''
        def _(self, *args, **kwargs):
            if (not self._in_with_statement) and (not self._txnDecorated):
                raise Exception(f'method `db.Api.{method.__name__}` called from outside `with` statement/context')
            if method.__name__ in ['insert','update','delete'] and self._readonly:
                errMsg = f'calling a write method (`db.Api.{method.__name__}`) on a read-only database'
                return {
                    'status':False,
                    'log': errMsg,
                } if not self.__returnKISAResponse else Error(errMsg)
                # raise Exception(f'calling a write method (`db.Api.{method.__name__}`) on a read-only database')
            return method(self,*args, **kwargs)
        return _

    def __init__(
        self,
        path:str=':memory:', 
        tables:dict[str, str] = {}, 
        readonly:bool=True, 
        bindingFunctions:list[tuple[str,int,Callable]]=[],
        transactionMode:bool = False,
        indices:dict = {},
        *,
        accessFromMultipleThreads:bool = False,
        useWALMode:bool = True,
        returnKISAResponse:bool|None = None,
        connectionTimeout:float = 30.0
    ):
        '''
        attempt to open an sqlite3 database connection object/instance

        Args:
            path(str): path to the database file. if;
                + `path` does not exist and it does not end with the `.sqlite3` extension, it will be added`
                
                + `path` is set to `':memory:'`, an in-memory db will be opened and `readonly` will automatically be set to False
            
            tables(dict[str, str]):
                    eg
                    ```
                    {
                        'credentials':"""
                            key             varchar(256) not null,
                            value           varchar(256) not null
                        """,
                        'users':"""
                            firstName       varchar(256) not null,
                            lastName        varchar(256) not null,
                            username        varchar(256) not null
                        """,
                    }
                    ```

            readonly(bool): flag indicating if the database should be opened in read-only mode.
                + if `path` is set to `':memory:'`, `readonly` will automatically be reset to False

            bindingFunctions(list[tuple[str,int,Callable]]):  Custom functions defined in python to be used by sqlite3. 
                + Each entry is in form 
                ```
                (name:str, nargs:int, func:Callable)
                ```
                eg
                ```
                [
                    ("tripple", 1, lambda x: 3*x), # (funNameToBeUsed, argsCount, function)
                    ...
                ]
                ```

            transactionMode(bool): open db in transactiom mode

            indices(dict): dict representing the indices to be made. format is
                ```
                {
                    `tableName`: [`singleCol`, (`multiCol1`,`multiCol2`,...),...]
                }
                ```
                eg
                ```
                {
                    'users': ['userId', ('firstName','lastName')]
                }
                ```
                i.e for single column-indices, a string is provided in the list. for composite/multi-col indices, a tuple is provided

            accessFromMultipleThreads(bool): if set to `True`, access to the handle from difference threads will be permitted
            useWALMode(bool): if set to `True`, WAL mode will be used for the underlying sqlite3 database
            returnKISAResponse(bool|None): if not set, `kisa_utils.db.RETURN_KISA_RESPONSES` will be used. if set to `True`, all public methods that dont return `None` will return KISA Response objects
        '''
        if getattr(self, "_dbInitializedInThread", False):
            return
        self._dbInitializedInThread = True

        self._in_with_statement = False
        self.isOpen = False
        self.functions:dict = {}
        self._txnDecorated = False
        
        self.__transactionMode = True if transactionMode else False
        self.__withContextCount = 0
        self.__returnKISAResponse = RETURN_KISA_RESPONSES if None==returnKISAResponse else returnKISAResponse

        self._path = path

        if  path not in RAM_DB_PATHS:
            path = storage.Path.getAbsolutePath(path)

            while path.endswith('/'): path = path[:-1]
            if not path.endswith(f'.{__EXT__}') and not os.path.isfile(path):
                path += f'.{__EXT__}'

            path_root = os.path.split(path)[0]
            
            if (not os.path.isdir(path_root)) and os.system(f'mkdir -p "{path_root}"'):
                return

            if not os.path.isfile(path):
                initTables = True
        else:
            path = ':memory:'

        readonly = False if (':memory:' == path or self.__transactionMode) else readonly

        self._readonly = True if readonly else False 

        self.db:sqlite3.Connection

        max_retries = 4
        for attempt in range(max_retries):
            try:
                self.db = sqlite3.connect(path, check_same_thread = not accessFromMultipleThreads, timeout=connectionTimeout)
                break
            except sqlite3.OperationalError as e:
                if attempt == max_retries - 1:
                    raise  # Re-raise on final attempt
                
                wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                print(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)

        if useWALMode:
            self.db.executescript(f'''
                /* set journal mode to WAL and `synchronous` to best value, which works best for WAL mode*/
                pragma journal_mode=WAL; -- WAL || TRUNCATE
                PRAGMA synchronous=FULL; -- FULL || NORMAL
            ''')


        if self.__transactionMode:
            self.db.isolation_level = None
        self.cursor:sqlite3.Cursor = self.db.cursor();

        initTables = True if tables else False
        if initTables:
            self.__startTransaction()
            for table in tables:
                self.cursor.execute(f'create table if not exists {table} ({tables[table]})')
            if self.__transactionMode:
                self.db.commit()
            else:
                self.__commit()
        
        if bindingFunctions:
            functionBindReply = self.bindFunctions(bindingFunctions)
            if not functionBindReply['status']:
                raise Exception(f'binding error:: {functionBindReply["log"]}')                

        self.isOpen = True

        if indices:
            currentindices = self.__getIndicesDict()
            tablesList = self.__getTablesList()
            for table in indices:
                cols = indices[table]

                for col in cols:
                    if (table in currentindices) and (col in currentindices[table]):
                        # columns already indexed
                        continue

                    if table not in tablesList:
                        raise ValueError(f'[DB-index Error] unknown table `{table}`')
                    
                    col = col if isinstance(col,str) else ','.join(col)
                    indexName = codes.new()
                    self.cursor.execute(f'create index if not exists i{indexName} on {table}({col})')

        self.__startTransaction()

        if readonly:
            self.cursor.execute(f'''
            pragma query_only = ON;   -- disable changes
            ''')

    def __bind_functions(self, functions) -> None:
        for entry in functions:
            if entry[0] in self.functions: continue
            self.db.create_function(*entry)
            self.functions[entry[0]] = entry[-1]

    def __startTransaction(self) -> None:
        if self.__transactionMode:
            self.cursor.execute('begin')
            self.__transactionData = {
                op:{'passed':0, 'failed':0}
                for op in ['insert','delete','update','createTable','execute',]
            }

    def __commit(self) -> None:
        '''
        attempt to commit to the database IF its not open in `transactionMode=True`
        '''
        if not self.__transactionMode:
            self.db.commit()

    def __formatDBJson(self, jsonPath:str, separator:str=JSON_SEPARATOR) -> str:
        '''
        attempt to format JSON from the KISA-way to the sqlite3 way
        Args:
            jsonPath(str): the path to the json object
            separator(str): the json-separator to expect/use

        Returns:
            formatted string
        Note:
            array indices may be -1 indicating `end of array` for some operation such as updates
        '''

        if not jsonPath: return jsonPath

        jsonPath = jsonPath.replace(' AS ',' as ').\
            replace(' As ',' as ').\
            replace(' aS ',' as ')#.strip(separator)

        if not all(jsonPath.split(separator)):
            raise ValueError('the json separator cant be next to itself')

        if jsonPath.startswith(separator) or jsonPath.endswith(separator):
            raise ValueError('json token can not start or end with the json-separator')

        jsonPath = [_.strip() for _ in jsonPath.split(' as ')]
        if 1==len(jsonPath):
            jsonPath, alias = jsonPath[0],None
        elif len(jsonPath)==2:
            jsonPath, alias = jsonPath
        else:
            alias = jsonPath[-1]
            jsonPath = ' as '.join(jsonPath[:-1])

        specialXter = '.' # '\x01'
        jsonPath = jsonPath.replace(separator,specialXter).strip(specialXter)

        arrayIndex = jsonPath.index('[') if '[' in jsonPath else len(jsonPath)
        keyIndex = jsonPath.index(specialXter) if specialXter in jsonPath else len(jsonPath)

        if arrayIndex<keyIndex:
            jsonPath = jsonPath[:arrayIndex]+f'->>"${jsonPath[arrayIndex:]}"'
        elif keyIndex<arrayIndex:
            jsonPath = jsonPath[:keyIndex]+f'->>"${jsonPath[keyIndex:]}"'

        if alias:
            jsonPath += f' as {alias}'
        
        jsonPath = jsonPath.replace('->>"$.[', '->>"$[').replace("].[","][")

        return jsonPath

    def __encodeIncomingData(self ,data:list, /, *, columnNames:list[str]=[], separator:str=JSON_SEPARATOR) -> list:
        '''
        attempt to jsonify data to be written to the database
        Args:
            data(list): the `1d/2d` list containing the data to jsonify where possible before writting to the database
                + 1d array = single row to write
                + 2d array = multiple rows to write
            columnNames(list[str]): the column names in the database
            separator(str): the JSON separator to use/expect
        '''
        _data = []
        if not columnNames:
            _2d = isinstance(data[0], (list,tuple))
            for entry in data:
                if _2d:
                    entry = [_ if not isinstance(_,(tuple,list,dict)) else storage.encodeJSON(_) for _ in entry]
                else:
                    entry = entry if not isinstance(entry,(tuple,list,dict)) else storage.encodeJSON(entry) 

                _data.append(entry)
        else:
            # this happens when we dont want to encode columns that are not JSON paths.
            # this is likely to be called from the `update` method
            for index, entry in enumerate(data):
                if isinstance(entry,(tuple,list,dict)) and separator not in columnNames[index]:
                    entry = storage.encodeJSON(entry)
                _data.append(entry)

        return _data

    def __decodeOutgoingData(self, data:list[tuple], dictType:dict|KDict = dict) -> list[tuple]:
        '''
        attempt to decode json objects to python list/dict where applicable. 
        Args:
            data(list[tuple]): returned by `cursor.fetch*`
        '''
        _data = []
        for entry in data:
            _entry = []
            for value in entry:
                if value and isinstance(value,str) and (value[0] in '[{'):
                    try:
                        value = storage.decodeJSON(value)
                        if dictType==KDict:
                            value = KDict._wrap(value)
                    except:
                        pass

                _entry.append(value)
            _data.append(tuple(_entry))

        return _data

    def __formatJSONCondition(self, condition:str, separator:str=JSON_SEPARATOR) -> str:
        '''
        format JSON condition from the KISA-format to the sqlite3 format
        '''
        # print(f'>>0{condition}<<')
        _condition = ''
        while (found := PY_NEGATIVE_ONE_ARRAY_INDEX_REGEX.search(condition)):
            start, end = found.start(), found.end()
            _condition += condition[:start] + '[#-1]'
            condition = condition[end:]
        condition = _condition + condition
        # print(f'>>{condition}<<')

        if separator not in condition: return condition

        jsonXters = string.digits+string.ascii_letters+separator+'[]-_#'

        jsonIndexRanges = []
        index = 0
        conditionLength = len(condition)
        while separator in condition[index:]:
            separatorIndex = index + condition[index:].index(separator)

            # find start and end of the json-path
            leftIndex, rightIndex = separatorIndex, separatorIndex
            while leftIndex >= 0:
                if condition[leftIndex] not in jsonXters: break
                leftIndex -= 1
            leftIndex += 1 # by the time we break out, we've already found a bad xter

            while rightIndex < conditionLength:
                if condition[rightIndex] not in jsonXters: break
                rightIndex += 1
            rightIndex -= 1 # by the time we break out, we've already found a bad xter

            jsonIndexRanges.append((leftIndex,rightIndex))
            # print(f'<{condition[leftIndex:rightIndex+1]}><{__formatDBJson(condition[leftIndex:rightIndex+1])}>')

            index = rightIndex + 1

        startIndex = 0
        _condition = ''
        jsonIndexRanges.append((conditionLength, conditionLength))
        for leftIndex,rightIndex in jsonIndexRanges:
            _condition += condition[startIndex:leftIndex]
            _condition += self.__formatDBJson(condition[leftIndex:rightIndex+1])
            startIndex = rightIndex+1

        return _condition

    def __getIndicesDict(self) -> dict[str,list]:
        '''
        get indeces dict
        '''
        indices = {}

        if not self.isOpen: return indices

        self.cursor.execute('''
            SELECT name, tbl_name
            FROM sqlite_master
            WHERE type = 'index';
        ''')

        for indexName, table in self.cursor.fetchall():
            if table not in indices: indices[table] = []
            self.cursor.execute(f'pragma index_info("{indexName}")')
            cols = tuple([_[2] for _ in self.cursor.fetchall()])
            cols = cols[0] if 1==len(cols) else cols
            if cols not in indices[table]:
                indices[table].append(cols)

        return indices

    def __getTablesList(self) -> list:
        tables = []

        if not self.isOpen: return tables

        self.cursor.execute('''
            SELECT name, tbl_name
            FROM sqlite_master
            WHERE type = 'table';
        ''')

        tables = [_[0] for _ in self.cursor.fetchall()]
        
        return tables

    def __getJSONListIndices(self, jsonPathSection:str) -> Response:
        '''
        get key and indices of a json path
        Returns:
            Response.data -> 
            ```
            {
                'key': str, # if array is a key in a dict, then this is set, otherwise its an empty string
                'indices': list[int] # contains all indices
            }
            ```
        '''
        data = KDict({
            'key': '',
            'indices': [],
        })

        if '[' not in jsonPathSection:
            return Ok(data)

        if jsonPathSection.count('[') != jsonPathSection.count(']') or jsonPathSection.index('[') > jsonPathSection.index(']'):
            return Error(f'malformed array indexing found: `{jsonPathSection}`')

        targetIndex = jsonPathSection.index('[')
        data.key = jsonPathSection[:targetIndex].strip()

        section = jsonPathSection[targetIndex:]
        while '[' in section:
            if section.count('[') != section.count(']') or section.index('[') > section.index(']'):
                return Error(f'malformed array indexing found: `{jsonPathSection}`')

            startIndex, endIndex = section.index('['), section.index(']')

            try:
                index = section[startIndex+1:endIndex]
                index = int(index)
            except:
                index = index.strip()
                if index != JSON_ARRAY_APPEND_SYMBOL:
                    return Error(f'malformed array index found: `{jsonPathSection}`->`{section[startIndex+1:endIndex]}`')

                if JSON_ARRAY_APPEND_SYMBOL in data.indices:
                    return Error(f'index `{JSON_ARRAY_APPEND_SYMBOL}` should be the last index: `{jsonPathSection}`->`{section[startIndex+1:endIndex]}`')

            data.indices.append(index)

            section = section[endIndex+1:]

        return Ok(data)

    def __formRootPathFields(self, root:dict|list, keys:list, value:Any) -> Response:
        for key in keys[:-1]:
            if not (resp := self.__getJSONListIndices(key)):
                return resp

            if not resp.data.indices: # dict object
                root = root.setdefault(key, {})
            else: # list object
                if resp.data.key and isinstance(root, dict):
                    root = root.setdefault(resp.data.key, [])

                if not isinstance(root, list):
                    return Error(f'indexing non-array: `{key}`')

                while resp.data.indices:
                    _index = index = resp.data.indices.pop(0)
                    if _index == JSON_ARRAY_APPEND_SYMBOL:
                        return Error(f'append index `{_index}` should be at the end: `{key}`, index `{_index}({index})`')
                    if index < 0:
                        index = len(root) + index
                    
                    if not (0<= index < len(root)):
                        return Error(f'array-index out of bounds: `{key}`, index `{_index}({index})`')

                    root = root[index]

        key = keys[-1]

        if not (resp := self.__getJSONListIndices(key)):
            return resp

        if not resp.data.indices: # dict object
            root[key] = value
        else: # list object
            if resp.data.key and isinstance(root, dict):
                root = root.setdefault(resp.data.key, [])

            if not isinstance(root, list):
                return Error(f'indexing non-array: `{key}`')

            while len(resp.data.indices):
                _index = index = resp.data.indices.pop(0)
                if _index != JSON_ARRAY_APPEND_SYMBOL:
                    if index < 0:
                        index = len(root) + index
                
                    if not (0<= index < len(root)):
                        return Error(f'array-index out of bounds: `{key}`, index `{_index}({index})`')
                elif resp.data.indices:
                    return Error(f'append index `{_index}` should be at the end: `{key}`, index `{_index}({index})`')

                if resp.data.indices:
                    root = root[index]
                else:
                    if _index != JSON_ARRAY_APPEND_SYMBOL:
                        root[index] = value
                    else:
                        root.append(value)

        return Ok()

    def __getRootAndPath(self, string, separator:str=JSON_SEPARATOR):
        index = string.index(separator)

        return string[:index], string[index + len(separator):]

    #---------------------------------------------------------------------------
    @__checkContext
    def execute(self, cmd:str, cmdData:list=[], executingMultiple:bool=False) -> dict[str,bool|str|int|sqlite3.Cursor] | Response:
        '''
        attempt to execute arbitrary SQLite3 commands
        Args:
            cmd(str): SQLite command to run
            cmdData(list): list to hold the values for the `?` placeholders in `cmd`
            executingMultiple(bool): indicate if we're executing/inserting multiple statements/rows at ago. this allows us to use cursor.executemany instead of cursor.execute
        Returns:
            ```
            # if a dict is returned
            {
                'status': bool,
                'log': str,
                'cursor': sqlite3.Cursor, 
                'affectedRows': int
            }

            # if a response object is returned
            Ok({
                'cursor': sqlite3.Cursor, 
                'affectedRows': int
            })

            Error(log)
            ```
        '''
        reply = {'status':False, 'log':'', 'cursor':None, 'affectedRows':0}

        try:
            cmd = self.__formatJSONCondition(cmd)
        except:
            if self._transactionMode: self._transactionData['execute']['failed'] += 1
            reply['log'] = 'failed to format cmd json'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        for index,value in enumerate(cmdData):
            if not isinstance(value,(int,float,str,bytes)):
                try:
                    cmdData[index] = storage.encodeJSON(value)
                except:
                    reply['log'] = f'could not serialize cmdData[{index}] to JSON'
                    return reply if not self.__returnKISAResponse else Error(reply['log'])

        try:
            cursor = (self.cursor.execute if not executingMultiple else self.cursor.executemany)(cmd,cmdData)
            affectedRows = cursor.rowcount

            if affectedRows < 0:
                reply['cursor'] = cursor
            elif 0==affectedRows:
                if self.__transactionMode: self.__transactionData['execute']['failed'] += 1
                reply['log'] = 'the write command did not affect any rows'
                return reply if not self.__returnKISAResponse else Error(reply['log'])
            else:
                if self.__transactionMode: self.__transactionData['execute']['passed'] += 1
                reply['affectedRows'] = affectedRows
        except Exception as e:
            reply['log'] = str(e)
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok({'cursor':reply['cursor'], 'affectedRows':reply['affectedRows']})

    @__checkContext
    def executeScript(self, sql:str) -> Response:
        '''
        directly execute complex sql commands. this is useful when for you need to execute complex transactions example 
        Args:
            sql(str): the sql to execute
        '''

        try:
            self.db.executescript(sql)
        except Exception as e:
            return Error(f'{e}')
        return Ok()

    @__checkContext
    def __createFetchResultsGenerator(self, results:sqlite3.Cursor, columnTitles:list, parseJson:bool, mode:str) -> Generator[tuple|dict|SimpleNamespace,None,None]:

        for entry in results:
            if parseJson:
                entry = self.__decodeOutgoingData([entry])[0]

            yield entry if 'plain' == mode else (
                dict(zip(columnTitles,entry)) if 'dicts' == mode else(
                    SimpleNamespace(**dict(zip(columnTitles,entry))) if 'namespaces' == mode else(
                        entry
                    )
                )
            )

    @__checkContext
    def fetch(self, 
            table:str, columns:list, condition:str, conditionData:list, 
            limit:int=MAX_FETCH_ITEMS, returnDicts:bool=False, 
            returnNamespaces:bool=False, parseJson:bool=False, 
            returnGenerator:bool=False,
            useKDicts:bool|None=None,
            offset:int = 0,
        ) -> list|Response:
        '''
        attempt to fetch from the database

        Args:
            table(str): database table name
            columns(list): list of the columns to fetch. json columns are accessed using the `/` separator eg `other/bio/contacts[0]`
            condition(str): a string indicating the SQL condition for the fetch eg `userId=? and dateCreated<?`. all values a represented with the `?` placeholder
            conditionData(list): a list containing the values for each `?` placeholder in the condition
            limit(int): number indicating the maximum number of results to fetch
            returnDicts(bool): if `True`, we shall return a list of dictionaries(KDict if `useKDicts`=`True`) as opposed to a list of tuples
            returnNamespaces(bool): if `True`, we shall return a list of named-tuples as opposed to a list of tuples
                ** if both `returnDicts` and `returnNamespaces` are set, `returnDicts` is effected
            parseJson(bool):if `True`, we shall parse json objects to python lists and dictionaries where possible
            returnGenerator(bool): if True, a generator will be returned instead of the list of tuple|dict|SimpleNamespace. this is especially recommended for large data
            useKDicts(bool): if True, all dicts returned are `KDicts` ie dicts that support the dot notation, just like JS objects
            offset(int): how many rows to skip. along with `limit`, this allows pagination of results
        '''
        if not (limit>0 and limit<=MAX_FETCH_ITEMS):
            err = f'please set a limit on the returned rows. maximum should be {MAX_FETCH_ITEMS}'
            if not self.__returnKISAResponse:
                raise ValueError(err)
            return Error(err)

        if not isinstance(offset, int) or offset < 0:
            err = f'invalid offset given. expected int >= 0'
            if not self.__returnKISAResponse:
                raise ValueError(err)
            return Error(err)

        useKDicts = PARSE_DICTS_TO_KDICTS if None==useKDicts else useKDicts

        condition = condition.strip() or '1'
        if not len(condition.strip()):
            err = 'no condition provided'
            if not self.__returnKISAResponse:
                raise ValueError(err)
            return Error(err)

        try:
            condition = self.__formatJSONCondition(condition)
        except:
            pass

        if columns in [['*']]:
            self.cursor.execute(f'select * from {table} where {condition} limit {limit}',conditionData)
            columns = [description[0] for description in self.cursor.description]

        # columns = [self.__formatDBJson(_) for _ in columns]
        columns = [self.__formatJSONCondition(_) for _ in columns]

        __SQL_stmt = f"select {','.join(columns)} from {table} where {condition} limit {limit} offset {offset}"
        # print(f'<{__SQL_stmt}>')

        if not self.__returnKISAResponse:
            self.cursor.execute(__SQL_stmt,conditionData)
        else:
            try:
                self.cursor.execute(__SQL_stmt,conditionData)
            except Exception as e:
                return Error(str(e))

        dictType = KDict if useKDicts else dict

        fetchedData = self.cursor
        if parseJson and not returnGenerator:
            fetchedData = self.__decodeOutgoingData(fetchedData, dictType=dictType)

        cols = [_[0] for _ in self.cursor.description]

        if not (returnDicts or returnNamespaces):
            if fetchedData == self.cursor:
                fetchedData = [_ for _ in fetchedData]

            returnData = fetchedData if not returnGenerator else self.__createFetchResultsGenerator(fetchedData, cols, parseJson, 'plain')
            return returnData if not self.__returnKISAResponse else Ok(returnData)

        if returnDicts:
            returnData = [dictType(zip(cols,_)) for _ in fetchedData] if not returnGenerator else self.__createFetchResultsGenerator(fetchedData, cols, parseJson, 'dicts')
            return returnData if not self.__returnKISAResponse else Ok(returnData)

        # namepsaces...
        if [_ for _ in cols if (
            (' ' in _) or not (
                'a'<=_[0]<='z' or \
                'A'<=_[0]<='Z' or \
                '_'==_[0]
            )
        )]:
            err = 'one or more column names is invalid as a key for namespaces'
            if not self.__returnKISAResponse: raise TypeError(err)
            return Error(err)

        returnData =  [SimpleNamespace(**dict(zip(cols,_))) for _ in fetchedData] if not returnGenerator else self.__createFetchResultsGenerator(fetchedData, cols, parseJson, 'namespaces')
        return returnData if not self.__returnKISAResponse else Ok(returnData)

    @__checkContext
    def createTables(self, tables:dict[str,str]) -> dict|Response:
        '''
        attempt to create tables to the database
        Args:
            tables(dict[str,str]): the tables to create
                eg
                ```
                {
                    'credentials':"""
                        key             varchar(256) not null,
                        value           varchar(256) not null
                    """,
                    'users':"""
                        firstName       varchar(256) not null,
                        lastName        varchar(256) not null,
                        username        varchar(256) not null
                    """,
                }
                ```
        
        @return standard dict of {status:BOOL, log:STR}
        '''

        reply = {'status':False, 'log':''}

        for table in tables:
            try:
                self.cursor.execute(f'create table if not exists {table} ({tables[table]})')
                self.__commit()
                if self.__transactionMode: self.__transactionData['createTable']['passed'] += 1
            except Exception as e:
                if self.__transactionMode: self.__transactionData['createTable']['failed'] += 1
                reply['log'] = str(e)
                return reply if not self.__returnKISAResponse else Error(reply['log'])

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok()

    @__checkContext
    def insert(self, table:str, data:list) -> dict[str,bool|str]|Response:
        '''
        insert a new row(s) into the database
        Args:
            table(str): the table into which to insert data
            data(list): 1d/2d list of the data to insert
                + 1d = insert single row
                + 2d = insert multple row
        '''
        reply = {'status':False, 'log':'', 'affectedRows':0}

        try:
            self.cursor.execute(f'select * from {table}')
            column_value_placeholders = ['?' for description in self.cursor.description]
        except Exception as e:
            if self.__transactionMode: self.__transactionData['insert']['failed'] += 1
            reply['log'] = str(e)
            return reply if not self.__returnKISAResponse else Error(reply['log'])
        
        if not isinstance(data, (list, tuple)):
            data = [data]

        try:
            data = self.__encodeIncomingData(data)
            if isinstance(data[0],(list,tuple)):
                cursor = self.cursor.executemany(f'insert into {table} values ({",".join(column_value_placeholders)})',data)
            else:
                cursor = self.cursor.execute(f'insert into {table} values ({",".join(column_value_placeholders)})',data)
            
            reply['affectedRows'] = cursor.rowcount
            self.__commit()
            if self.__transactionMode: self.__transactionData['insert']['passed'] += 1
        except Exception as e:
            if self.__transactionMode: self.__transactionData['insert']['failed'] += 1
            reply['log'] = str(e)
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok({'affectedRows':reply['affectedRows']})

    @__checkContext
    def update(self, table:str, columns:list[str], columnData:list, condition:str, conditionData:list,/,*,jsonSeparator:str=JSON_SEPARATOR) -> dict[str,bool|str]|Response:
        '''
        update rows in the database
        Args:
            table(str): the table to update
            columns(list[str]): the list of columns to update in the table
            columnData(list): the new column values. values should match the `columns` in count
            condition(str): sqlite condition to use 
            conditionData(list): data to fill in the sqlite `?` in the `condition`
            jsonSeparator(str): the JSON separator to use
        '''
        reply = {'status':False, 'log':''}

        if columns in [['*']]:
            self.cursor.execute(f'select * from {table}')
            columns = [description[0] for description in self.cursor.description]

        if len(columns) != len(columnData):
            if self.__transactionMode: self.__transactionData['update']['failed'] += 1
            reply['log'] = '[db-update err] expected same number of items in `columns` as in `columnData`'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        try:
            columnData = self.__encodeIncomingData(columnData, columnNames=columns)
        except Exception as e:
            if self.__transactionMode: self.__transactionData['update']['failed'] += 1
            reply['log'] = f'failed to encode incoming data: {str(e)}'
            return reply if not self.__returnKISAResponse else Error(reply['log'])
        
        condition = condition.strip() or '1'

        try:
            condition = self.__formatJSONCondition(condition)
        except:
            if self.__transactionMode: self.__transactionData['update']['failed'] += 1
            reply['log'] = 'failed to format condition json'
            return reply if not self.__returnKISAResponse else Error(reply['log'])
        
        values = []
        _columns = []
        json_roots = {}
        for index,col in enumerate(columns):
            if jsonSeparator not in col:
                _columns.append(f'{col}=?')
                values.append(columnData[index])
            else:
                
                # if '[-1]' in col:
                #     if col.count('[-1]')>1:
                #     # if path.count('[#]')>1:
                #         if self.__transactionMode: self.__transactionData['update']['failed'] += 1
                #         reply['log'] = 'we dont allow more than `[-1]` or `[#]` signatures for json'
                #         return reply if not self.__returnKISAResponse else Error(reply['log'])
                #     if not col.endswith('[-1]'):
                #     # if not path[:-1].endswith('[#]'): 
                #         if self.__transactionMode: self.__transactionData['update']['failed'] += 1
                #         reply['log'] = 'json-array `[-1]` or `[#]` should be the last in the path'
                #         return reply if not self.__returnKISAResponse else Error(reply['log'])
                
                root, path = self.__getRootAndPath(col.strip())

                if root not in json_roots:
                    cursor = self.cursor.execute(f'select {root} from {table} where {condition}', conditionData)
                    rootResult = cursor.fetchone()
                    if not rootResult:
                        _columns.append(f'{root}=?')
                        values.append("{}")
                        continue

                    rootResult = rootResult[0]
                    rootResult = storage.decodeJSON(rootResult)
                    # print('>>> ',rootResult,'<<<')

                    if isinstance(rootResult, list):
                        if self.__transactionMode: self.__transactionData['update']['failed'] += 1
                        reply['log'] = 'arrays are not yet supported as the top-level JSON objects'
                        return reply if not self.__returnKISAResponse else Error(reply['log'])

                else:
                    rootResult = json_roots[root]

                json_roots[root] = rootResult

                if not (resp := self.__formRootPathFields(json_roots[root], path.split(JSON_SEPARATOR), columnData[index])):
                    reply['log'] = resp.log
                    return reply if not self.__returnKISAResponse else resp

                _columns.append(f'{root}=?')

                values.append(storage.encodeJSON(rootResult))
        columns = _columns
        values += conditionData


        if not condition:
            if self.__transactionMode: self.__transactionData['update']['failed'] += 1
            reply['log'] = 'please provide an update condition. use `1` if you want all data updated'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        try:
            cursor = self.cursor.execute(f'update {table} set {",".join(columns)} where {condition}',values)

            reply['affectedRows'] = cursor.rowcount

            if not reply['affectedRows']:
                if self.__transactionMode: self.__transactionData['update']['failed'] += 1
                reply['log'] = 'update condition does NOT affect any rows'
                return reply if not self.__returnKISAResponse else Error(reply['log'])

            self.__commit()
            if self.__transactionMode: self.__transactionData['update']['passed'] += 1
        except Exception as e:
            if self.__transactionMode: self.__transactionData['update']['failed'] += 1
            reply['log'] = str(e)
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok({'affectedRows':reply['affectedRows']})

    @__checkContext
    def delete(self, table:str, condition:str, conditionData:list) -> dict[str,bool|str]|Response:
        '''
        delete rows from a table
        Args:
            table(str): the table to modify
            condition(str): sqlite condition to use 
            conditionData(list): data to fill in the sqlite `?` in the `condition`
        '''
        reply = {'status':False, 'log':'', 'affectedRows':0}

        condition = condition.strip()
        if not condition:
            if self.__transactionMode: self.__transactionData['delete']['failed'] += 1
            reply['log'] = 'please provide a delete condition. use `1` if you want all data gone'
            return reply if not self.__returnKISAResponse else Error(reply['log'])
        try:
            condition = self.__formatJSONCondition(condition)
        except:
            if self.__transactionMode: self.__transactionData['delete']['failed'] += 1
            reply['log'] = 'failed to format condition json'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        try:
            cursor = self.cursor.execute(f'delete from {table} where {condition}',conditionData)

            reply['affectedRows'] = cursor.rowcount

            if not reply['affectedRows']:
                if self.__transactionMode: self.__transactionData['delete']['failed'] += 1
                reply['log'] = 'delete condition does NOT affect any rows'
                return reply if not self.__returnKISAResponse else Error(reply['log'])

            self.__commit()
            if self.__transactionMode: self.__transactionData['delete']['passed'] += 1
        except Exception as e:
            if self.__transactionMode: self.__transactionData['delete']['failed'] += 1
            reply['log'] = str(e)
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok({'affectedRows':reply['affectedRows']})

    @__checkContext
    def commitTransaction(self) -> dict|Response:
        '''
        attempt to commits all operations of a transaction

        Returns:
            `Response` or `dict` in form of 
            ```
            {'status':bool, 'log':str}
            ```
        '''
        reply = {'status':False, 'log':''}

        if not self.__transactionMode:
            reply['log'] = 'database not in transaction mode'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        if not self.isOpen:
            reply['log'] = 'database not open'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        if not self.inTopLevelContext:
            reply['log'] = 'can not commit transaction in non top-level context'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        for op in self.__transactionData:
            if self.__transactionData[op]['failed']:
                reply['log'] = f'{self.__transactionData[op]["failed"]} `{op}` operation(s) returned a `False` status'
                return reply if not self.__returnKISAResponse else Error(reply['log'])
        
        self.cursor.execute('commit')

        self.__startTransaction()

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok()

    def bindFunctions(self, functions:list[tuple[str,int,Callable]]) -> dict|Response:
        '''
        attempt to bind python functions to the db-handle
        Args:
            functions(list[tuple[str,int,Callable]]): a list of functions-tuples to bind
            eg
            ```
            [
                ("tripple", 1, lambda x: 3*x), # (funNameToBeUsed, argsCount, function)
                ...
            ]
            ```

        @return: standard kisa-dict of `{'status':BOOL, 'log':STR}`
        '''
        reply = {'status':False, 'log':''}

        if not isinstance(functions, list):
            reply['log'] = 'expected `functions` to be a list'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        if not functions:
            reply['log'] = 'no functions provided'
            return reply if not self.__returnKISAResponse else Error(reply['log'])
        
        signatures = []
        for index, function in enumerate(functions):
            if isinstance(function, tuple):
                if 3 != len(function):
                    reply['log'] = 'invalid tuple-style function signature given'
                    return reply if not self.__returnKISAResponse else Error(reply['log'])
                signatures.append(function)
                continue

            if not callable(function):
                reply['log'] = f'item at index {index} is not a function'
                return reply if not self.__returnKISAResponse else Error(reply['log'])

            name = function.__name__
            if name.startswith('<'):
                reply['log'] = f'function at index {index} seems to be a lambda function. these are not allowed'
                return reply if not self.__returnKISAResponse else Error(reply['log'])

            nArgs, nKwargs = _getNumberOfArgsAndKwargs(function)

            signatures.append((name,nArgs,function))

        try:
            self.__bind_functions(signatures)
        except Exception as e:
            reply['log'] = f'function binding error: {e}'
            return reply if not self.__returnKISAResponse else Error(reply['log'])

        reply['status'] = True
        return reply if not self.__returnKISAResponse else Ok()

    # @__checkContext
    def close(self) -> bool:
        '''
        close the sqlite connection
        '''
        
        if self.__withContextCount > 0:
            return False
        
        # print('>>>closed DB<<<<', self._path)
        if self.isOpen:
            # self.db.execute('pragma optimize;')
            if self.__transactionMode:
                pass # self.commitTransaction()
            else:
                self.db.commit()

            if self.__withContextCount <= 0:
                self.db.close()
                # self.db, self.cursor = None,None
                self.isOpen = False

        return True

    # @__checkContext
    def release(self) -> None:
        '''
        close the sqlite3 connection
        '''

        path = self._path

        if not self.close(): 
            return

        if path in RAM_DB_PATHS: return

        threadId = getCurrentThreadId()
        with Api.__lock:
            if (path in Api.__openDatabases) and (threadId in Api.__openDatabases[path]):
                del Api.__openDatabases[path][threadId]

    # methods to add context to the handle
    def __enter__(self) -> 'Api':
        self._in_with_statement = True
        self.__withContextCount += 1
        return self

    def __exit__(self, *args) -> bool:
        self.__withContextCount -= 1
        if self.__withContextCount > 0:
            if args[0] is None:
                return True
            else:
                return False

        # args = [exc_type, exc_value, traceback]
        self.release()

        self._in_with_statement = False

        # False=propagate exceptions, True=supress them
        # you want to propagate exceptions so that the calling code can know what went wrong
        if args[0] is None:
            return True
        else:
            return False

    # to be called when the GC deletes the instance. this is important for callers that somehow dont use a context manager and forget to call the `release` method leading to dangling resources and database locks
    def __del__(self):
        self.close()

    def __bool__(self)->bool:
        return self.isOpen

    @property
    def inTopLevelContext(self) -> bool:
        '''
        check if the opened db-handle is in the top-most `with` context. 
        If it is, then its okay to commit a transaction
        '''
        return self.__withContextCount <= 1

Handle = Api

def transaction(*dbArgs, **dbKwargs) -> dict|Response:
    '''
    attempt to decorate a function in a single transaction
    @params `dbArgs`: args to be passed to Api/Handle when creating the db-handle
    @params `dbKwargs`: keyword-args to be passed to Api when creating the db-handle

    `dbArgs` and `dbKwargs` [in their order] are; 
    + `path:str`=':memory:', 
    + `tables:[str, str]` = {}, 
    + `readonly:bool`=True, 
    + `bindingFunctions:list[tuple[str,int,Callable]]`=[],
    + `transactionMode:bool` = False

    + `indices:dict` = {False}
    + `accessFromMultipleThreads:bool` = False
    + `useWALMode:bool` = True
    + `returnKISAResponse:bool|None` = None | kisa_utils.db.RETURN_KISA_RESPONSES

    NB: the exact ordering and naming of `dbArgs` and `dbKwargs` should ALWAYS be got from Api/Handle
    
    '''

    returnKISAResponse = dbKwargs.get('returnKISAResponse',RETURN_KISA_RESPONSES)

    def handler(func) -> dict:
        def wrapper(*args, **kwargs) -> dict:
            reply = {'status':False, 'log':''}

            dbKwargs['transactionMode'] = True
            try:
                handle = Handle(*dbArgs, **dbKwargs)
            except:
                reply['log'] = '[TXN-E01] failed to open database'
                return reply if not returnKISAResponse else Error(reply['log'])

            if not handle.isOpen:
                reply['log'] = '[TXN-E02] failed to open database'
                return reply if not returnKISAResponse else Error(reply['log'])

            with handle:
                handle._txnDecorated = True
                kwargs['handle'] = handle

                try:
                    funcReply = func(*args, **kwargs)
                except Exception as e:
                    tracebackLog = traceback.format_exc()
                    reply['log'] = f'txn callback failed with exception: {tracebackLog}'
                    return reply if not returnKISAResponse else Error(reply['log'])

                if returnKISAResponse:
                    if not isinstance(funcReply, Response):
                        return Error('[TXN-E03] decorated function does not return a KISA Response object yet `returnKISAResponse` was set to True')
                elif ((not isinstance(funcReply,dict)) or ('status' not in funcReply)):
                    reply['log'] = '[TXN-E03] decorated function does not conform to the expected return structure `{"status":bool, "log":str, ...}`'
                    return reply

                if (isinstance(funcReply, Response) and not funcReply) or (not isinstance(funcReply, Response) and not funcReply['status']):
                    return funcReply

                txnCommitReply = handle.commitTransaction()
                if (isinstance(txnCommitReply, Response) and not txnCommitReply) or (not isinstance(txnCommitReply, Response) and not txnCommitReply['status']):
                    return txnCommitReply

                return funcReply

        return wrapper
    return handler

class Column:
    @enforceRequirements
    def __init__(
        self, 
        name: Value(str, lambda n: Ok() if n and ' ' not in n and not n[0].isdigit() else Error('invalid column name given')),
        dataType: type, # int|float|bytes|list|dict|tuple, 
                        # bytes=blob, list|dict|tuple=JSON
        /,
        *,
        validator: Value|None = None, # must take 1 argument and return a 
                                      # kisa_utils.response.Response object
        required:bool = False,
        maxSize:int = -1, # -1=unlimited. for ;
                          #     strings,JSON:list|tuple|dict,bytes: maxSize=`len`
                          #     int,float: maxSize=maxValue
        unique:bool = False,
        isPrimaryKey:bool = False,
        trackChanges: bool = False, # if set to True, all changes/updates 
                                    # along with their timestamps will be logged
                                    # all changes will be stored in a special 
                                    # table in the database. the very first insert
                                    # will trigger a log as well if trackChanges is
                                    # set to `True`
        # z:Callable|None = None
    ) -> None:
        '''
        create a column definition/instance
        '''
        ...

class Table:
    @enforceRequirements
    def __init__(
        self,
        name: Value(str, lambda n: Ok() if (n and ' ' not in n and not n[0].isdigit()) else Error('invalid column name given')),
        /,
        *,
        trackChanges: bool = False, # if set to True, all changes/updates 
                                    # along with their timestamps will be logged
                                    # all changes will be stored in a special 
                                    # table in the database. the very first insert
                                    # will trigger a log as well if trackChanges is
                                    # set to `True`

        # onInsert:Callable|None=None,
        # onDelete:Callable|None=None,
        # onUpdate:Callable|None=None,
    ) -> None:
        '''
        create a table definition
        '''
        pass

# ------------------------------------------------------------------------------
if __name__=='__main__':
    # Column('ab', int)

    with Api('/tmp/bukman/database.db2') as handle:
        print(handle.fetch('keys',['*'],'',[]))
    # Column('ab', int)

    with Api('/tmp/bukman/database.db2') as handle:
        print(handle.fetch('keys',['*'],'',[]))