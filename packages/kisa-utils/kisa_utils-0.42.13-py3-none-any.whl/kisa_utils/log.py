from kisa_utils import db, config, storage, dates, codes
import json

def __getTopicKey():
    return '_sys_/log:'

def __getConfigKey(key):
    return __getTopicKey()+key

def write(topic:str, msg:str, other:dict={}) -> dict[str, bool|str]:
    '''
    write/save a log
    Args:
        topic(str): topic of the log
        msg(str): the actual log message (120 character max)
        other(dict): dict object containing any other data you may need in the log

    Returns:
        the standard dict;
        ```
        {
            'status': bool, 
            'log': str
        }
        ```
    '''
    reply = {'status':False, 'log':''}

    topic, msg = topic.strip(), msg.strip()

    if not topic:
        reply['log'] = 'no `topic` given'
        return reply

    if not msg:
        reply['log'] = 'no `msg` given'
        return reply

    otherJSON = ''
    if not isinstance(other, (str, bytes)):
        try:
            otherJSON = json.JSONEncoder().encode(other)
        except:
            reply['log'] = 'failed to jsonify `other`'
            return reply
    else:
        otherJSON = other

    with db.Api(
        config.getValue(__getConfigKey('dbPath')), 
        readonly=False
    ) as handle:
        return handle.insert('entries',[
            (
                dates.currentTimestamp(),
                topic,
                msg,
                otherJSON
            ),
        ])


        reply['status'] = True
    return reply

def __init__() -> None:
    '''
    init the module
    '''
    defaults = {
        'dbPath': storage.Path.join(config.getConfigPath(),'logs'),
        'tables': {
            'entries':'''
                tstamp  varchar(32) not null,
                topic   varchar(32) not null,
                msg     varchar(128) not null,
                other   json not null
            ''',
        }
    }

    for key in defaults:
        topicKey = __getConfigKey(key)
        if 1 or not config.getValue(topicKey):
            config.setValue(topicKey, defaults[key])


    with db.Api(
        config.getValue(__getConfigKey('dbPath')), 
        tables = config.getValue(__getConfigKey('tables')),
        readonly=False
    ) as handle: pass

__init__()

if __name__=='__main__':
    print(write('test','testing 1,2...',{}))