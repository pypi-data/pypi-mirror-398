import time as new_time
from datetime import datetime, time, timedelta, timezone
from loguru import logger

yymmdd = '%Y-%m-%d'
yymmdd_hhmm = '%Y-%m-%d %H:%M'
yymmdd_hhmmss = '%Y-%m-%d %H:%M:%S'
yymmdd_hhmmss_long = '%Y%m%d%H%M%S'
yymm = '%Y%m'
yy = '%Y'
yyweek = '%Y%W'

morning_start = time(9, 30, 0)
morning_end = time(11, 30, 0)
afternoon_start = time(13, 0, 0)
afternoon_end = time(15, 0, 0)

def get_day_year(_datetime : datetime=None):
    '''
    @param: datetime类型
    获取日期是一年中的第几天
    '''
    try:
        # 获取当前日期
        today = datetime.today()
        if _datetime is not None:
            today = _datetime
        # 获取当前日期是一年中的第几天
        year = today.timetuple().tm_year
        mon = today.timetuple().tm_mon
        day_of_year = today.timetuple().tm_yday
        return year, mon, day_of_year
    except Exception as e:
        logger.error(f'【date_util.get_day_year】异常, - {str(e)}')

def get_week_year(_datetime : datetime=None):
    '''
    @param: datetime类型
    获取日期是一年中的第几周
    '''
    try:
        # 获取当前日期
        today = datetime.today()
        if _datetime is not None:
            today = _datetime
        # 获取当前日期是一年中的第几周
        # today = datetime.date.today()
        # 使用isocalendar()方法获取年、周数和周内日期
        isocalendar = today.isocalendar()
        # year_week 是一个包含三个元素的元组：年、周数、周内日期
        return isocalendar.year, isocalendar.week
    except Exception as e:
        logger.error(f'【date_util.get_week_year】异常, - {str(e)}')

def get_week_year_by_timestamp(timestamp: int=datetime.now().timestamp()):
    if len(str(timestamp)) == 13:
        timestamp = timestamp / 1000
    _date = datetime.fromtimestamp(timestamp)
    return get_week_year(_date)

def get_mon_year(_datetime : datetime=None):
    '''
    @param: datetime类型
    获取日期是一年中的第几月
    '''
    try:
        # 获取当前日期
        today = datetime.today()
        if _datetime is not None:
            today = _datetime
        return today.year, today.month
    except Exception as e:
        logger.error(f'【date_util.get_week_year】异常, - {str(e)}')

def get_mon_year_by_timestamp(timestamp : int=datetime.now().timestamp()):
    '''
    @param: datetime类型
    获取日期是一年中的第几月
    '''
    if len(str(timestamp)) == 13:
        timestamp = timestamp / 1000
    _date = datetime.fromtimestamp(timestamp)
    return get_mon_year(_date)

def get_timezone_utc_timestamp_ms():
    '''
    获取utc时区时间戳数据
    '''
    utc_now = datetime.now(timezone.utc)
    utc_now = datetime(utc_now.year, utc_now.month, utc_now.day, utc_now.hour, utc_now.minute, utc_now.second, utc_now.microsecond)
    return int(utc_now.timestamp()) * 1000

def get_time_zone_diff():
    '''
    获取与utc的时区差值
    '''
    utc_now = datetime.now(timezone.utc)
    now = datetime.now()
    utc_now = datetime(utc_now.year, utc_now.month, utc_now.day, utc_now.hour, utc_now.minute, utc_now.second, utc_now.microsecond)
    now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)
    diff = int(now.timestamp() - utc_now.timestamp())
    return diff

def get_time_zone_diff_ms():
    
    return get_time_zone_diff() * 1000

def day2str(day, format_str='%Y-%m-%d'):
    return datetime.strftime(day, format_str)


def str2day(day_str, format_str='%Y-%m-%d'):
    return datetime.strptime(day_str, format_str)


def str2timestampe(day_str, format_str='%Y-%m-%d %H:%M:%S'):
    dateTime = new_time.strptime(day_str, format_str)
    timestampe = new_time.mktime(dateTime)
    return int(timestampe)


def time2date(time_float):
    time_float = int(time_float)
    return str2day(str(time_float), yymmdd_hhmmss)


def date2time(date):
    return float(day2str(date, yymmdd_hhmmss_long) + '000')


def get_detail_time(_datetime=datetime.today(), hour=0, minute=0, second=0):
    # 获取任意时刻的时间戳
    today_0 = _datetime - timedelta(hours=_datetime.hour, minutes=_datetime.minute, seconds=_datetime.second)
    today_anytime = today_0 + timedelta(hours=hour, minutes=minute, seconds=second)
    # tsp = today_anytime.timestamp()
    # print('{}  的时间戳是  {}'.format(today_anytime, tsp))
    return today_anytime


def get_datestr_start(date):
    timestampe = str2timestampe(date, yymmdd)
    start_date = datetime.fromtimestamp(timestampe)
    ago = get_detail_time(start_date, 0, 0)
    return int(ago.timestamp())


def get_before_now(now, days=0, seconds=0, minutes=0, hours=0, format=yymmdd_hhmmss):
    # 当前时间往前推30天
    ago = now - timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours)
    return ago.strftime(format)


def get_aftertime(n:int=0):  # 精确到分钟
    """
    获取当前时间往后的时间
    :param n: 当前时间后的n分钟
    :return: 返回当前时间后的时间，精确当分钟
    """
    nowtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 获取当前时间
    # 将当前时间转换为时间数组
    timeArray1= new_time.strptime(nowtime, "%Y-%m-%d %H:%M:%S")
    print(timeArray1)
    # 将时间转换为时间戳:
    timeStamp = int(new_time.mktime(timeArray1))
    print(timeStamp)
    # 在原来时间戳的基础上加n*60
    timeStamp += (n * 60)
    print(timeStamp)
    # 把timestamp处理之后转换为时间数组，格式化为需要的格式
    timeArray2 = new_time.localtime(timeStamp)
    print(timeArray2)
    aftertime = new_time.strftime("%Y-%m-%d %H:%M", timeArray2)
    print(aftertime)
    new_date = (datetime(timeArray2.tm_year, timeArray2.tm_mon, timeArray2.tm_mday, timeArray2.tm_hour, timeArray2.tm_min))
    return new_date, aftertime

def get_current_hour_minutes_time(current_time, hour, minutes):
    '''
    获取之前的时间
    '''
    creation = datetime(current_time.year, current_time.month, current_time.day, hour, minutes)  # 2023年3月15日 12:00
    return creation

def get_before_date(days=0, seconds=0, minutes=0, hours=0, format=yymmdd_hhmmss):
    now = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp())
    # 当前时间往前推30天
    ago = now - timedelta(days=days, seconds=seconds, minutes=minutes, hours=hours)
    return ago.strftime(format)

def get_before_date_start(days :int=0, format=yymmdd_hhmmss):
    '''
    获取当天开始时间,也就是凌晨时间0点
    '''
    machine_now = datetime.now(timezone.utc).timestamp()
    now = datetime.fromtimestamp(machine_now)
    
    ago = now - timedelta(days=days)
    ago = get_detail_time(ago, 0, 0)
    return ago.strftime(format)

if __name__ == '__main__':
    get_week_year_by_timestamp(datetime.now().timestamp())
    get_detail_time()
    get_week_year()
