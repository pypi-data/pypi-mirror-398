from multiprocessing import Process

from nature.random import Random


class Worker(Process):
    def __init__(self, **process_kwargs) -> None:
        process_kwargs.setdefault("daemon", True)
        super().__init__(**process_kwargs)
        self.random = Random()
