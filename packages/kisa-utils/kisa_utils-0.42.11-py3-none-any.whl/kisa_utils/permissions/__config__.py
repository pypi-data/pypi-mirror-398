from unittest import result
from kisa_utils.storage import Path
import subprocess
import sys
import string

from kisa_utils.response import Response, Ok, Error
from kisa_utils.structures.validator import Value

# variables...
paths = {
    'db':f"{subprocess.check_output('realpath ~',shell=True).decode('utf-8').strip()}/.kisaperms"
}

dbFileName = '{projectId}.kperms'

# -----------------------------------------------------------------------------
def __init():
    for path in paths:
        if not Path.createDirectory(paths[path])['status']:
            sys.exit(f'failed to create path: {path}')

__init()