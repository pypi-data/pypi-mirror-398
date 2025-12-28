import time 

def measure(fnc):
    def inner(*args, **kwargs):
        start_time = time.time()
        a = fnc(*args, **kwargs)  
        std_time = time.time() - start_time    
        print(std_time)
        return a 
    


    return inner
