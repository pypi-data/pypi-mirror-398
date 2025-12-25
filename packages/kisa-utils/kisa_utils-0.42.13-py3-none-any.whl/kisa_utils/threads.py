'''
this module manages the creation and executaion of threads, be it;
    - individual threads
    - group threads
    - routine threads

@author bukman, <glayn2bukman@gmail.com>, (256)701-173-049
'''
from concurrent import futures
import time
import datetime
import threading
import inspect
import traceback
from . import codes
from .response import Response, Ok, Error
from typing import Callable

__mainThread = threading.main_thread()

__DATA = {
    'routineLoops': {},
}

__executor = None

class __Executor(futures.ThreadPoolExecutor):
    def __init__(self, workers:int = 512):
        futures.ThreadPoolExecutor.__init__(self, max_workers=workers)

    def run(self, function, *args, **kwargs):
        return self.submit(function, *args, **kwargs)

    def __del__(self):
        print('shutting down executor')
        self.shutdown(wait=False, cancel_futures=True)

class Group:
    def __init__(self,):
        self._functions = {}
        self._functionOrder = []

    def add(self, function:Callable, *args:tuple, **kwargs:dict) -> Response:
        '''
        add a function to the group
        Args:
            function(Callable): the function to be run
            args(tuple): arguments to be passsed to `function`
            kwargs(dict): key-word arguments to be passsed to `function`
        '''
        if not callable(function):
            return Error(f'`{function}` is not callable')

        functionName = function.__name__

        for functionId in self._functions:
            functionDetails = self._functions[functionId]
            if (functionName == functionDetails['functionName']) and functionDetails['args']==args and functionDetails['kargs']==kwargs:
                return Error(f'function `{functionName}` already registered in the group with exact `args` and `kwargs` given')

        if functionName.startswith('<'):
            return Error('lambda functions are not allowed')

        functionId = codes.new()
        while functionId in self._functions:
            functionId = codes.new()

        self._functions[functionId] = {
            'functionName': functionName,
            'function': function,
            'args': args,
            'kwargs': kwargs,
        }
        self._functionOrder.append(functionId)

        return Ok()

    def __markedFunction(self, functionId:str, function:Callable, *args:tuple, **kwargs:dict) -> dict:
        '''
        this method marks/tags functions so that we canorganize the function results in the `waitForAll` method
        '''

        result = {
            'functionId': functionId,
            'reply':None
        }

        try:
            result['reply'] = function(*args, **kwargs)
        except Exception as e:
            result['reply'] = {'status':False, 'log':f'threads.Group error: {e}'}

        return result

    def waitForAll(self) -> list:
        '''
        Returns:
            `list` of results in the order in which the functions were added to the group
        '''

        futuresList = [runOnce(
            self.__markedFunction, 
            functionId,
            self._functions[functionId]['function'],
            *self._functions[functionId]['args'],
            **self._functions[functionId]['kwargs'],
        ).data for functionId in self._functions]

        resultsDict = {}
        for future in futures.as_completed(futuresList):
            result = future.result()
            resultsDict[result['functionId']] = result['reply']

        resultsList = []
        for functionId in self._functionOrder:
            resultsList.append(resultsDict[functionId])

        return resultsList

def runOnce(function:Callable, *args:tuple, **kwargs:dict) -> Response:
    '''
    run a task in a separate thread
    Args:
        function(Callable): the function to be run
        args(tuple): arguments to be passsed to `function`
        kwargs(dict): key-word arguments to be passsed to `function`
    '''
    __initExecutor()

    if not callable(function):
        return Error(f'`{function}` is not callable')

    try:
        return Ok(__executor.run(function, *args, **kwargs).result())
    except Exception as e:
        return Error(f'failed to run task: {e}')

def __loop(function:Callable, duration:float, *args:tuple, **kwargs:dict) -> None:
    '''
    run `function` every `duration` seconds
    '''
    while 1:
        time.sleep(duration)
        try:
            function(*args, **kwargs)
        except Exception as e:
            print(f'`[run-every ERR] `{inspect.getsourcefile(function)}::{function.__name__}` failed with exception:')
            print('-----------')
            traceback.print_exc()
            print('-----------')


def runEvery(function:Callable, duration:float, *args:tuple, **kwargs:dict) -> dict[str,str|bool]:
    '''
    run a task periodically
    Args:
        function(Callable): the function to call every `duration`
        duration(float): the time(in SECONDS) after which to run `function` periodically
        args(tuple): arguments to be passsed to `function`
        kwargs(dict): key-word arguments to be passsed to `function`

    Returns:
        dict in form
        ```
        {
            'status': bool,
            'log': str,
            'directory': str
        }
        ```

    Note:
        the very first `function` call is made after `duration` and not immediately
    '''

    __initExecutor()
    
    reply = {'status':False, 'log':''}

    if not callable(function):
        reply['log'] = f'`{function}` is not callable'
        return reply

    try:
        future = __executor.run(__loop, function, duration, *args, **kwargs)
    except Exception as e:
        reply['log'] = f'failed to run task: {e}'
        return reply

    # future.result()

    reply['status'] = True
    return reply

def __loopRoutineThreads():
    currentMinuteData = {
        # this dictionary will help us not run the same function multiple times within the same minute
        # this is necessary because the main loop checks candidate-functions every second
        'minute':-1,
        'functionsAlreadyRun':{}
    }
    while __mainThread.is_alive():
        time.sleep(1)
        targetFunctionNames = tuple(__DATA['routineLoops'].keys())
        if not targetFunctionNames: continue

        currentDatetime = datetime.datetime.now(datetime.UTC) #+ datetime.timedelta(hours=+3)
        _utcMinute = currentDatetime.minute
        if _utcMinute != currentMinuteData['minute']:
            currentMinuteData['minute'] = _utcMinute
            currentMinuteData['functionsAlreadyRun'] = {}

        for functionName in targetFunctionNames:
            data = __DATA['routineLoops'][functionName]
            correctedTime = currentDatetime + datetime.timedelta(hours = data['tzHoursFromUTC'])
            currentDay,currentHour,currentMinute = correctedTime.weekday(),correctedTime.hour,correctedTime.minute

            if (currentDay not in data['weekDays']) or \
                (currentHour not in data['timesOfDay']) or \
                currentMinute not in data['timesOfDay'][currentHour] or\
                (functionName in currentMinuteData['functionsAlreadyRun']) \
            :
                continue

            try:
                future = __executor.run(data['function'],*data['args'], **data['kwargs'])         
                # future.result()
                currentMinuteData['functionsAlreadyRun'][functionName] = None
            except Exception as e:
                print(f'[routine-loop ERR]: {e}')
                pass

def runAt(function:Callable, timesOfDay:list[tuple[int,int]], weekDays:list[int], *args:tuple, tzHoursFromUTC:float = +3.00, **kwargs:dict) -> Response:
    '''
    run `function` rountinely at particular times of the day
    Args:
        function(Callable): function to call rountinely
        timesOfDay(list[tuple[int,int]]): a `list` of `tuples` each in format `(hour:int, minute:int)`
        weekDays(list[int]): a list of `ints` each ranging `0-6, inclusive` indicating a day of the week where `0=sunday` and `6=saturday`
        tzHoursFromUTC(float): hours to add/subtract from UTC. this allows for `timesOfDay` to be seen in a particular timezone. 
                                    the default value is `+3.00` ie `EAT` so times in `timesOfDay` are in EAT
        args(tuple): arguments to be passsed to `function`
        kwargs(dict): key-word arguments to be passsed to `function`
    
    '''

    __initExecutor()
    
    if not callable(function):
        return Error(f'`{function}` is not callable')

    if (function.__name__ in __DATA['routineLoops']) and __DATA['routineLoops'][function.__name__]['args']==args and __DATA['routineLoops'][function.__name__]['kargs']==kwargs:
        return Error(f'function `{function.__name__}` already registered with `runAt`')

    if function.__name__.startswith('<'):
        return Error('lambda functions are not allowed')

    if not (isinstance(weekDays, list) and all([isinstance(_,int) and 0<=_<=6 for _ in (weekDays or ['x'])])):
        return Error(f'invalid `weekDays` given')

    if not(isinstance(timesOfDay, list) and all(
        [isinstance(hr_min,tuple) and 2==len(hr_min) for hr_min in (timesOfDay or ['x'])]
    )):
        return Error(f'invalid `timesOfDay` given')

    for index, (hour, minute) in enumerate(timesOfDay):
        if not(isinstance(hour,int) and 0<=hour<=23 and isinstance(minute,int) and 0<=minute<=59):
            return Error(f'timesOfDay[{index}]: invalid time given `{(hour,minute)}`')

    weekDays.sort()
    timesOfDay.sort(key = lambda t: t[0])

    hourMinutes = {}
    for hour,minute in timesOfDay:
        if hour not in hourMinutes:
            hourMinutes[hour] = []
        
        hourMinutes[hour].append(minute)

    __DATA['routineLoops'][function.__name__] = {
        'function': function,
        'timesOfDay':hourMinutes,
        'weekDays': weekDays,
        'args': args,
        'kwargs': kwargs,
        'tzHoursFromUTC': tzHoursFromUTC,
    }

    return Ok()

def __initExecutor():
    global __executor

    if __executor: return

    __executor = __Executor()
    future = __executor.run(__loopRoutineThreads)
    # future.result()

# futures.as_completed([__executor.run(__loopRoutineThreads)])

if __name__=='__main__':
    '''
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for url in wiki_page_urls:
            futures.append(executor.submit(get_wiki_page_existence, wiki_page_url=url))
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    print("Threaded time:", time.time() - threaded_start)
    '''

    # def f(key=7):
    #     print(f'key={key}::am done!')
    
    # print(runEvery(f,1))
    # print(runOnce(f, key=14))
    # # futures.as_completed(__executor.run(f))

    # print('this is some dope shit')

    # print(runAt(lambda:2, [(2,45),(1,30),], [0,5,3]))

    # def routine(showTime:bool = False):
    #     print('calling routine...')
    #     if showTime:
    #         print('routine thread::',time.asctime())
    #     else:
    #         print('routine thread:: not showing time')

    # now = datetime.datetime.utcnow() + datetime.timedelta(hours=+3)
    # hour,minute = now.hour,now.minute
    # print(runAt(routine, [(hour,minute), (hour,minute+1 % 60)], [6], showTime=True))

    # while 1: pass

    # -------------------
    # def greet():
    #     print('hey niggas...')
    
    # print(runOnce(greet))
    # # print(runAt(greet,[(17,35)],[6]))

    # import random
    # number = random.randint(1,10)
    # while 1:
    #     guess = int(input('guess my number: '))
    #     if guess < number: print('too low!')
    #     elif guess > number: print('too high!')
    #     else:
    #         print('you guessed it!')
    #         break
    
    # -------------------

    # group test 1 (CPU)
    def addNumbers(a,b): return a+b

    group = Group()
    for i in range(5):
        j = 1
        print(i,j)
        group.add(addNumbers,i,j)
    
    results = group.waitForAll()
    print(results)

    # group test 2 (I/O)
    import requests
    wiki_page_url = "https://en.wikipedia.org/wiki/{number}"
    def get_wiki_page_existence(wiki_page_url, timeout=10):
        response = requests.get(url=wiki_page_url, timeout=timeout)

        page_status = "unknown"
        if response.status_code == 200:
            page_status = "exists"
        elif response.status_code == 404:
            page_status = "does not exist"

        return wiki_page_url + " - " + page_status

    t0 = time.time()
    print('\nchecking wiki pages one at a go...')
    for i in range(10):
        print(get_wiki_page_existence(wiki_page_url.format(number=i)))
    print('time taken:',time.time()-t0)

    t0 = time.time()
    print('\nchecking wiki pages using a group of threads...')
    group = Group()
    for i in range(10):
        group.add(get_wiki_page_existence,wiki_page_url.format(number=i))
    print(group.waitForAll())
    print('time taken:',time.time()-t0)
