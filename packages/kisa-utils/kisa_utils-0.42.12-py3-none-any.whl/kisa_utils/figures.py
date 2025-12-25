from typing import List

def humanizeFigure(figure:int|float, toInt:bool=True, useNearestUpper:bool=False) -> str:
    '''
    return string version of figure with commas where they make sense
    Args:
        figure(int|float): value to humanize
        toInt(bool=True): convert figure to int (for floats)
        useNearestUpper(bool): round off to nearest upper figure (base 100 used by default)
    Examples:
        ```
        humanizeFigure(123456.908) -> '123,456'
        humanizeFigure(123456.908, toInt=False) -> '123,456.908'
        humanizeFigure(123456.908, useNearestUpper=True) -> '123,500'
        ```
    '''
    #if figure<1000:
    #    return str(figure)

    figure = figure if figure else 0

    if useNearestUpper:
        toInt = True

    if toInt: 
        figure = int(figure)

    if useNearestUpper:
        figure = toNearestUpper(figure)

    figureAsString = str(figure)
    sign_prefix = ''
    if (figureAsString and '-'==figureAsString[0]):
        sign_prefix = '-'
        figureAsString = figureAsString[1:]

    decimal = '.'+figureAsString.split('.')[-1] if '.' in figureAsString else ''
    real = figureAsString.split('.')[0]
    
    real_len = len(real)

    comma_count = real_len//3 if real_len%3 else (real_len//3)-1
    
    value:List[str] = []
    
    n = 1
    while n<=real_len:
        value.insert(0,real[-n])
        if (not n%3) and (n!=real_len):
            value.insert(0,',')
        n += 1
    
    return sign_prefix + ''.join(value)+decimal

def toNearestUpper(value:int|float, base:int=100) -> int:
    '''
    convert figures to nearest upper base value
    Args:
        value(int|float): the value to convert
        base(int): the base to use for the conversion
    Examples:
        ```
        toNearestUpper(1234) -> 1300
        toNearestUpper(1234, 50) -> 1250
        toNearestUpper(1234567, 1000) -> 1235000
        ```
    '''
    value = int(value)
    return int(value + base-(value%base) if value%base else value)

def toNearestLower(value:int|float, base:int=100) -> int:
    '''
    convert figures to nearest lower base value
    Args:
        value(int|float): the value to convert
        base(int): the base to use for the conversion
    Examples:
        ```
        toNearestLower(1234) -> 1200
        toNearestLower(1234, 50) -> 1200
        toNearestLower(1234567, 1000) -> 1234000
        ```
    '''
    value = int(value)
    return int(value - (value%base) if value%base else value)

def toNearest(value:int|float, base:int=100):
    '''
    convert figures to nearest lower or upper base value
    Args:
        value(int|float): the value to convert
        base(int): the base to use for the conversion
    Examples:
        ```
        toNearest(1_234) -> 1_200
        toNearest(1_264) -> 1_300
        toNearest(1_234, 50) -> 1_250
        toNearest(1_234_567, 1000) -> 1_235_000
        toNearest(1_234_467, 1000) -> 1_234_000
        ```
    '''

    if value%base < base/2: return toNearestLower(value,base)
    else: return toNearestUpper(value,base)

def splitNumber(number:int, interval:int=3) -> str:
    '''
    split number into groups. used for created eaiser-to-read long numbers such as account numbers
    Args:
        number(int): the number to split 
        interval(int): how many numbers to group together
    Examples:
        ```
        splitNumber(1_234_534_567) -> '123 453 456 7'
        splitNumber(1_234_534_567, 2) -> '12 34 53 45 67'
        splitNumber(1_234_534_567, 4) -> '1234 5345 67'
        ```
    '''
    n = str(number)
    _n=''
    for index,xter in enumerate(n):
        _n += xter
        if index and not (index+1)%interval:
            _n += ' '
    _n = _n.strip()

    return _n
