from typing import Any
import pickle, os, sys

__config_root_path = os.path.join(os.path.expanduser('~'),'.kisaconf') 

__EXT = 'kisaconf'

if (not os.path.isdir(__config_root_path)) and os.system(f'mkdir "{__config_root_path}"'):
    sys.exit('failed to create config root path')

def _getTopicPath(topic:str):
    fout = os.path.join(__config_root_path,f'{topic}.{__EXT}')

    return fout
def _initTopic(topic:str):
    foutPath = _getTopicPath(topic)
    if not os.path.isfile(foutPath):
        with open(foutPath,'wb') as fout:
            pickle.dump({}, fout)

    return foutPath

def _getTopicAndKey(path:str) -> list[str,str]:
    '''
    path: topicName/keyName eg 'topic1/key1'

    @returns [topic,key]
    '''
    if ('/' not in path) or (' ' in path) or path.startswith('/') or path.endswith('/'):
        raise ValueError('invalid key path given')

    return path.split('/')

def getValue(path:str) -> Any|None:
    '''
    get the value of a set topic-key path
    Args:
        path(str): topicName/keyName eg 'topic1/key1'
    '''

    topic, key = _getTopicAndKey(path)

    with open(_initTopic(topic),'rb') as fin:
        return pickle.load(fin).get(key)
    
def setValue(path:str, value:Any) -> bool:
    '''
    set the value of a set topic-key path
    Args:
        path(str): topicName/keyName eg 'topic1/key1'
    '''
    topic, key = _getTopicAndKey(path)

    topicFile = _initTopic(topic)
    with open(topicFile,'rb') as fin:
        data = pickle.load(fin)

    data[key] = value

    with open(topicFile, 'wb') as fout:
        try: pickle.dump(data,fout)
        except: return False
    
    return True

def getTopic(topic:str) -> dict|None:
    '''
    get topic data
    Args:
        topic(str): the topic name
    '''
    topic,_ = _getTopicAndKey(f'{topic}/_')
    data = None

    topicPath = _getTopicPath(topic)

    if not os.path.isfile(topicPath):
        return data

    with open(topicPath,'rb') as fin:
        data = pickle.load(fin)

    return data

def getConfigPath() -> str:
    '''get path to the config files root directory'''
    return __config_root_path

def __init__() -> None:
    global __config_root_path
    _rootPath = getValue('_sys_/configPath')
    if _rootPath:
        __config_root_path = _rootPath
    else:
        setValue('_sys_/configPath', __config_root_path)

__init__()
