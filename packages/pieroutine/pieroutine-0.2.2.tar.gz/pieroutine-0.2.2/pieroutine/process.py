from multiprocessing import Pool, cpu_count, Process, Queue
from typing import Any, Callable

from pieroutine.wait_group import WaitGroup


class ProcessConcurrent:
    __slots__ = ["f", "arguments", "process_count"]
    
    def __init__(self, func: Callable, arguments: list):
        self.f = func 
        self.arguments = arguments
        arguments_length = len(arguments)
        cc = cpu_count()
        self.process_count = cc - 1 if arguments_length >= cc else arguments_length
        
    def run_pool(self):
        with Pool(processes=self.process_count) as pool:
            return pool.map(self.f, self.arguments)
        
    def process_worker(
        self, 
        arg: Any, 
        wait_group: WaitGroup, 
        queue: Queue = None,
        auto_done: bool = False
    ):
        wait_group.add()
        kwargs = {}
        if not auto_done:
            kwargs["wait_group"] = wait_group
            
        try:
            if res := self.f(*arg, **kwargs) and queue is not None:
                queue.put_nowait(res)
        finally:
            if auto_done:
                wait_group.done()
    
    def run_process(
        self, 
        wait_group: WaitGroup, 
        queue: Queue = None,
        auto_done: bool = False
    ):
        [
            Process(target=self.process_worker, args=(arg, wait_group, queue, auto_done)).start()
            for arg in self.arguments
        ]