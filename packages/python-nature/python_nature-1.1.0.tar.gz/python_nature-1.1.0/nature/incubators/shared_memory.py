import pickle
import struct
import multiprocessing.shared_memory as sm


class SharedMemoryObject:
    def __init__(self, name: str | None = None, capacity: int = 1024):
        """Create or attach to shared memory."""
        if name:
            self.shm: sm.SharedMemory = sm.SharedMemory(name=name)
        else:
            self.shm: sm.SharedMemory = sm.SharedMemory(create=True, size=capacity)
        self.size_struct = struct.Struct("Q")  # 8-byte unsigned long long for size

    def write(self, obj):
        """Serialize and write an object to shared memory."""
        data = pickle.dumps(obj)
        size = len(data)
        if size + 8 > self.shm.size:
            raise ValueError("Object too large for shared memory")
        self.shm.buf[:8] = self.size_struct.pack(size)
        self.shm.buf[8 : 8 + size] = data

    def read(self):
        """Read and deserialize an object from shared memory."""
        size = self.size_struct.unpack(self.shm.buf[:8])[0]
        return pickle.loads(self.shm.buf[8 : 8 + size])

    def close(self):
        """Close shared memory."""
        self.shm.close()

    def unlink(self):
        """Unlink shared memory (only needed for creator)."""
        self.shm.unlink()

    @property
    def name(self):
        """Get the shared memory name."""
        return self.shm.name
