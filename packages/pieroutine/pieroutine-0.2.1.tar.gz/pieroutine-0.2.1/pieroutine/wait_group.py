from multiprocessing import Lock, Process, Value
from time import time
from typing import Callable


class RunType:
    PROCESS = 1
    THREAD =2  # implement functionalities for threads


class WaitGroup:
    __slots__ = ["_counter", "_lock"]
    _instance = None
    
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WaitGroup, cls).__new__(cls) 
        return cls._instance
    
    def __init__(self):
        # using the lock object we control the reading and writing 
        # on our counter in processes
        self._lock = Lock()
        
        # with multiprocessing.Value we create a shared value 
        # for sharing it between our processes
        self._counter = Value("i", 0)
        
    def add(self):
        with self._lock:
            self._counter.value += 1

    def done(self):
        with self._lock:
            if self._counter.value == 0:
                raise SystemError("the _counter cannot be zero")
            self._counter.value -= 1
    
    def wait(self):
        while self._counter.value > 1:
            ...
            
    def _process_wait_for(self, process: Process, timeout: int = 100) -> bool:
        """ 
            return True if the process getting done.
            process: multiprocessing.Process = a multiprocessing.Process object 
            timeout: int = a valid int for living process
        """
        if timeout <= 0:
            raise ValueError("invalid timeout")
        process.start()
        start_time = time()
        while process.is_alive():
            if (timeout and start_time) and (time() > start_time + timeout):
                process.kill()
                raise TimeoutError
        return True
            
    def wait_for(self, func: Callable, args, timeout: int, mode: RunType):
        match mode:
            case RunType.PROCESS:
                p = Process(target=func, args=args) 
                print("PID: ", p.pid)
                self._process_wait_for(p, timeout)
            case RunType.THREAD:
                pass
            case _:
                raise NotImplementedError(f"{mode} not implemented yet")
        