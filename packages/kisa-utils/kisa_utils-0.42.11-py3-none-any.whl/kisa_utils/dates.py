import datetime
import time

WEEK_DAYS = {
    1:'Monday', 2:'Tuesday', 3:'Wednesday',
    4:'Thursday', 5:'Friday', 6:'Saturday',
    7: 'Sunday'
}

def weekRange(date:str|datetime.datetime) -> tuple[str,str]: # assumes standardizedDates to be given
    '''
    return a list containing the monday and sunday that belong to the week
    Args:
        date(str|datetime.datetime): the date whose week-range we need to get
    Returns:
        ```
        (monday:str, sunday:str) # each date is in format "YYYY-MM-DD"
        ```
    '''
    
    if isinstance(date,(str,bytes)):
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

    weekStart = (date - datetime.timedelta(days=date.weekday()-0)).strftime('%Y-%m-%d')
    weekEnd = (date +datetime.timedelta(days=6-date.weekday())).strftime('%Y-%m-%d')
    
    return weekStart,weekEnd

 # assumes standardizedDates to be given
def humanizeDate(date:str, includeWeekDay:bool=False) -> str:
    '''
    convert date into a human-friendly format
    Args:
        date(str): the date to humanize. its in the `YYYY-MM-DD` format
        includeWeekDay(bool): wheather or not to include the week-day
    Returns:
        `str` in format `DD MonthCode YYYY`
    Examples:
        ```
        humanizeDate('2021-09-23') -> '23 Sep 2021'
        humanizeDate('2021-09-23', True) -> 'Thu 23 Sep 2021'
        ```    
    '''
        
    if includeWeekDay:
        return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%a %d %b %Y')

    return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d %b %Y')
    
    #date = date.split('-')
    #return f'{date[2]} {MONTH_CODES[date[1]]} {date[0]}'

def dehumanizeDate(date:str) -> str:
    '''
    convert date from human-friendly format to YYYY-MM-DD
    Args:
        date(str): the humanized date to dehumanize
    Examples:
        ```
        dehumanizeDate('23 Sep 2021') -> '2021-09-23'
        dehumanizeDate('Thu 23 Sep 2021') -> '2021-09-23'
        ```    

    '''
    if 2==date.count(' '):
        return datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')

    return datetime.datetime.strptime(date, '%a %d %b %Y').strftime('%Y-%m-%d')

def daysBetweenDates(dateFrom:str, dateTo:str) -> int:  # assumes standardizedDates to be given
    '''
    get the number of days between dates, not inclusive
    Args:
        dateFrom(str): the start date in `YYYY-MM-DD` format
        dateTo(str): end date in `YYYY-MM-DD` format
    Note:
        the days are not inclusive in the count
    Examples:
        ```
        daysBetweenDates(monday, tuesday) -> 1 # both days in the same week
        ```
    '''

    return (datetime.datetime.strptime(dateTo, '%Y-%m-%d') - datetime.datetime.strptime(dateFrom, '%Y-%m-%d')).days

def daysBetweenDatesInlusive(dateFrom:str, dateTo:str) -> str:  # assumes standardizedDates to be given
    '''
    get the number of days between dates, inclusive
    Args:
        dateFrom(str): the start date in `YYYY-MM-DD` format
        dateTo(str): end date in `YYYY-MM-DD` format
    Note:
        the days are not inclusive in the count
    Examples:
        ```
        daysBetweenDatesInlusive(monday, tuesday) -> 2 # both days in the same week, monday is included in the count
        ```
    '''
    days = daysBetweenDates(dateFrom, dateTo)
    return (abs(days)+1) * (-1 if days<0 else +1)

def howLongAgo(dateFrom:str, dateTo:str, shortestVersion:bool=True) -> str:
    '''
    get a human-friendly how-long-ago eg '3 days', '1 week, 4 days', '3 months, 1 week, 6 days', etc
    Args:
        dateFrom(str): the start date in the YYYY-MM-DD format
        dateTo(str): the end date in the YYYY-MM-DD format
        shortestVersion(bool): return the shorted possible version
    Examples:
        ```
        howLongAgo('2025-01-01', '2025-05-18') -> '4 months, 2 weeks'
        howLongAgo('2025-01-01', '2025-05-18', False) -> '4 months, 2 weeks, 3 days'
        ```
    '''
    days = daysBetweenDates(dateFrom, dateTo)

    return_str = ''
    
    if days>=365:
        years = int(days/365)
        days = days%365
        return_str += f'{years} {"years" if years>1 else "year"}'
    
    if days >=30:
        months = int(days/30)
        days = days%30
        if return_str: return_str +=', '
        return_str += f'{months} {"months" if months>1 else "month"}'

    if shortestVersion and return_str.count(',')>=1:
        return return_str

    if days >=7:
        weeks = int(days/7)
        days = days%7
        if return_str: return_str +=', '
        return_str += f'{weeks} {"weeks" if weeks>1 else "week"}'

    if shortestVersion and return_str.count(',')>=1:
        return return_str
        
    if days:
        if return_str: return_str +=', '
        return_str += f'{days} {"days" if days>1 else "day"}'
        
    return return_str

def currentTimestamp() -> str:
    '''
    get current timestamp in EAT
    Returns:
        string in format `YYYY-MM-DD HH:MM:SS`
    '''
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=3.00)
    return str(now)[:19]

def dateFrom(date:str, days:int, hours:int=0) -> str:
    '''
    get the date thats `days` + `hours` from `date`
    Args:
        date(str): the reference date to use format is `YYYY-MM-DD`
        days(int): days from the reference date
        hours(int): hours to include to the days to ge tthe new date
    Examples:
        ```
        dateFrom('2025-06-18', 1) -> '2025-06-19'
        dateFrom('2025-01-01', -2) -> '2024-12-30'
        ```
    '''
    _date = datetime.datetime.strptime(date, '%Y-%m-%d')
    return str(_date + datetime.timedelta(days=days, hours=hours))[:10]

def TimeFrom(timestamp:str, days:int=0, hours:int=0, minutes:int=0, seconds:int=0) -> str:
    '''
    get the time thats `days` + `hours` + `minutes` + `seconds` from `timestamp`
    Args:
        timestamp(str): the reference timestamp to use, format is `YYYY-MM-DD HH:MM:SS`
        days(int): days from the reference timestamp
        hours(int): hours to include to the days to ge tthe new date
        minutes(int): minutes to include to the days to ge the new date
        seconds(int): seconds to include to the days to ge the new date
        ```
    '''
    _tstamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return str(_tstamp + datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds))

def dateFromNow(days=0,hours=0) -> str:
    '''
    get the timestamp(not date) thats `days` + `hours` from the current time
    Args:
        days(int): days from the reference date
        hours(int): hours to include to the days to ge tthe new date
    Examples:
        ```
        # assuming the current time is '2025-06-18 10:53:54'
        dateFromNow(1) -> '2025-06-19 10:53:54'
        dateFromNow(-2) -> '2025-06-16 10:53:54'
        ```
    '''
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=3.00)
    return str(now+datetime.timedelta(days=days, hours=hours))[:19]

def TimeFromNow(days:int=0, hours:int=0, minutes:int=0, seconds:int=0) -> str:
    '''
    get the time thats `days` + `hours` + `minutes` + `seconds` from `timestamp`
    Args:
        days(int): days from the reference timestamp
        hours(int): hours to include to the days to ge tthe new date
        minutes(int): minutes to include to the days to ge the new date
        seconds(int): seconds to include to the days to ge the new date
        ```
    '''
    timestamp = currentTimestamp()
    return TimeFrom(timestamp, days, hours, minutes, seconds)


# thanks to airtel & MTN strange date formats, we have this
def standardizedDate(date:str, fmt:str=''):
    '''
    standardize date/timestamp into the `YYYY-MM-DD HH:MM:SS` standard
    Args:
        date(str): the date to standardize
        fmt(str): the format in which the date/timestamp is currently in
    Note:
        Supported formats;
        - DD-MM-YYYY HH:MM:SS
        - MM-DD-YYYY HH:MM:SS
        
        - DD-MM-YYYY HH:MM:SS AM
        - MM-DD-YYYY HH:MM:SS AM

        - DD-MM-YYYY HH:MM
        - MM-DD-YYYY HH:MM
        
        - DD-MM-YYYY HH:MM AM
        - MM-DD-YYYY HH:MM AM
        
        - YYYY-MM-DD
        - DD-MM-YYYY
        - MM-DD-YYYY
        
        - YYYY-MM-DD HH:MM:SS
        - YYYY-MM-DD HH:MM:SS AM

        - YYYY-MM-DD HH:MM
        - YYYY-MM-DD HH:MM AM
    '''
    _date = None

    date = date.replace('/','-').replace('"','').replace("'",'')
    date = '-'.join([(_ if len(_)>1 else f'0{_}') for _ in date.split('-')])

    if len(date)<len('YYYY-MM-DD'): raise ValueError('invalid date given')
    if not fmt: raise ValueError('no format given')

    fmt:str|None = fmt.upper().replace('PM','AM')

    fmt = {
        'DD-MM-YYYY HH:MM:SS':'%d-%m-%Y %H:%M:%S',
        'MM-DD-YYYY HH:MM:SS':'%m-%d-%Y %H:%M:%S',
        
        'DD-MM-YYYY HH:MM:SS AM':'%d-%m-%Y %I:%M:%S %p',
        'MM-DD-YYYY HH:MM:SS AM':'%m-%d-%Y %I:%M:%S %p',

        'DD-MM-YYYY HH:MM':'%d-%m-%Y %H:%M',
        'MM-DD-YYYY HH:MM':'%m-%d-%Y %H:%M',
        
        'DD-MM-YYYY HH:MM AM':'%d-%m-%Y %I:%M %p',
        'MM-DD-YYYY HH:MM AM':'%m-%d-%Y %I:%M %p',
        
        'YYYY-MM-DD':'%Y-%m-%d',
        'DD-MM-YYYY':'%d-%m-%Y',
        'MM-DD-YYYY':'%m-%d-%Y',
        
        'YYYY-MM-DD HH:MM:SS':'%Y-%m-%d %H:%M:%S',
        'YYYY-MM-DD HH:MM:SS AM':'%Y-%m-%d %I:%M:%S %p',

        'YYYY-MM-DD HH:MM':'%Y-%m-%d %H:%M',
        'YYYY-MM-DD HH:MM AM':'%Y-%m-%d %I:%M %p',
    }.get(fmt,None)

    if not fmt: raise ValueError('unknown date format given')

    try:
        _date = datetime.datetime.strptime(date, fmt)
    except:
        raise ValueError('failed to format date to standard time')
    return str(_date)
# -----------------------------------------------------------------
def _testStandardizeTime():
    for date,fmt in [
        ('10/7/2022 19:31:30','DD-MM-YYYY HH:MM:SS'),
        ('7/10/2022 19:31:30','MM-DD-YYYY HH:MM:SS'),
        ('10/7/2022 07:31:30 pm','DD-MM-YYYY HH:MM:SS AM'),
        ('7/10/2022 07:31:30 pm','MM-DD-YYYY HH:MM:SS AM'),
        ('10/7/2022 19:31','DD-MM-YYYY HH:MM'),
        ('7/10/2022 19:31','MM-DD-YYYY HH:MM'),
        ('10/7/2022 07:31 pm','DD-MM-YYYY HH:MM AM'),
        ('7/10/2022 07:31 pm','MM-DD-YYYY HH:MM AM'),
        ('2022-7-10','YYYY-MM-DD'),
        ('10-07-2022','DD-MM-YYYY'),
        ('07-10-2022','MM-DD-YYYY'),
        ('2022-7-10 19:3:30','YYYY-MM-DD HH:MM:SS'),
        ('2022-7-10 7:31:30 pm','YYYY-MM-DD HH:MM:SS AM'),
        ('2022-7-10 19:31','YYYY-MM-DD HH:MM'),
        ('2022-7-10 7:31 pm','YYYY-MM-DD HH:MM AM'),

    ]:
        print(date,'->',standardizedDate(date,fmt))

def lastWeekOn(day:int, humanize:bool=False) -> str:
    '''
    get the date(YYYY-MM-DD) on `day`, last week
    Args:
        day(int): the week day; Mon=1, Tue=2, ..., Sun=7
        humanize(bool): humanize the date
    Examples:
        ```
        # assuming the current date is '2025-06-18'
        lastWeekOn(3) -> '2025-06-11'
        lastWeekOn(3, True) -> '11 Jun 2025'
        ```
    '''
    assert isinstance(day,int) and 1<=day<=7

    now = datetime.datetime.utcnow()+datetime.timedelta(hours=+3)
    today = now.weekday() + 1

    date = now + datetime.timedelta(days=-(today-day)-7)
    strDate = f'{date}'[:10]

    if humanize:
        return humanizeDate(strDate)
    return strDate

def secondsSinceEpoch()->int:
    '''get the seconds since epoch'''
    return int(time.time())

def minutesSinceEpoch()->int:
    '''get minutes since epoch'''
    return secondsSinceEpoch() // 60

def today() -> str:
    '''get current date in YYYY-MM-DD format'''
    return currentTimestamp()[:10]

def tomorrow() -> str:
    '''get tomorrow's date in YYYY-MM-DD format'''
    return dateFromNow(days=+1)[:10]

def yesterday() -> str:
    '''get yesterday's date in YYYY-MM-DD format'''
    return dateFromNow(days=-1)[:10]

def endOfMonth(year:str|int, month:str|int) -> str:
    '''
    get the last date(YYYY-MM-DD) of the given month
    Args:
        year(str|int): 4 characters representing the year
        month(str|int): 1|2 characters representing the month
    Examples:
        ```
        endOfMonth(2025, 6) -> '2025-06-30'
        endOfMonth(2025, 2) -> '2025-02-28'
        ```
    '''

    year = f'{year}'
    month = f'{month}'

    if not(year.isdigit() and month.isdigit()) or 4!=len(year) or len(month)>2:
        raise ValueError('invalid year or month given')

    if 1==len(month): month = f'0{month}'

    if not 1<=int(month)<=12:
        raise ValueError('invalid month given')

    lastDay = f'{year}-{month}-28'
    nextDay = dateFrom(lastDay, days=+1)

    while nextDay[:7] == lastDay[:7]:
        lastDay = nextDay
        nextDay = dateFrom(lastDay, days=+1)

    return lastDay

def endOfCurrentMonth() -> str:
    '''
    get last date(YYYY-MM-DD) of the current month
    '''

    dateToday = today()

    year, month, day = dateToday.split('-')
    return endOfMonth(year, month)

def dateIsValid(date:str, dateFormat:str='YYYY-MM-DD') -> bool:
    '''
    check if a date is valid in the provided format
    Args:
        date(str): the date to check
        dateFormat(str): the date format for which to check the date. common formats are;
            - 'YYYY-MM-DD'
            - 'YYYY-MM-DD HH:MM:SS'
    '''
    try:
        standardizedDate(date, dateFormat)
    except:
        return False
    
    return True

def isWeekend(date:str) -> bool:
    '''
    check if `date` is in a weekend (Saturday or Sunday)
    Args:
        date(str): the date to check
    '''
    return humanizeDate(date, includeWeekDay=True).split(' ')[0] in ['Sat','Sun']

def isSunday(date:str) -> bool:
    '''
    check if `date` is a Sunday
    Args:
        date(str): the date to check
    '''
    return humanizeDate(date, includeWeekDay=True).split(' ')[0] in ['Sun']

def isSaturday(date:str) -> bool:
    '''
    check if `date` is a Saturday
    Args:
        date(str): the date to check
    '''
    return humanizeDate(date, includeWeekDay=True).split(' ')[0] in ['Sat']

if __name__=='__main__':
    print(lastWeekOn(3, humanize=True))