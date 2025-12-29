from _hashlib import HASH
from io import BufferedWriter
from typing import BinaryIO

from typing_extensions import Buffer


class HashWriter(BinaryIO):
    def __init__(self, rawWriter: BufferedWriter, hashWriter: HASH):
        self.rawWriter = rawWriter
        self.hashWriter = hashWriter

    def write(self, data: Buffer):
        self.hashWriter.update(data)
        return self.rawWriter.write(data)

    def flush(self):
        return self.rawWriter.flush()

    def close(self):
        return self.rawWriter.close()

    def writable(self):
        return True
