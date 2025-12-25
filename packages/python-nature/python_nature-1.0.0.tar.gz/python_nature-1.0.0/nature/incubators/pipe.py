import multiprocessing as mp
import pickle
from typing import Any


class Pipe:
    def __init__(self) -> None:
        self.receiver_conn, self.sender_conn = mp.Pipe()

    def send(self, obj: object) -> None:
        self.sender_conn.send(pickle.dumps(obj))

    def recv(self) -> Any | None:
        data = None
        while self.receiver_conn.poll():
            data = self.receiver_conn.recv()
        return pickle.loads(data) if data else None
