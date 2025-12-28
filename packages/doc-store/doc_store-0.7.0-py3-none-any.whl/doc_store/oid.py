import itertools
import os
import random
import threading
import time
import uuid

"""
# oid generator

algorithm from mongodb. (modified a little)

oid has 12 bytes.

```
 (mongo) |   4-bytes |   3-bytes  |   2-bytes  | 3-bytes |
oid ====   timestamp + machine_id + process_id + seq_id

 timestamp: the seconds start from unix epoch
machine_id: generated from machine network mac address
process_id: generated from process id
    seq_id: counter value that start from a random number
```
"""


_enc_chars = sorted("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
_enc_char_indices = {c: i for i, c in enumerate(_enc_chars)}


def _encode_int(v: int, byte_len: int) -> str:
    bits = v
    bit_len = byte_len * 8
    res = []
    while bit_len >= 6:
        bit_len -= 6
        idx = (bits >> bit_len) & 0x3F
        res.append(_enc_chars[idx])
    if bit_len > 0:
        idx = (bits << (6 - bit_len)) & 0x3F
        res.append(_enc_chars[idx])
    return "".join(res)


def _decode_int(s: str, byte_len: int) -> int:
    bits = 0
    bit_len = 0
    for c in s:
        idx = _enc_char_indices[c]
        bits = (bits << 6) | idx
        bit_len += 6
    if bit_len > byte_len * 8:
        bits = bits >> (bit_len - byte_len * 8)
    return bits


class OidGenerator:
    def __init__(self):
        self.mac = uuid.getnode() & 0xFFFFFF
        self.pid = os.getpid() & 0xFFFF
        seq_start = random.randint(0, 0xFFFFFF)
        self.seq_iter = itertools.count(seq_start)
        self.seq_lock = threading.Lock()

    def get(self, time_offset: int = 0) -> str:
        ts = int((time.time() + time_offset))
        with self.seq_lock:
            seq = next(self.seq_iter) & 0xFFFFFF
        id = (ts << 64) + (self.mac << 40) + (self.pid << 24) + seq
        return _encode_int(id, 12)


default_generator = OidGenerator()


def oid(time_offset: int = 0) -> str:
    return default_generator.get(time_offset)


def is_oid(id: str):
    # fmt: off
    return (
        isinstance(id, str)
        and len(id) == 16
        and all(c in _enc_char_indices for c in id)
    )
    # fmt: on


def oid_int(id: str) -> int:
    return _decode_int(id, 12) if is_oid(id) else 0


def oid_time(id) -> int:
    id_int = oid_int(id)
    return (id_int >> 64) & 0xFFFFFFFF
