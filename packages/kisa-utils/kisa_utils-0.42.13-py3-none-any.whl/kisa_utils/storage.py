import os, glob, json
import inspect
from kisa_utils.response import Response, Error, Ok

encodeJSON = json.JSONEncoder().encode
decodeJSON = json.JSONDecoder().decode

class _Meta(type):
    @property
    def HOME(cls):
        '''
        get user's home directory
        '''
        return os.path.expanduser('~')

class Path(metaclass=_Meta):
    join          = os.path.join
    directoryName = os.path.dirname

    @staticmethod
    def exists(path:str) -> bool:
        'check if `path` exists. returns True/False'
        return os.path.exists(path)

    @staticmethod
    def isDirectory(path:str) -> bool:
        return os.path.isdir(path)

    @staticmethod
    def isFile(path:str) -> bool:
        return os.path.isfile(path)

    @staticmethod
    def createDirectory(path:str) -> Response:
        '''
        attempt to create a directory provided in `path`. 
        Args:
            path(str): the path to create

        Note:
            if any intermediate directories dont exist, they will be created as well

        '''
        if os.system(f"mkdir -p '{path}' 2> /dev/null"):
            return Error('failed to create directory. please review your permissions')
        
        return Ok()
    
    @staticmethod
    def createShortcut(source:str, destination:str) -> Response:
        '''
        attempt to create a shortcut.
        Args:
            source(str): the path we want to create a shortcut to
            destination(str): the path to the shortcut 
        '''

        if not Path.exists(source):
            return Error('the source path does not exist')

        if Path.exists(destination):
            return Error('the destination path already exists')

        if os.system(f"ln -s -T '{source}' '{destination}' 2> /dev/null"):
            return Error('failed to create the shortcut. please confirm that all necessary paths are valid and exist')
        
        return Ok()

    @staticmethod
    def delete(path:str) -> Response:
        '''
        attempt to delete `path`.

        Note:
            if the path is a directory, it will NOT be deleted if its empty 
        '''

        if not Path.exists(path):
            return Error('path does not exist')

        if Path.isDirectory(path) and os.listdir(path):
            return Error('can not delete a non-empty directory')

        if Path.isFile(path):
            if os.system(f"rm '{path}' 2> /dev/null"):
                return Error('failed to delete the file. please ensure you have the right permissions')
        else:
            if os.system(f"rmdir '{path}' 2> /dev/null"):
                return Error('failed to delete the directory. please ensure you have the right permissions')
        
        return Ok()

    @staticmethod
    def copy(source:str, destination:str) -> Response:
        '''
        attempt to copy a file/directory
        Args:
            source(str): the path we want to copy
            destination(str): the path to the new copy of the file/directory 
        '''

        if not Path.exists(source):
            return Error('the source path does not exist')

        if Path.exists(destination):
            return Error('the destination path already exists')

        if os.system(f"cp -rfHpu '{source}' '{destination}' 2> /dev/null"):
            return Error('failed to copy the source. please confirm that all necessary paths are valid and exist')
        
        return Ok()

    @staticmethod
    def listDirectory(path:str) -> Response:
        '''
        attempt to list the contents of a directory
        Args:
            path(str): the path to the directory we want to list
        '''

        if not Path.isDirectory(path):
            return Error('the path given is not a directory')

        path += '/*'
        contents = [os.path.abspath(f) for f in glob.glob(path)]

        return Ok(contents)

    @staticmethod
    def getMyAbsolutePath() -> str:
        '''
        return the absolute path to the file where this function is called

        Examples:
            if called from:
            * /a/b/c/d/file.py, it will return '/a/b/c/d/file.py'

            * ~/file.py, it will return '/home/{user}/file.py'
        '''
        # Get the frame of the calling function
        caller_frame = inspect.currentframe().f_back

        # Get the file path from the frame
        caller_file = inspect.getframeinfo(caller_frame).filename

        # Return the absolute path of the caller file
        return os.path.abspath(caller_file)

    @staticmethod
    def directoryBackAt(path:str, howFarBack:int=0) -> Response:
        '''
        get directory thats `howFarBack` steps from `path`
        Args:
            path(str): path to origin file/directory from where to navigate backwards
            howFarBack(int): how far back to go from the origin `path`. 0 refers the the directory containing the path

        Examples:
            consider:
            ```
            `path` = '/a/b/c/d/e/f/x.png'
            if `howFarBack` = 0, then final directory = '/a/b/c/d/e/f'

            if `howFarBack` = 1, then final directory = '/a/b/c/d/e'
            
            if `howFarBack` = 4, then final directory = '/a/b'
            ```
        '''

        if not Path.exists(path):
            return Error('could not find the given path')

        if howFarBack<0:
            return Error('invalid value given for `howFarBack`')

        parent = os.path.dirname(path)

        if howFarBack >= parent.count('/'):
            return Error('value of `howFarBack` goes beyond the root directory `/`')

        return Ok('/'.join(parent.split('/')[:-howFarBack]) if howFarBack else parent)

    @staticmethod
    def getAbsolutePath(path:str) -> str:
        '''
        get absolute path to file
        Args:
            path(str): path, relative or otherwise whose absolute path we need
        '''
        return os.path.abspath(path)


if __name__=='__main__':
    print(Path.getAbsolutePath('.'))