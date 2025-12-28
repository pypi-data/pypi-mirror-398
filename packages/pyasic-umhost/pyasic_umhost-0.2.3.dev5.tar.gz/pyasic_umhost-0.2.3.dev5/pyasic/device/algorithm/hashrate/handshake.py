from __future__ import annotations
from typing_extensions import Self

from pyasic.device.algorithm.hashrate.base import AlgoHashRateType


class HandshakeHashRate(AlgoHashRateType):
    rate: float

    def into(self, _other=None) -> Self:
        return self.__class__(rate=self.rate)
