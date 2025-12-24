import threading
import time
from datetime import datetime, timezone

from nlbone.config.settings import get_settings


class Snowflake:
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5
    SEQUENCE_BITS = 12

    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1  # 31
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1  # 31
    SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1  # 4095

    WORKER_ID_SHIFT = SEQUENCE_BITS
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    EPOCH = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    def __init__(self, datacenter_id: int, worker_id: int):
        if not (0 <= worker_id <= self.MAX_WORKER_ID):
            raise ValueError(f"worker_id must be 0..{self.MAX_WORKER_ID}")
        if not (0 <= datacenter_id <= self.MAX_DATACENTER_ID):
            raise ValueError(f"datacenter_id must be 0..{self.MAX_DATACENTER_ID}")

        self.datacenter_id = datacenter_id
        self.worker_id = worker_id
        self.sequence = 0
        self.last_ts = -1
        self._lock = threading.Lock()

    @staticmethod
    def _timestamp_ms() -> int:
        return int(time.time() * 1000)

    def _wait_next_ms(self, last_ts: int) -> int:
        ts = self._timestamp_ms()
        while ts <= last_ts:
            ts = self._timestamp_ms()
        return ts

    def next_id(self) -> int:
        with self._lock:
            ts = self._timestamp_ms()

            if ts < self.last_ts:
                ts = self._wait_next_ms(self.last_ts)

            if ts == self.last_ts:
                self.sequence = (self.sequence + 1) & self.SEQUENCE_MASK
                if self.sequence == 0:
                    ts = self._wait_next_ms(self.last_ts)
            else:
                self.sequence = 0

            self.last_ts = ts

            id64 = (
                ((ts - self.EPOCH) << self.TIMESTAMP_SHIFT)
                | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
                | (self.worker_id << self.WORKER_ID_SHIFT)
                | self.sequence
            )
            return id64


setting = get_settings()
_DC_ID = int(setting.SNOWFLAKE_DATACENTER_ID)
_WORKER_ID = int(setting.SNOWFLAKE_WORKER_ID)
SNOWFLAKE = Snowflake(datacenter_id=_DC_ID, worker_id=_WORKER_ID)
