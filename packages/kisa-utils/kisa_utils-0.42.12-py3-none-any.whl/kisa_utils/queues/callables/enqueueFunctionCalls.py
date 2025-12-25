'''
utilities to queue function calls. 

This is helpful when there are functions we need to be run in sequence even when 
the callers are from different threads eg in a web server.

An example is if we want to process one payment at a go regardless of how many 
concurrent threads try to do so at once

usage: decorate your functiona/callable with the `queueCalls` decorator
'''
# python3.6 variant
from threading import Thread, Lock
from multiprocessing import Process, Lock as ProcessLock, Queue as ProcessQueue, Manager
from functools import wraps
from queue import Queue
from typing import Callable, Union
import sys, os, time

from kisa_utils.response import Response, Ok, Error
from kisa_utils.codes import new as newCode
from kisa_utils import storage; jdecode = storage.decodeJSON

__MAIN_LOCK = Lock()
__WORKER_LOCKS_AND_QUEUES = {}

__MAIN_PROCESS_LOCK = ProcessLock()
__WORKER_PROCESSES_LOCKS_AND_QUEUES = {}
__PROCESSES_FUNCTION_REGISTRY = {}
__PROCESS_OUTFILE_DIRECTORY = '/tmp/enqueue/out'
if not os.path.isdir(__PROCESS_OUTFILE_DIRECTORY) and os.system(f'mkdir -p "{__PROCESS_OUTFILE_DIRECTORY}"'):
    sys.exit(f'[enqueue]init-error: failed to create outfile-directory `{__PROCESS_OUTFILE_DIRECTORY}`')


def __createWorker(group:str) -> Response:
    '''
    create group worker thread
    '''
    lock:Lock = __WORKER_LOCKS_AND_QUEUES[group]['lock']
    queue:Queue = __WORKER_LOCKS_AND_QUEUES[group]['queue']
    resultsDict:dict = __WORKER_LOCKS_AND_QUEUES[group]['resultsDict']

    def worker():
        while 1:
            # wait until tasks are available...
            taskId, func, args, kwargs = queue.get()

            try:
                resp = func(*args, **kwargs)
                if not isinstance(resp, Response):
                    resp = Error(f'{func.__name__} returned {type(resp)} instead of {Response}')
            except Exception as e:
                resp = Error(f'{func.__name__}: {e}')
            
            with lock:
                resultsDict[taskId] = resp

    thrd = Thread(target=worker, daemon=True)
    thrd.start()

    return Ok()

def __createProcessWorker(group:str) -> Response:
    '''
    create group worker process
    '''
# def __createProcessWorker(group:str, resultsDict) -> Response:
    lock = __WORKER_PROCESSES_LOCKS_AND_QUEUES[group]['lock']
    queue:ProcessQueue = __WORKER_PROCESSES_LOCKS_AND_QUEUES[group]['queue']

    def worker():
        print(group, __PROCESSES_FUNCTION_REGISTRY)
        while 1:
            # wait until tasks are available...
            taskId, funcId, args, kwargs = queue.get()
            func = __PROCESSES_FUNCTION_REGISTRY[funcId]
            
            try:
                resp = func(*args, **kwargs)
                if not isinstance(resp, Response):
                    resp = Error(f'{func.__name__} returned {type(resp)} instead of {Response}')
            except Exception as e:
                resp = Error(f'{func.__name__}: {e}')
            
            with open(f'{__PROCESS_OUTFILE_DIRECTORY}/{taskId}.out', 'w') as fout:
                fout.write(resp.asJSON)
                fout.flush()

    proc = Process(target=worker)
    proc.daemon = True
    proc.start()

    return Ok()

def __queueCallsDecorator(func: Callable, group: str) -> Callable:
    """ Actual decorator logic. """
    if func.__annotations__.get('return') != Response:
        sys.exit(f'{func.__name__} must have {Response} as its return type hint')

    if group not in __WORKER_LOCKS_AND_QUEUES:
        with __MAIN_LOCK:
            __WORKER_LOCKS_AND_QUEUES[group] = {
                'lock': Lock(),
                'queue': Queue(),
                'resultsDict': {},
            }

            resp = __createWorker(group)
            if not resp:
                sys.exit(resp.log)

    lock = __WORKER_LOCKS_AND_QUEUES[group]['lock']
    queue = __WORKER_LOCKS_AND_QUEUES[group]['queue']
    resultsDict = __WORKER_LOCKS_AND_QUEUES[group]['resultsDict']

    @wraps(func)
    def decorated(*args, **kwargs) -> Response:
        taskId = newCode()
        queue.put((taskId, func, args, kwargs))

        while taskId not in resultsDict:
            pass

        resp = resultsDict[taskId]

        with lock:
            del resultsDict[taskId]

        return resp

    return decorated

def __queueProcessCallsDecorator(func: Callable, group: str) -> Callable:
    """ Actual decorator logic. """
    if func.__annotations__.get('return') != Response:
        sys.exit(f'{func.__name__} must have {Response} as its return type hint')

    __funcId = newCode()
    print(f'<{__funcId}, {group}, {func}>')

    __PROCESSES_FUNCTION_REGISTRY[__funcId] = func

    if group not in __WORKER_PROCESSES_LOCKS_AND_QUEUES:
        with __MAIN_PROCESS_LOCK:
            __WORKER_PROCESSES_LOCKS_AND_QUEUES[group] = {
                'lock': ProcessLock(),
                'queue': ProcessQueue(),
            }

            # resp = __createProcessWorker(group, __WORKER_PROCESSES_LOCKS_AND_QUEUES[group]['resultsDict'])
            resp = __createProcessWorker(group)
            if not resp:
                sys.exit(resp.log)

    queue = __WORKER_PROCESSES_LOCKS_AND_QUEUES[group]['queue']

    @wraps(func)
    def decorated(*args, **kwargs) -> Response:
        taskId = newCode()
        queue.put((taskId, __funcId, args, kwargs))

        while not os.path.isfile(f'{__PROCESS_OUTFILE_DIRECTORY}/{taskId}.out'):
            pass

        time.sleep(0.01) # for some reason we sometimes detect a file has been created but before data is actually written to it
        with open(f'{__PROCESS_OUTFILE_DIRECTORY}/{taskId}.out', 'r') as fin:
            resp = jdecode(fin.read())
            resp = Ok(resp['data']) if resp['status'] else Error(resp['log'])

        os.system(f'rm "{__PROCESS_OUTFILE_DIRECTORY}/{taskId}.out"')

        # print('RR:',resp)

        return resp

    return decorated

def queueCallsInThreads(func: Callable = None, *, group: str|None = None) -> Callable:
    '''
    Decorator to queue function calls as a group using threads as task managers.
    Can be used with or without parentheses.

    Args:
        func(Callable): decorated function
        group(str|None): the group to attach the threads in
    
    Examples:
        ```
        @queueCallsInThreads # decorator not called with parentheses
        def myFunc(): ...

        # or

        @queueCallsInThreads() # decorator called with empty parentheses, same as first one
        def myFunc(): ...

        # or

        @queueCallsInThreads(group="my_group") # decorator called with parentheses, specify ONLY the `group` 
        def myFunc(): ...
        ```
    '''
    # If the decorator is used without parentheses, the function is passed as the first argument
    if func:
        if callable(func):
            return __queueCallsDecorator(func, newCode())  # Assign default group if no group is provided
        else:
            sys.exit(f'`queueCalls` must be run in one of the following flavours; `@queueCalls`, `@queueCallsInThreads()`,`@queueCallsInThreads(group=STRING)`')

    if isinstance(group, str):
        group = group.strip()
        if not group:
            sys.exit('empty group given. use `None` if you don’t want to specify the group')
    elif group is not None:
        sys.exit('unexpected type for `group`. Expected `str | None`')

    # If used with parentheses, return the actual decorator
    def wrapper(f: Callable):
        return __queueCallsDecorator(f, group if group else newCode())

    return wrapper

def queueCallsInProcesses(func: Callable = None, *, group: Union[str, None] = None) -> Callable:
    '''
    Decorator to queue function calls as a group using threads as task managers.
    Can be used with or without parentheses.

        Args:
        func(Callable): decorated function
        group(str|None): the group to attach the processes in

    Examples:
        ```
        @queueCalls # decorator not called with parentheses
        def myFunc(): ...

        # or

        @queueCallsInThreads() # decorator called with empty parentheses, same as first one
        def myFunc(): ...

        # or

        @queueCallsInThreads(group="my_group") # decorator called with parentheses, specify ONLY the `group` 
        def myFunc(): ...
        ```
    '''

    if group:
        print(f'queueCallsInProcesses: custom groups not yet supported! `{group}` will be ignored')
        group = newCode()

    # If the decorator is used without parentheses, the function is passed as the first argument
    if func:
        if callable(func):
            return __queueProcessCallsDecorator(func, newCode())  # Assign default group if no group is provided
        else:
            sys.exit(f'`queueCalls` must be run in one of the following flavours; `@queueCalls`, `@queueCallsInThreads()`,`@queueCallsInThreads(group=STRING)`')

    if isinstance(group, str):
        group = group.strip()
        if not group:
            sys.exit('empty group given. use `None` if you don’t want to specify the group')
    elif group is not None:
        sys.exit('unexpected type for `group`. Expected `str | None`')

    # If used with parentheses, return the actual decorator
    def wrapper(f: Callable):
        return __queueProcessCallsDecorator(f, group if group else newCode())

    return wrapper


if __name__=='__main__':
    import random, time

    def __callback(funcId:str, id:int, waitingTime:float) -> Response:
        time.sleep(waitingTime)
        print(f'func:{funcId}, thrd-id:{id}, sleep-delay:{waitingTime}')
        return Ok(id)

    @queueCallsInThreads(group='x')
    def f1(thrdId:int, waitingTime:float)->Response:
        __callback('F1', thrdId, waitingTime)

    @queueCallsInThreads
    def f2(thrdId:int, waitingTime:float)->Response:
        __callback('F2', thrdId, waitingTime)

    @queueCallsInThreads(group='x')
    def f3(thrdId:int, waitingTime:float)->Response:
        __callback('F3', thrdId, waitingTime)

    @queueCallsInThreads(group='x')
    def f4(thrdId:int, waitingTime:float)->Response:
        __callback('F4', thrdId, waitingTime)

    def f5(thrdId:int, waitingTime:float)->Response:
        __callback('F5', thrdId, waitingTime)

    def f6(thrdId:int, waitingTime:float)->Response:
        __callback('F6', thrdId, waitingTime)

    print('----QUEUED:UNGROUPED (F1 and F2 are both run in parallel but for each, the calls are in FIFO order)----')
    thrds = []
    for i in range(5):
        thrd = Thread(target = f1, args=(i, random.random()), daemon=True)
        thrd.start()
        thrds.append(thrd)
    for i in range(5):
        thrd = Thread(target = f2, args=(i, random.random()), daemon=True)
        thrd.start()
        thrds.append(thrd)
    
    [thrd.join() for thrd in thrds]

    print('\n----QUEUED:GROUPED (all function calls are in FIFO and in addition all F3 calls are handled before F4 calls begin)----')
    thrds = []
    for i in range(5):
        thrd = Thread(target = f3, args=(i, random.random()), daemon=True)
        thrd.start()
        thrds.append(thrd)
    for i in range(5):
        thrd = Thread(target = f4, args=(i, random.random()), daemon=True)
        thrd.start()
        thrds.append(thrd)
    
    [thrd.join() for thrd in thrds]

    print('\n----UNQUEUED (calls will be in least-delay-first order are no queueing is done at all)----')
    thrds = []
    for i in range(5):
        thrd = Thread(target = f5, args=(i, random.random()), daemon=True)
        thrd.start()
        thrds.append(thrd)
    for i in range(5):
        thrd = Thread(target = f6, args=(i, random.random()), daemon=True)
        thrd.start()
        thrds.append(thrd)
    
    [thrd.join() for thrd in thrds]

    # print(myFunc('John Doe',10))
