import subprocess
import hashlib

__ECRYPTION_SALT:str = 'kisa.encrypt@2023'
__HASH_SALT:str = 'k.i.s.a.hash@+9JI0'

def __encrypt(msg:str, returnBytes:bool=False, pswd:str=__ECRYPTION_SALT) -> str|bytes:
    '''
    this encryption is by no means meant to be secure. its simple obfusication really
    '''
    try:
        out = subprocess.run(f'''echo '{msg}' | openssl aes-256-cbc -a -iter=10 -pass pass:{pswd}''',check=True,shell=True,capture_output=True, text=True).stdout.strip()
        return out.encode('utf-8') if returnBytes else out
    except:
        raise ValueError('error calling <openssl> is it installed?')

def __decrypt(encryptedMsg:str, returnBytes:bool=False, pswd:str=__ECRYPTION_SALT) -> str|bytes:
    '''
    undo the effect of `__encrypt(...)`
    '''
    try:
        out=subprocess.run(f'''echo '{encryptedMsg}' | openssl aes-256-cbc -d -a -iter=10 -pass pass:{pswd}''',check=True,shell=True,capture_output=True, text=True).stdout.strip()
        return out.encode('utf-8') if returnBytes else out
    except:
        raise ValueError('error calling <openssl> is it installed?')

def __hash(msg:str|bytes, returnBytes:bool=False, salt:str|bytes = __HASH_SALT) -> str|bytes:
    '''
    hash a message
    '''
    if isinstance(msg,str):
        msg = bytes(msg,'utf-8')
    if isinstance(salt,str):
        salt = bytes(salt,'utf-8')
    
    # `sha3_256` is prefered to `sha256`
    _hash = hashlib.sha3_256(msg+salt).hexdigest()
    return bytes(_hash,'utf-8') if returnBytes else _hash

def decrypt(encryptedMsg:str, *, returnBytes:bool=False, password:str='') -> str|bytes:
    '''
    decrypt message
    Args:
        encryptedMsg(str): encrypted emssage to decrypt
        returnBytes:(bool): return `bytes` instead of `str` 
        password(str): the password used during encryption
    '''
    return __decrypt(encryptedMsg, returnBytes=returnBytes) if not password else __decrypt(encryptedMsg, returnBytes=returnBytes, pswd=password)

def encrypt(msg:str, *, returnBytes:bool=False, password:str='') -> str|bytes:
    '''
    encrypt message
    Args:
        msg(str): emssage to encrypt
        returnBytes:(bool): return `bytes` instead of `str` 
        password(str): the password to use during encryption
    '''
    return __encrypt(msg, returnBytes=returnBytes) if not password else __encrypt(msg, returnBytes=returnBytes, pswd=password)

def hash(msg:str|bytes, returnBytes:bool=False) -> str|bytes:
    '''
    hash a message
    Args:
        msg(str|bytes): the message to hash
        returnBytes(bool): return `bytes` instead of `str` 
    '''
    return __hash(msg, returnBytes=returnBytes)

def xor(data:bytearray, key:bytes|bytearray, startIndex:int, endIndex:int) -> bool:
    '''
    perform XOR operations on `data` using `key`
    Args:
        data(bytearray): bytearray to be encrypted with XOR
        key(bytes|bytearray): bytes|bytearray to use to performa the XOR operation on `data`
        startIndex(int): index from which to start performing the XOR operation
        endIndex(int): index at which performing the XOR operation will stop. the index is INCLUSIVE
            if `endIndex=-1` then `data` will be XOR'd to the very end
    
    Note:
        the XOR operation is done in chunks of length=len(key) where the next chunk starts at an index equal to last-index-of-prioir-chunk + 1
    '''

    if not isinstance(data, bytearray): return False
    if not isinstance(key, (bytes,bytearray)): return False

    dataLength = len(data)
    keyLength = len(key)

    if startIndex<0 or endIndex < -1: return False

    if endIndex==-1: endIndex = len(data)-1

    endIndex = min(endIndex, dataLength-1)

    if startIndex >= dataLength: return False

    if startIndex > endIndex: return False

    index = startIndex

    while index <= endIndex:
        data[index] ^= key[(index-startIndex)%keyLength]
        index += 1
        
    return True

if __name__=='__main__':
    data = bytearray([1,2,3,4,5])
    key = bytes([13,12,13,14])
    # key = bytes([11,12])
    # key = bytes([11,])

    print([c for c in data]); print(xor(data,key,0,-1))
    print([c for c in data]); print(xor(data,key,0,-1))
    print([c for c in data])

    pass