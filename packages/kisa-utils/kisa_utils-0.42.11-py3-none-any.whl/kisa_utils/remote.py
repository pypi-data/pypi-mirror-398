import requests

def sendRequest(url:str|bytes, method:str|bytes='post', jsonPayload:dict={}, timeout:int=180, **requestKwargs:dict) -> dict:
    '''
    attempt to send request with JSON payload.
    Args:
        url(str|bytes): resource to send request to
        method(str|bytes): request method; one of GET|POST
        jsonPayload(dict): dictionary with payload data
        timeout(int): how long to wait[SECONDS] before raising the timeout error
        **requestKwargs(dict): kwargs to be passed to the `requests.{post,get,put,etc}` calls

    Returns:
        ```
        {
            'status': bool,
            'log': str,
            'responseType':str, # STR|JSON,
            'response':None|str|dict # None if error occurered, `dict` if request returned JSON, `str` otherwise
        }
        ```
        
    @return {'status':BOOL, 'log':STR, }
    '''

    reply = {'status':False, 'log':'', 'response':None}

    method = method.lower()
    if method not in ['get','post']:
        reply['log'] = 'invalid method given'
        return reply

    try:
        if 'get'==method:
            response = requests.get(url,json=jsonPayload,timeout=(5,timeout), **requestKwargs)
        elif 'post'==method:
            response = requests.post(url,json=jsonPayload,timeout=(5,timeout), **requestKwargs)
        else:
            reply['log'] = 'invalid method given'
            return reply

        if response.status_code!=200:
            try: reply['response'] = response.json()
            except: pass
            
            reply['log'] = f'response returned error code: {response.status_code}, `{response.reason}`'
            return reply

        try:
            responseJSON = response.json()
            reply['response'] = responseJSON
            reply['status'] = True
            return reply
        except:
            reply['log'] = 'no JSON reply got'
            return reply
            
    except requests.exceptions.Timeout:
        reply['log'] = 'connection timeout'
        return reply
    except requests.exceptions.ConnectionError:
        reply['log'] = 'connection failed'
        return reply

