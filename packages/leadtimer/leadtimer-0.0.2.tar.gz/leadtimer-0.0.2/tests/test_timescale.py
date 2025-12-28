from leadtimer.timescale.timescale import timescale
from time import sleep

def test_timescale():
    @timescale
    def slow_task(): 
        sleep(0.5)
        return True

    assert slow_task() == True