"""
Kisa Server Utilities
"""

import kisa_utils as kutils
from kisa_utils.storage import Path
from kisa_utils.response import Response, Ok, Error
from flask import Flask, request, jsonify, wrappers, render_template_string
from flask import current_app, g as app_ctx, make_response
from flask_cors import CORS
from functools import wraps
import copy
import inspect
from kisa_utils.structures.validator import Value
from kisa_utils.structures.validator import validateWithResponse
from pathlib import Path as pathLib
import string
import sys
from flask_basicauth import BasicAuth
from types import UnionType
import re
from kisa_utils.functionUtils import enforceRequirements
from werkzeug.exceptions import BadRequest
from typing import Dict, Any, Union, get_origin, get_args, Optional, Callable
import types


_VALID_HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
_WHITE_LISTED_PARAMS = ["headers"]

from typing import Optional, Callable
from functools import wraps
from flask import request, abort
import base64
import binascii


class SecurityPolicy:
    """
    Provides Flask decorators for common HTTP security policies.
    Each method returns a decorator that uses a provided callback for all validation logic.
    """

    @staticmethod
    def basic_auth(validator: Callable[[str, str], Response]) -> Callable:
        """
        Decorator for HTTP Basic Authentication.
        Expects 'Authorization: Basic <base64(username:password)>' header.
        `validator` receives (username, password) and returns a Response.

        Args:
            validator (Callable[[str, str], Response]): (username, password) -> Response.

        Raises:
            HTTPException: 
                401 (Unauthorized), 
                400 (Bad Request), 
                403 (Forbidden), 
                500 (internal server error).
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                auth = request.headers.get('Authorization')
                if not auth or not auth.startswith('Basic '):
                    abort(401, description="Basic authentication required.")

                try:
                    decoded_credentials = base64.b64decode(auth[len('Basic '):]).decode('utf-8')
                    username, password = decoded_credentials.split(':', 1)
                except (ValueError, UnicodeDecodeError, binascii.Error) as e:
                    abort(400, description="Malformed Basic authentication header.")

                resp = validator(username, password)
                if not resp:
                    abort(403, description=f"{resp.log}")
                
                try:
                    return f(*args, **kwargs)
                except Exception as  e:
                    abort(500, description=f"Internal server error: {str(e)}")


            return wrapper
        return decorator

    @staticmethod
    def bearer_token(validator: Callable[[str], Response]) -> Callable:
        """
        Decorator for Bearer Token authentication.
        Expects 'Authorization: Bearer <token>' header.
        `validator` receives (token_string) and returns a Response.

        Args:
            validator (Callable[[str], Response]): (token_string) -> Response.

        Raises:
            HTTPException: 
                    401 (Unauthorized), 403 (Forbidden)
                    500 (internal server error)
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                auth = request.headers.get('Authorization')
                if not auth or not auth.startswith('Bearer '):
                    abort(401, description="Bearer token authentication required.")
                
                token = auth[len('Bearer '):]
                try: 
                    resp = validator(token)

                    if not resp:
                        abort(403, description=f"{resp.log}")
                except Exception as e:
                    abort(500, description=f"Token validation error: {str(e)}")
            
                
                try:
                    return f(*args, **kwargs)
                except Exception as  e:
                    abort(500, description=f"Internal server error: {str(e)}")
            return wrapper
        return decorator

    @staticmethod
    def api_key(validator: Callable[[str], Response], header_name: str = 'X-API-KEY') -> Callable:
        """
        Decorator for API Key authentication.
        Looks for the API key in the specified `header_name`.
        `validator` receives the extracted API key string and returns bool.

        Args:
            validator (Callable[[str], bool]): (api_key_string) -> bool.
            header_name (str, optional): The name of the HTTP header containing the API key.
                Defaults to 'X-API-KEY'.

        Raises:
            HTTPException: 
                401 (Unauthorized), 403 (Forbidden),
                500 (internal server error)

        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                api_key = request.headers.get(header_name)
                
                if not api_key:
                    abort(401, description=f"API key required. Missing '{header_name}' header.")

                try: 
                    resp = validator(api_key)

                    if not resp:
                        abort(403, description=f"{resp.log}")
                except Exception as e:
                    abort(500, description=f"API-Key validation Err: {str(e)}")
                
                try:
                    return f(*args, **kwargs)
                except Exception as  e:
                    abort(500, description=f"Internal server error: {str(e)}")
                
            return wrapper
        return decorator

def __init() -> None:
    '''
    init the envrionment
    '''
    globals()['__ENDPOINTS'] = {}
    __app = Flask(__name__)
    CORS(__app)

    __app.config['PROPAGATE_EXCEPTIONS'] = False

    __basic_auth = BasicAuth(__app)
    globals()['__SERVER_APP'] = __app
    globals()['__BASIC_AUTH'] = __basic_auth

    # change logger to include time spend on a request
    import logging, logging.handlers, time
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.basicConfig(level=logging.INFO)
    __app.logger.addHandler(logging.handlers.SysLogHandler(address="/dev/log"))  # Address for journald

    @__app.before_request
    def beforeRequest():
        '''
        create a gate for all incoming requests
        '''
        app_ctx.start_time = time.perf_counter()
        app_ctx.start_timestamp = kutils.dates.currentTimestamp()

    @__app.after_request
    def logging_after(response):
        '''
        create an exit point for all requests
        '''
        # Get total time in milliseconds
        total_time = round(time.perf_counter() - app_ctx.start_time, 4)
        # Log the time taken for the endpoint 

        current_app.logger.info('[%s %s %s %d] %s', request.method, app_ctx.start_timestamp, total_time, response.status_code, request.path)
        
        return response


__init()

def __quoteKeys(string:str) -> str:
    '''
    quote keys to be used in the generated docs
    Args:
        string(str): the string to quote
    '''
    # Match keys followed by a colon, e.g., k1: or some_key123:
    return re.sub(r'(\b\w+\b)(\s*):', r'"\1"\2:', string)


def getEndpoints() -> dict:
    '''
    return a deep copy of endpoints. this is obviously because we dont to fuck with the original dict
    '''
    return copy.deepcopy(__ENDPOINTS)


def setEndpoints(group:str, endpoint:str, value:dict) -> None:
    '''
    set attributes of an endpoint
    Args:
        group(str): the endpoint group
        endpoint(str): the endpoint name
        value(dict): dict containing information such as handler, handler-file-path, etc
    '''
    if (existing_endpoint := __ENDPOINTS.get(group, {}).get(endpoint, None)):
        raise ValueError(f"Endpoint {endpoint} in group {group} already exists as {existing_endpoint}!")
    # if __ENDPOINTS.get(group, {}).get(endpoint, None):
    #     raise ValueError(f"Endpoint `{endpoint}` in group `{group}` already exists as `{get(endpoint)}`!")

    __ENDPOINTS[group] = __ENDPOINTS.get(group, {})

    groupEndpointKeys = list(__ENDPOINTS[group].keys())
    groupEndpoints = [_.lower() for _ in groupEndpointKeys]
    endpointLower = endpoint.lower()

    if endpointLower in groupEndpoints:
        index = groupEndpoints.index(endpointLower)
        raise ValueError(f"Endpoint `{endpoint}` in group `{group}` already exists! as `{groupEndpointKeys[index]}`")

    __ENDPOINTS[group][endpoint] = value


def __validateEndpointAndGroupName(name:str, _type:str) -> Response:
    '''
    validate names for both endpoints and group-names
    Args:
        name(str): the name to validate
        _type(str): the type/category of the name. one of `group|endpoint`
    '''
    allowedCharacters = string.digits + string.ascii_letters + "-_/"

    if not isinstance(_type, str):
        return Error(f" type `{_type}` expected a string but got `{type(_type)}`")

    _type = _type.lower()

    if not isinstance(name, str):
        return Error(f"{_type} name expected a string but got `{type(_type)}")

    name = name.strip().lower()

    if not name and _type != "group":
        return Error(f"{_type} name `{name}` is invalid. It cant be empty spaces")

    if " " in name:
        return Error(f"{_type} name `{name}` should not contain spaces")

    if name and len(name) < 3:
        return Error(f"{_type} name `{name}` should contain at least 3 characters")

    if "//" in name:
        return Error(f"{_type} name `{name}` should not contain `//`")

    for char in name:
        if char not in allowedCharacters:
            return Error(f"{_type} name `{name}` should contain characters from `{allowedCharacters}`")

    return Ok()


def __findCommonBase(path1:str, path2:str) -> str:
    """
    find the first common directory between two paths.
    Args:
        path1(str): first path
        path2(str): second path
    Example:
        ```
        path1:str = "/a/b/c/k"
        path2:str = "/a/b/d/e"

        __findCommonBase(path1, path2) -> "/a/b"
        ```
    """
    # Convert both paths to absolute paths (if not already)
    path1 = pathLib(path1).resolve()
    path2 = pathLib(path2).resolve()

    commonBase = None

    # Iterate through the parents of both paths
    for parent1 in path1.parents:
        for parent2 in path2.parents:
            if parent1 == parent2:
                commonBase = parent1
                break
        if commonBase:
            break
    return commonBase


def __getHandlerRelativePath(handler: Callable) -> str:
    '''
    get the path of the request handler relative to the file that called `servers.flask.startServer(...)`
    Args:
        handler(Callable): the request handler who'se relative path we want to get
    '''
    handlerFilePath = inspect.getsourcefile(handler)
    runningFilePath = __file__

    commonDir = __findCommonBase(handlerFilePath, runningFilePath)

    if commonDir is None:
        raise ValueError(
            f"No common base directory found between the path for handler `{handler}` and the running file path for `{__file__.split('/')[-1]}`.")

    relativePath = str(pathLib(handlerFilePath).relative_to(
        pathLib(commonDir))).strip(".py")
    relativePath = f"{relativePath}:{handler.__name__}"

    return relativePath


def entry(func):
    """
    Entry decorator automatically injects request data into a handler function
    before each request as keyword arguments. These include:

    - origin: The value of the 'Origin' header from the request, or None if not present.
    - headers: A dictionary of all headers in the request.
    - method: The HTTP method (e.g., GET, POST) used for the request.
    - payload: The JSON payload of the request, or an empty dictionary if no payload is present.

    Example usage:
        ```
        @entry()
        def handler(*, origin:str, headers:dict, method:str, payload:dict):
            print("Request origin:", origin)
            print("Request headers:", headers)
            print("HTTP method:", method)
            print("JSON payload:", payload)
        ```
    """

    signature = inspect.signature(func)

    for key, value in signature.parameters.items():
        if value.kind != inspect.Parameter.KEYWORD_ONLY:
            raise ValueError(
                f'function `{func.__name__}`: should only take keyword arguments or parameters!')

    def wrapper(*args, **kwargs):
        origin = request.headers.get('Origin')
        headers = dict(request.headers)
        method = request.method
        payload = request.get_json() if request.is_json else {}

        return func(origin=origin, headers=headers, method=method, payload=payload)

    __SERVER_APP.before_request(wrapper)

    return wrapper


# def exit(func):
#     signature = inspect.signature(func)

#     for key, value in signature.parameters.items():
#         if value.kind != inspect.Parameter.KEYWORD_ONLY:
#             raise ValueError(
#                 f'function `{func.__name__}`: should only take keyword arguments or parameters, this case response only')

#     def wrapper(response):
#         return func(response=response)

#     __SERVER_APP.after_request(wrapper)

#     return wrapper

@enforceRequirements
def __verifyResponseHeaders(headers:dict[str, str|int|float], /) -> Response:
    '''
    validate response headers to be set
    Args:
        headers(dict[str, str|int|float]): the headers dict to validate
    '''

    keyTypes, valuetypes = get_args(__verifyResponseHeaders.__annotations__['headers'])

    for header in headers:
        if not isinstance(header, keyTypes):
            return Error(f'response header `{header}` expected to be of type `{keyTypes}`')
        if not isinstance(headers[header], valuetypes):
            return Error(f'response header `{header}` value expected to be of type `{valuetypes}`')

    return Ok()

# @enforceRequirements
def endpoint(
    name:str|Callable = '', group:str = '', methods:list[str] = ['POST'],
    security: Optional[Callable] = None,
    responseHeaders:dict[str, str|int|float] = {}
) -> Callable:
    """
    Creates Flask endpoints.

    Args:
        name (str): The name of the endpoint. Defaults to the handler name.
        group (str): The group under which the endpoint falls. The actual endpoint will be ".../{group}/{name}".
        methods (list): List of HTTP methods to allow.
        security: One of servers.flask.SecurityPolicy.basic_auth, bearer_token, or api_key.
        responseHeaders (dict): Headers to set for responses.

    Note:
        If the decorated function (handler) needs to capture the headers of the incoming request,
        it must have a keyword-only argument named `headers` of type `dict` with no default value,
        e.g., 
        ```
        def handler(*, headers: dict) -> Response:
            ...
        ```
    """
    def decorator(func):
        # in case the decorator is called as `@endpoint` as opposed to `@endpoint(...)`
        nonlocal name, group, methods , security
  
        if callable(name):
            name, group = '', ''

        methods = _normalize_and_validate_methods(methods)
        
        if responseHeaders and not (resp := __verifyResponseHeaders(responseHeaders)):
            raise ValueError(resp.log)

        __DEFAULTS = {}

        if 1:
            _group = group + '/' if group else ''
            _name = '/' + _group + (name or func.__name__)

            if security is not None:
                handler = security(func) 
            else:
                handler = func

            if not (endpointValidationReply := __validateEndpointAndGroupName(_name, "endpoint")):
                raise ValueError(endpointValidationReply.log)

            if not (groupValidationReply := __validateEndpointAndGroupName(_group, "group")):
                raise ValueError(groupValidationReply.log)

            signature = inspect.signature(func)
            typeHints = func.__annotations__
            # parameters = signature.parameters

            headers_type = typeHints.get("headers")
            if headers_type and not (headers_type is dict):
                raise TypeError("arg::headers type must be 'dict'")

            if not handler.__doc__ or not (handler.__doc__.strip()):
                raise ValueError(
                    f"handler function {func.__name__} has no docString!")

            if not typeHints.get("return", None):
                raise TypeError(
                    f"handler function {func.__name__} has no return type")

            expectedReturnType = typeHints['return']

            if typeHints.get("return") not in (expectedReturns := (Response, str, tuple)):
                raise TypeError(
                    f"handler function {func.__name__} return type should be one of {'|'.join([_.__name__ for _ in expectedReturns])}")

            args = []
            kwargs = []

            for key, value in signature.parameters.items():
                if value.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    raise TypeError(
                        f"function `{handler.__name__}` should take either positional-only or keyword-only parameters")

                if value.kind == inspect.Parameter.POSITIONAL_ONLY:
                    if key == "headers":
                        raise ValueError(f"arg: {key}, should ony be passed as keyword_only argument!")
                    
                    if value.default is not inspect.Parameter.empty:
                        if not (resp := validateWithResponse(value.default, typeHints[key])):
                            raise ValueError(f'arg `{key}` default value: {resp.log}')
                        args.append((key, value.default))
                    else:
                        args.append((key,))
                elif value.kind == inspect.Parameter.KEYWORD_ONLY:
                    if value.default is not inspect.Parameter.empty:
                        if key == "headers":
                            raise ValueError(f'arg `{key}` should have no default value')
                        
                        if not (resp := validateWithResponse(value.default, typeHints[key])):
                            raise ValueError(f'arg `{key}` default value: {resp.log}')
                        
                        kwargs.append((key, value.default))
                    else:
                        kwargs.append((key,))

                if str(value).startswith('*'):
                    raise ValueError(
                        f'function `{func.__name__}`: *{key} or **{key} not allowed in function signature')

                # print(f'<{key}> <{value}> <{value.default}> <{inspect._empty==value.default}>')

                hint = typeHints.get(key, None)
                if not hint:
                    raise TypeError(f"parameter {key} has no type hint")

                if inspect._empty != value.default:
                    __DEFAULTS[key] = value.default

            # print(typeHints)
            if "headers" in typeHints and "headers" in _WHITE_LISTED_PARAMS:
                del typeHints["headers"]

            validationStructure = copy.deepcopy(typeHints)
            del validationStructure["return"]

            __group = group if group else 'default'
            # print("handler====>", handler)
            new_entry = {
                "handler": handler,
                "expectedStructure": validationStructure,
                "path": __getHandlerRelativePath(handler),
                "docs": handler.__doc__,
                "defaults": __DEFAULTS,
            }
            setEndpoints(__group, _name, new_entry)

        @wraps(func)
        def w():
            nonlocal handler, new_entry

            resp = process_request_data(request, new_entry["expectedStructure"], defaults=copy.deepcopy(__DEFAULTS))
            if not resp: 
                return resp

            payload = resp.data
                
            # Handle text payloads differently
            if isinstance(payload, (str, bytes)):
                if len(args) == 1 and not kwargs:
                    return func(payload)
                raise BadRequest("Text input requires exactly one positional parameter")

            nonlocal validationStructure
            _args = []
            _kwargs = {}

            for item in args:
                arg = item[0]

                if arg in payload:
                    _args.append(payload[arg])
                else:
                    if len(item) == 2:
                        default = item[1]
                        _args.append(default)
                        payload[arg] = default

            for item in kwargs:
                kwarg = item[0]
                _headers_present = True if kwarg == "headers" else False  

                if kwarg in payload:
                    _kwargs[kwarg] = payload[kwarg]
                else:
                    if _headers_present and kwarg == "headers":
                            _kwargs[kwarg] = dict(request.headers)
                            continue
                    
                    if len(item) == 2:
                        default = item[1]
                        _kwargs[kwarg] = default
                        payload[kwarg] = default

            validationResponse = validateWithResponse(
                payload, validationStructure)
            if not validationResponse:
                return validationResponse

            resp = handler(*_args, **_kwargs)

            nonlocal expectedReturnType
            if not isinstance(resp, expectedReturnType):
                raise TypeError(f'`{handler.__name__}` did NOT return a {expectedReturnType.__name__} object')

            if isinstance(resp, tuple):
                if 2 != len(resp):
                    raise Exception(f'expected 2-item tuple from the endpoint handler!')
                if not isinstance(resp[1], int):
                    raise Exception(f'expected status_code as the second item in the tuple from the endpoint handler!')

            if not responseHeaders:
                return resp
            
            if isinstance(resp, tuple):
                resp,statusCode = resp
            else:
                statusCode = 200

            if isinstance(resp, Response):
                resp = resp.asJSON

            response =  make_response(resp,statusCode)

            for header in responseHeaders:
                response.headers[header] = responseHeaders[header]

            return response

        w.__name__ = f'__kisa_wrapper_{_group}_{handler.__name__}'
        __SERVER_APP.route(_name, methods=methods)(w)
        
        return func

    # in case the decorator is called as `@endpoint` as opposed to `@endpoint(...)`
    if callable(name):
        return decorator(name)
    return decorator

@enforceRequirements
def _normalize_and_validate_methods(methods: list[str], /) -> list:
    '''
    Normalize and validate HTTP methods
    Args:
        methods(list[str]): the list of methods to validate
    '''
    if not methods:
        return ['POST']
    
    if not methods:
        raise ValueError("Methods list cannot be empty")
    
    normalized_methods = [method.upper() for method in methods]
    
    for method in normalized_methods:
        if method not in _VALID_HTTP_METHODS:
            raise ValueError(
                f"Invalid HTTP method: {method}. "
                f"Valid methods are: {', '.join(sorted(_VALID_HTTP_METHODS))}"
            )
    
    return normalized_methods


def process_request_data(request, expected_structure:dict, *, defaults:dict = {}) -> Response:
    """
    Process incoming request data.

    Args:
        request: the request to process
        expected_structure(dict): the structure against which to process the request data
    """
    urlData = defaults
    urlData.update(request.values.to_dict())
    jsonData = {}
    
    if request.is_json:
        jsonData = request.json

    # print(jsonData, urlData)

    urlData.update(jsonData)

    resp = conform_dict(urlData, expected_structure)
    # print("resp=====>", resp)
    if not resp: return resp
        
    return Ok(resp.data)

def startServer(*, host:str = '0.0.0.0', port:int = 5000, debug:bool = True, threaded:bool = True, userName:str = 'user', password:str = '0000', **flaskKwargs:dict) -> Response:
    '''
    start the flask server
    Args:
        host(str): the ip address to bind the server to
        port(int): the port to use
        debug(bool): wheather to run the server in debug mode or not
        threaded(bool): spawn a new thread for every incoming request
        userName(str): user-name to use for accessing the `api/docs` endpoint (basic-auth)
        password(str): password to use for accessing the `api/docs` endpoint (basic-auth)
        **flaskKwargs: other keyword arguments to provide to flask's `app.run`
    '''
    runningFile = sys.argv[0].split("/")[-1]

    stack = inspect.stack()
    fileCallingStartServer = stack[1].filename.split("/")[-1]

    if ".py" in runningFile and runningFile != fileCallingStartServer:
        raise AssertionError(
            f"start server is not being from the running file. \n runningFile: {runningFile} \n fileCallingStartServer: {fileCallingStartServer}")

    __SERVER_APP.config['BASIC_AUTH_USERNAME'] = userName
    __SERVER_APP.config['BASIC_AUTH_PASSWORD'] = password

    generateSourceMap()
    generateDocs()

    __SERVER_APP.run(
        host,
        port,
        debug=debug,
        threaded=threaded,
        **flaskKwargs
    )
    return Ok()


def getAppInstance():
    '''
    return the main flask-app instance
    '''
    return __SERVER_APP


def generateDocs():
    '''
    generate endpoint and HTML for the api docs
    '''
    data = getEndpoints()
    print('generating docs...')
    _html = generate_html(data)

    @__SERVER_APP.route('/api/docs', methods=['GET'])
    @__BASIC_AUTH.required
    def docs() -> str:
        return render_template_string(_html)


def __customPrettyPrint(data: str, indent: int = 2) -> str:
    '''
    pretty print json-like string (doesnt have to be valid json eg "[int|float, {k:str}]")
    '''
    result = ""
    level = 0
    i = 0
    in_string = False
    buffer = ""

    def flush_buffer(newline=True):
        nonlocal buffer, result
        stripped = buffer.strip()
        if stripped:
            result += " " * (indent * level) + stripped
            if newline:
                result += "\n"
        buffer = ""

    while i < len(data):
        char = data[i]

        if char == '"':
            in_string = not in_string
            buffer += char

        elif char in '{[' and not in_string:
            buffer = buffer.rstrip()  # ensure no extra space before {
            buffer += ' '+char
            flush_buffer()
            level += 1

        elif char in '}]' and not in_string:
            flush_buffer()
            level -= 1
            result += " " * (indent * level) + char
            if i + 1 < len(data) and data[i + 1] == ',':
                result += ','
                i += 1
            result += "\n"

        elif char == ',' and not in_string:
            buffer += char
            flush_buffer()

        elif char == ':' and not in_string:
            buffer = buffer.rstrip()  # remove space before colon
            buffer += ":"

            # Ensure exactly one space after colon
            # Look ahead — if the next char is not a space, insert one manually
            if i + 1 < len(data) and data[i + 1] != ' ':
                buffer += " "
            elif i + 1 < len(data) and data[i + 1] == ' ':
                # Skip all extra spaces after colon
                while i + 1 < len(data) and data[i + 1] == ' ':
                    i += 1
                buffer += " "

        else:
            buffer += char

        i += 1

    flush_buffer()
    return result.strip()


def generate_html(data:dict[str, dict[str, Any]]) -> str:
    '''
    generate the api-docs HTML
    Args:
        data(dict[str, dict[str, Any]]): the data from which to generate the HTML docs
    '''
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px; max-width: 800px; margin: auto;">
        <h1 style="text-align: center; color: #333;">API Documentation</h1>

        <!-- Filter and Search Controls -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <select id="groupFilter" style="padding: 8px; font-size: 1em;">
                <option value="">All Groups</option>
                {}
            </select>
            <input type="text" id="searchInput" placeholder="Search endpoints..." style="padding: 8px; font-size: 1em; width: 60%;" onkeyup="filterContent()">
        </div>
    """.format(''.join(f'<option value="{group}">{group.capitalize()}</option>' for group in data.keys()))

    # Generate the HTML structure for each group and endpoint
    for group, endpoints in data.items():
        html += f"""
        <details class="group" data-group="{group}" style="border: 1px solid #ddd; border-radius: 8px; background-color: #fff; margin-bottom: 15px; padding: 15px;">
            <summary style="font-size: 1.4em; font-weight: bold; cursor: pointer; outline: none; color: #333;">
                {group.capitalize()}
            </summary>
            <div class="endpoints">
        """

        for endpoint, details in endpoints.items():
            html += f"""
            <div class="endpoint" data-endpoint="{endpoint}">
                <h3 style="font-size: 1.2em; color: #0073e6;">Endpoint: <span class="highlight">{endpoint}</span></h3>
            """

            if details.get('docs'):
                html += f"""
                <p style="margin: 5px 0; font-size: 0.9em;">
                    <strong>Documentation:</strong>
                    <pre style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{details['docs'].strip()}</pre>
                </p>
                """

            # Display the expected structure as a formatted code snippet
            html += "<p style='margin: 5px 0;'><strong>Expected Structure:</strong><br>"
            html += "<pre style='background-color: #272822; color: #f8f8f2; padding: 10px; border-radius: 5px; font-size: 0.9em; overflow-x: auto;'>"
            html += "{<br>"

            __defaults = details['defaults']

            for key, val in details['expectedStructure'].items():
                # print(key, val, isinstance(val, type))
                expandStructure:bool = False
                
                if isinstance(val, UnionType):
                    types = val.__args__
                    _type = '|'.join(_.__name__ for _ in types)

                elif isinstance(val, (type, Value)):
                    _type = val.__name__
                else:
                    _type = type(val).__name__ #+ f'\n  {val} \n'.replace("'",'').replace('class ','').replace('<','').replace('>','')
                    expandStructure = True

                html += f"<span style='color: #66d9ef;'>&nbsp;&nbsp;'{key}'</span>: <span style='color: #a6e22e;'>{_type}</span>,"
                if expandStructure:
                    expanded:str = f'{val}'\
                        .replace("'",'')\
                        .replace('class ','')\
                        .replace('<','')\
                        .replace('>','')\
                        .replace(' | ','|')\
                        .replace(': ',':')
                    expanded = __quoteKeys(expanded)

                    indentation = '&nbsp;'*(len(type(val).__name__)+len(':'))
                    expanded = __customPrettyPrint(expanded).replace('\n',f'<br>{indentation}')
                        
                    html += f"<br><span style='color: #66d9ef;'>{indentation}</span> <span style='color: #fae22e;'>{expanded}</span>"

                if key in __defaults:
                    trailingComma = False
                    if html[-1] in [',']: 
                        html = html[:-1]
                        trailingComma = True

                    html += " <span style='color: #ef66d9; font-weight:bold;'>=</span>"
                    html += f" <span style='color: #ffa000; font-weight:bold;'>{__defaults[key]}</span>"
                    if trailingComma: html += ','

                html += "<br>"

            html += "}</pre></p></div>"

        html += """
            </div>
        </details><br>
        """

    # JavaScript for filtering and search highlighting
    html += """
        <script>
            function filterContent() {
                let groupFilter = document.getElementById("groupFilter").value.toLowerCase();
                let searchInput = document.getElementById("searchInput").value.toLowerCase();

                // Iterate over each group and endpoint to apply filters
                document.querySelectorAll(".group").forEach(group => {
                    let groupName = group.getAttribute("data-group").toLowerCase();
                    let groupMatches = groupFilter === "" || groupName === groupFilter;

                    // Show or hide group based on filter
                    group.style.display = groupMatches ? "block" : "none";

                    if (groupMatches) {
                        let endpointMatchFound = false;

                        // Iterate over each endpoint within the group
                        group.querySelectorAll(".endpoint").forEach(endpoint => {
                            let endpointName = endpoint.getAttribute("data-endpoint").toLowerCase();
                            let matchesSearch = endpointName.includes(searchInput);

                            // Highlight matches
                            let highlightSpan = endpoint.querySelector(".highlight");
                            if (searchInput) {
                                let regex = new RegExp(searchInput, "gi");
                                highlightSpan.innerHTML = endpointName.replace(regex, (match) => `<span style="background-color: #ffeb3b;">${match}</span>`);
                            } else {
                                highlightSpan.innerHTML = endpointName;
                            }

                            endpoint.style.display = matchesSearch ? "block" : "none";
                            if (matchesSearch) endpointMatchFound = true;
                        });

                        // If no endpoint in the group matches the search, hide the group
                        if (!endpointMatchFound) {
                            group.style.display = "none";
                        }
                    }
                });
            }

            // Event listener for dropdown filter
            document.getElementById("groupFilter").addEventListener("change", filterContent);
        </script>
    """

    html += "</body></html>"
    return html


def generateSourceMap() -> None:
    '''
    generate a map of all endpoints and the file+function in which its handler defines
    '''
    data = getEndpoints()
    endpointsMap = {}
    # basePath = ''

    for group in data.keys():
        items = data[group]
        for endpoint in items.keys():
            endpointsMap[endpoint] = items[endpoint]['path']
            # string = f"{endpoint} ===> {items[endpoint]['path']}\n"
            # fwrite.write(string)

    with open('sourcemap.txt', 'w') as fout:
        for endpoint in sorted(endpointsMap.keys()):
            fout.write(f'{endpoint} -> {endpointsMap[endpoint]}\n')

def conform_dict(data: Dict[str, Any], structure: Dict[str, Any]) -> Response:
    """
    Converts and validates a dictionary to match a specified structure.
    
    Args:
        data: Input dictionary to be converted
        structure: Dictionary specifying expected types/structure
                  (e.g., {"age": int, "profile": {"name": str, "height": float}})
    
    Returns:
        Converted dictionary that matches the structure
    
    Raises:
        ValueError: If data cannot be converted to the expected types
        KeyError: If required keys are missing
    """
    result = {}

    # print("expected structure===>", structure)
    # print("received data===>", data)
    
    for key, expected_type in structure.items():
        if key not in data:
            return Error(f"Missing required key: {key}")

        value = data[key]
        
        # Handle nested dictionaries
        if isinstance(expected_type, dict):   
            if not isinstance(value, dict):
                return Error(f"Expected dict for key '{key}', got {type(value)}")
            
            resp = conform_dict(value, expected_type)
            if not resp: return resp

            result[key] = resp.data
            continue
        
        # Handle union types (e.g., int | float)
        if not (_resp := validateWithResponse(value, expected_type)):
            return Error(f'key `{key}`: {_resp.log}')
        result[key] = value

        origin = get_origin(expected_type)

    return Ok(result)

def convert_value(value:Any, target_type:type)->Any:
    '''
    convert `value` to type `target_type`
    Args:
        value(Any): the value to convert
        target_type(type): the type into which the value should be converted
    Example:
        ```
        convert_value("17", int) -> 17
        ```
    Note:
        `target_type` can be a union eg `int|float`
    '''
    if isinstance(target_type, types.UnionType):
        return _convert_union(value, target_type)
    elif isinstance(target_type, type):
        return _convert_single_type(value, target_type)
    else:
        raise ValueError(f"Unsupported target type: {target_type}")

def _convert_union(value:Any, union_type:type)->Any:
    '''
    convert `value` to one of the types in `union_type`
    Args:
        value(Any): the value to convert
        union_type(type): the types union into which the value should be converted eg `int|float`
    Example:
        ```
        _convert_union("17", int|float) -> 17
        ```
    '''
    allowed_types = get_args(union_type)

    if type(value) in allowed_types: return value

    val_length = len(value.split("."))
    
    t = float if val_length > 1 else int
    try:
        return _convert_single_type(value, t)
    except (ValueError, TypeError):
        raise ValueError(f"Cannot convert {value} to any of {allowed_types}")

def _convert_single_type(value:Any, target_type:type)->Any:
    '''
    convert `value` to type `target_type`
    Args:
        value(Any): the value to convert
        target_type(type): the type into which the value should be converted
    Example:
        ```
        convert_value("17", int) -> 17
        ```
    '''
    # return value if structure type is similar to data value
    if type(value) == target_type:
        return value
    
    if target_type is bool:
        if isinstance(value, str):
            value = value.lower()
            if value in ('true'):
                return True
            if value in ('false'):
                return False
        raise ValueError(f"Invalid boolean value: {value}")
    
    elif target_type is int:
        try:
            return int(float(value)) if isinstance(value, str) and '.' in value else int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert {value} to int")
    
    elif target_type is float:
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot convert {value} to float")
    
    # Default conversion
    try:
        return target_type(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert {value} to {target_type.__name__}: {str(e)}")

# startServer()
if __name__ == "__main__":
    # print('======> app:', getAppInstance())
    startServer()