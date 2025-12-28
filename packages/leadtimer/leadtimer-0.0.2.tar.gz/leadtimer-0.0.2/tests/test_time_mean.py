from leadtimer.time_mean.time_mean import time_mean
from time import sleep

def test_time_mean():
    def heavy_task(one, two):
        sleep(0.5)
        return one, two
    
    mean = time_mean(2, heavy_task, 1, two = 2)
    assert mean != (1, 2)
    assert mean > 0 