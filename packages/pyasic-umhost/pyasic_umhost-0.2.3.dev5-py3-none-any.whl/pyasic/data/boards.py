# ------------------------------------------------------------------------------
#  Copyright 2022 Upstream Data Inc                                            -
#                                                                              -
#  Licensed under the Apache License, Version 2.0 (the "License");             -
#  you may not use this file except in compliance with the License.            -
#  You may obtain a copy of the License at                                     -
#                                                                              -
#      http://www.apache.org/licenses/LICENSE-2.0                              -
#                                                                              -
#  Unless required by applicable law or agreed to in writing, software         -
#  distributed under the License is distributed on an "AS IS" BASIS,           -
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    -
#  See the License for the specific language governing permissions and         -
#  limitations under the License.                                              -
# ------------------------------------------------------------------------------
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from pyasic.device.algorithm.hashrate import AlgoHashRateType


class HashBoard(BaseModel):
    """Унификация данных платы.

    Атрибуты:
        slot: Номер слота.
        hashrate: Хешрейт платы в H/s (число).
        inlet_temp: Температура на входе (гидро ASIC), °C.
        outlet_temp: Температура на выходе (гидро ASIC), °C.
        temp: Температура PCB, °C.
        chip_temp: Температура чипов, °C.
        chips: Кол-во чипов.
        expected_chips: Ожидаемое кол-во чипов.
        serial_number: Серийный номер платы.
        missing: Плата отсутствует в данных.
        tuned: Плата протюнена.
        active: Плата сейчас тюнится.
        voltage: Входное напряжение платы.
    """

    slot: int = 0
    hashrate: AlgoHashRateType | None = None
    inlet_temp: float | None = None
    outlet_temp: float | None = None
    temp: float | None = None
    chip_temp: float | None = None
    chips: int | None = None
    expected_chips: int | None = None
    serial_number: str | None = None
    missing: bool = True
    tuned: bool | None = None
    active: bool | None = None
    voltage: float | None = None

    @classmethod
    def fields(cls) -> set:
        all_fields = set(cls.model_fields.keys())
        all_fields.update(set(cls.model_computed_fields.keys()))
        return all_fields

    def get(self, __key: str, default: Any = None):
        try:
            val = self.__getitem__(__key)
            if val is None:
                return default
            return val
        except KeyError:
            return default

    def __getitem__(self, item: str):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(f"{item}")

    def as_influxdb(self, key_root: str, level_delimiter: str = ".") -> str:
        def serialize_int(key: str, value: int) -> str:
            return f"{key}={value}"

        def serialize_float(key: str, value: float) -> str:
            return f"{key}={value}"

        def serialize_str(key: str, value: str) -> str:
            return f'{key}="{value}"'

        def serialize_algo_hash_rate(key: str, value: AlgoHashRateType) -> str:
            # Уже H/s, записываем числом
            return f"{key}={round(float(value), 2)}"

        def serialize_bool(key: str, value: bool) -> str:
            return f"{key}={str(value).lower()}"

        serialization_map_instance = {
            AlgoHashRateType: serialize_algo_hash_rate,
        }
        serialization_map = {
            int: serialize_int,
            float: serialize_float,
            str: serialize_str,
            bool: serialize_bool,
        }

        include = [
            "hashrate",
            "temp",
            "chip_temp",
            "chips",
            "expected_chips",
            "tuned",
            "active",
            "voltage",
        ]

        field_data = []
        for field in include:
            field_val = getattr(self, field)
            serialization_func: Callable[[str, Any], str | None] = (
                serialization_map.get(
                    type(field_val),
                    lambda _k, _v: None,  # type: ignore
                )
            )
            serialized = serialization_func(
                f"{key_root}{level_delimiter}{field}", field_val
            )
            if serialized is not None:
                field_data.append(serialized)
                continue
            for datatype in serialization_map_instance:
                if serialized is None:
                    if isinstance(field_val, datatype):
                        serialized = serialization_map_instance[datatype](
                            f"{key_root}{level_delimiter}{field}", field_val
                        )
            if serialized is not None:
                field_data.append(serialized)
        return ",".join(field_data)
