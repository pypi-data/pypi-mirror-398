import time 

def time_mean(count_start, fnc, *args, **kwargs):
    time_start = time.time()
    for i in range(count_start):
        fnc(*args, **kwargs)
    time_std = time.time() - time_start
    krugmean = time_std / count_start
    return krugmean
#time_mean(10)