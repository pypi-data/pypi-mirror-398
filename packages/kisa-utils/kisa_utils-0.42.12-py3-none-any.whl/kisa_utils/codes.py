import random
import time
import string

__MAX_CODE_LENGTH = 32

__ID_SPACE = string.ascii_lowercase + string.ascii_uppercase + string.digits

def new(length:int=12, useSeparator:bool=False, xterSet:str=__ID_SPACE) -> str:
    '''
    generate a new code
    Args:
        length(int): length of the code to generate
        useSeparator(bool): include a separator ('-') in the code
        xterSet(str): the chatacters to use eg '0123456789' ensures the code only has numbers in it
    Note:
        compexity of the code will be len(xterSet)^length
    '''
    
    assert(length>0 and length<=__MAX_CODE_LENGTH)
    code = ''
    __ID_SPACE_length = len(xterSet)
    while length:
        code += xterSet[random.randrange(0,__ID_SPACE_length)]
        length -= 1
        
        if useSeparator and length and not(length%4):
            code += '-'
    return code

if __name__=='__main__':
    pass