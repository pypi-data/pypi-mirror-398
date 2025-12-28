import time
import hashlib


def generate_hash_id(_series, time_salt=False):
    now = time.localtime()
    salt = str(now.tm_year) + ' ' + str(now.tm_mon) + ' ' + str(now.tm_mday) + ' ' + str(now.tm_hour)
    sss = [str(_series.iloc[i]) for i in range(len(_series))]
    if time_salt:
        str_values = " ".join(sss) + ' ' + salt
    else:
        str_values = " ".join(sss)

    return hashlib.sha3_256(str_values.encode('utf-8')).hexdigest()

def row_hash_id(_series, time_salt=False):
    now = time.localtime()
    salt = str(now.tm_year) + ' ' + str(now.tm_mon) + ' ' + str(now.tm_mday) + ' ' + str(now.tm_hour)
    sss = [str(_series.iloc[i]) for i in range(len(_series))]
    if time_salt:
        str_values = " ".join(sss) + ' ' + salt
    else:
        str_values = " ".join(sss)

    return hashlib.sha3_256(str_values.encode('utf-8')).hexdigest()

def dict_hash_id(_dict:dict, time_salt=False):
    now = time.localtime()
    salt = str(now.tm_year) + ' ' + str(now.tm_mon) + ' ' + str(now.tm_mday) + ' ' + str(now.tm_hour)
    sss = [f'{key}: {value}' for key, value in _dict.items()]
    if time_salt:
        str_values = " ".join(sss) + ' ' + salt
    else:
        str_values = " ".join(sss)

    return hashlib.sha3_256(str_values.encode('utf-8')).hexdigest()

def array_hash_id(_array, time_salt=False):
    now = time.localtime()
    salt = str(now.tm_year) + ' ' + str(now.tm_mon) + ' ' + str(now.tm_mday) + ' ' + str(now.tm_hour)
    sss = [str(i) for i in _array]
    if time_salt:
        str_values = " ".join(sss) + ' ' + salt
    else:
        str_values = " ".join(sss)

    return hashlib.sha3_256(str_values.encode('utf-8')).hexdigest()

