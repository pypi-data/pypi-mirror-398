from _typeshed import Incomplete

DATA_FORMAT: str
DATA_FORMAT_SIZE: Incomplete

class Channel:
    name: Incomplete
    lock: Incomplete
    shared_memory_size: Incomplete
    shm: Incomplete
    write_pos: Incomplete
    read_pos: Incomplete
    queue_number: Incomplete
    max_queue_number: Incomplete
    def __init__(self, name, create: bool = False, shared_memory_size: int = 104857600, max_queue_number: int = 5) -> None: ...
    def write_data(self, data, timeout: float = 600.0): ...
    def read_data(self): ...
    def close(self) -> None: ...
