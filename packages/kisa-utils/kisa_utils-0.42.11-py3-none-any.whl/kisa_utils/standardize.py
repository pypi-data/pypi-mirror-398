def phoneNumber(number:str, countryCode:str='256') -> str|None:
    '''
    standardize phone number
    Args:
        number(str): the phone number to standardize
        countryCode(str): the country code to use (without the leading `'+'`)
    Returns:
        + `str` if all went well
        + `None` if an error occured (invalid phone number given)
    Examples:
        ```
        phoneNumber('701222333') -> '256701222333'
        phoneNumber('2560701222333') -> None
        phoneNumber('256701222333') -> '256701222333'
        phoneNumber('70122233') -> None
        phoneNumber('701222333', '230') -> '230701222333'
        phoneNumber('0701222333', '230') -> '230701222333'
        ```
    '''
    number = number.strip('+')
    if not number.isdigit(): return None

    if number.startswith(countryCode): 
        return None if len(number) not in [12] else number
    
    number = str(number).strip().lstrip('0')
    
    if number.startswith(countryCode):
        number = number[len(countryCode):]
    if number.startswith('0'):
        number = number[1:]
    
    number = countryCode + number
    
    if len(number) not in [12]:
        return None
    
    return number

def network(number:str) -> str|None:
    '''
    get network that the phone number belongs to
    Args:
        number(str): the phone number whose network should be resolved
    Returns:
        + `str`, one of `mtn | airtel` if the phone number is valid
        + None if the phone number is invalid
    '''
    _standardizedNumber = phoneNumber(number)
    if not _standardizedNumber:
        return None
    
    networkCodes = _standardizedNumber[3:5]
    if networkCodes in ['77','78','76', '79']:
        return 'mtn'
    elif networkCodes in ['70','75','74']:
        return 'airtel'
    return None

if __name__=='__main__':
    for number,status in [
        ('70',None),
        ('701173040','256701173040'),
        ('0701173040','256701173040'),
        ('+2560701173040','256701173040'),
        ('+256701173040','256701173040'),
        ('256701173040','256701173040'),
        ('25670117304',None),
    ]:
        reply = phoneNumber(number)
        assert reply==status, f'{number} returned {reply} instead of {status}'