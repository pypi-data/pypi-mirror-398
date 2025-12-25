'''
this module is reponsible to creating and managing named caches for KISA

@author bukman, <glayn2bukman@gmail.com>, (256)701-173-049
'''

import time
from . import threads
from .queues.callables import executorQueues
from . import db
from typing import Callable

class CacheException(Exception):
    pass

class _EmptyCacheValue:
    def __init__(self): pass

class Cache:
    __ACTIVE_CACHES = {}
    def __init__(self, name:str) -> None:
        '''
        create a cache instance
        Args:
            name(str): the cache name
        '''
        self.__cache = {
            # key: {
            #     'lastUpdated': int, 
            #     'updator': callable, 
            #     'value': any,
            #     'autoUpdateAfter': int, 
            #     'duplicateUpdateThreshold': float
            # }
        }

        if name in self.__ACTIVE_CACHES:
            raise CacheException('a cache with the given name already exists')

        self.__ACTIVE_CACHES[name] = self

        loopThreadReply = threads.runEvery(self.__monitorLoop, 0.1)
        if not loopThreadReply['status']:
            raise CacheException(f'cache main thread: {loopThreadReply["log"]}')

        queueReply = executorQueues.create(f'_cache:{name}', self.__readQueue)
        if not queueReply['status']:
            raise CacheException(f'cache queue thread: {queueReply["log"]}')

        self.__queue = queueReply['queue']

    def __monitorLoop(self) -> None:
        now = time.time()

        keys = self.__cache.keys()
        for key in keys:
            if now - self.__cache[key]['lastUpdated'] >  self.__cache[key]['autoUpdateAfter']:
                self.__queue.push(key)

    def __readQueue(self, key:str) ->  None:
        if key not in self.__cache: return

        now = time.time()

        if now - self.__cache[key]['lastUpdated'] >  self.__cache[key]['duplicateUpdateThreshold']:
            self.__updateValue(key)

    def __updateValue(self, key:str) -> None:
        if key not in self.__cache: return

        try:
            value = self.__cache[key]['updator']()
        except:
            return   

        if (None==value) or (isinstance(value,dict) and not value.get('status',True)):
            return

        now = time.time()
        # print(now, value)
        self.__cache[key]['value'] = value
        self.__cache[key]['lastUpdated'] = now

    def addKey(self, name:str, updator:Callable, autoUpdateAfter:int=3600, duplicateUpdateThreshold:float=30) -> dict:
        '''
        create a new cache key

        Args:
            name(str): the name of the key
            updator(Callable): the function to call everytime we need to update the key. 
                            The value of the key is whatever the function returns.
                            Also, the `updator` should not take any arguments or keywords
            autoUpdateAfter(int): how many SECONDS to wait before we automatically call the `updator` function
            duplicateUpdateThreshold(float): SECONDS within which if multiple requests to update the key will be ignored as long as one is already activated.
                say we have 20 calls to update a key in 1 minute, only 1 request will be obeyed to avoid strange deadlocks and database contension-resources
        
        Returns:
            ```
            {
                'status':bool,
                'log':str
            }
            ```
            
        NB: the result of the `updator` will be ignored if;
            - its `None`
            - its a `dict` with `status` set to `False`
            - the `updator` raised an exception
        '''
        reply = {'status':False, 'log':''}

        if name in self.__cache:
            reply['log'] = 'key name already exists in the cache'
            return reply

        if not callable(updator):
            reply['log'] = 'given `updator` is not a function/callable'
            return reply

        updatorName = updator.__name__
        if updatorName.startswith('<'):
            reply['log'] = 'lambda functions are not allowed'
            return reply

        if autoUpdateAfter < 1:
            reply['log'] = '`autoUpdateAfter` too low'
            return reply
        
        if duplicateUpdateThreshold < 1:
            reply['log'] = '`duplicateUpdateThreshold` too low'
            return reply

        self.__cache[name] = {
            'lastUpdated': 0, 
            'updator': updator, 
            'value': _EmptyCacheValue(),
            'autoUpdateAfter': autoUpdateAfter, 
            'duplicateUpdateThreshold': duplicateUpdateThreshold
        }

        reply['status'] = True
        return reply

    def triggerKeyUpdate(self, key:str) -> dict:
        '''
        trigger update value of a key
        Args:
            key(str): name of the cache key

        Returns:
        ```
        {
            'status':bool, 
            'log':str
        }
        ```
        '''
        reply = {'status':False, 'log':''}

        if key not in self.__cache:
            reply['log'] = f'key `{key}` not found in the cache'
            return reply

        return self.__queue.push(key)
        
    def getValue(self, key:str) -> dict:
        '''
        attempt to get the value of a key set in the cache
        Args:
            key(str): name of the cache key

        Returns:
        ```
        {
            'status':bool, 
            'log':str, 
            'value':Any
        }
        ```
        '''
        
        reply = {'status':False, 'log':'', 'value':None}

        if key not in self.__cache:
            reply['log'] = 'unknown cache key given'
            return reply

        if isinstance(self.__cache[key]['value'], _EmptyCacheValue):
            reply['log'] = 'cache not yet ready'
            return reply

        reply['status'] = True
        reply['value'] = self.__cache[key]['value']
        return reply

def create(name:str) -> dict:
    '''
    create a new cache object
    Args:
        name(str): the name of the cache

    Returns:
    ```
    {
        'status':bool,
        'log':str,
        'cache': Cache
    }
    ```
    '''
    reply = {'status':False, 'log':'', 'cache':None}

    if name in Cache._Cache__ACTIVE_CACHES:
        reply['cache'] = Cache._Cache__ACTIVE_CACHES[name]
    else:
        try:
            reply['cache'] = Cache(name)
        except Exception as e:
            reply['log'] = f'error creating cache: {e}'
            return reply

    reply['status'] = True
    return reply

def get(name:str) -> Cache | None:
    '''
    get cache by its name
    Args:
        name(str): the cache name
    '''
    return Cache._Cache__ACTIVE_CACHES.get(name,None)

if __name__=='__main__':
    count = 0
    def updateCount():
        global count
        count += 1
        return count
    
    cacheReply = create('countCache')
    print(cacheReply)
    cache:Cache = cacheReply['cache']
    cache:Cache = get('countCache')

    print(cache.addKey('count', updateCount, autoUpdateAfter=5, duplicateUpdateThreshold=2))
    print(cache.getValue('count'))

    print(cache.triggerKeyUpdate('count')); time.sleep(1.1)
    print(cache.triggerKeyUpdate('count')); time.sleep(1.1)
    print(cache.triggerKeyUpdate('count')); time.sleep(1.1)

    while 1:
        print(cache.getValue('count'))
        time.sleep(1)
        
