from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, model_serializer, model_validator
from typing_extensions import Self

Number = Union[int, float]


_UNIT_KEYS = ("H", "KH", "MH", "GH", "TH", "PH", "EH", "ZH")

def _extract_multiplier_from_unit(unit: Any) -> float | None:
    """
    Пытаемся получить множитель единицы измерения:
    - Если это Enum/объект с .value (как раньше) — берём unit.value.
    - Если это dict (после сериализации старых Unit-моделей) — ищем:
        * прямой ключ "value";
        * либо "default" с вложенным "value";
        * либо ключи из _UNIT_KEYS (берём значение "H" как 1 и делаем относительный коэффициент,
          но чаще в старых моделях .value уже содержит множитель).
    Возвращаем None, если не получилось определить множитель.
    """
    # Вариант 1: Enum/объект с .value
    try:
        v = getattr(unit, "value", None)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    except Exception:
        pass

    # Вариант 2: dict-представление
    if isinstance(unit, dict):
        # Прямой value
        v = unit.get("value")
        if isinstance(v, (int, float)) and v > 0:
            return float(v)

        # value внутри default
        default = unit.get("default")
        if isinstance(default, dict):
            v = default.get("value")
            if isinstance(v, (int, float)) and v > 0:
                return float(v)

        # Фоллбэк: если есть набор ключей-единиц, пробуем взять "H" как 1
        # (обычно старые модели уже давали .value, так что сюда редко попадём)
        has_any = any(k in unit for k in _UNIT_KEYS)
        if has_any:
            # Если явно указан текущий юнит, но без .value — распознать сложно.
            # В таких структурах обычно есть поле "current" или "default".
            # Попробуем "current" -> {'name': 'GH', 'value': 1_000_000_000}, и т.п.
            current = unit.get("current") or unit.get("default")
            if isinstance(current, dict):
                v = current.get("value")
                if isinstance(v, (int, float)) and v > 0:
                    return float(v)

    return None


class AlgoHashRateType(BaseModel):
    """
    Упрощённый тип хешрейта:
    - всегда хранит значение в H/s;
    - сериализуется как число (без единиц);
    - если при создании передан старый `unit`, нормализуем rate в H/s и убираем unit;
    - арифметика поддерживается; деление возвращает число-отношение.
    """

    rate: float
    # Принимаем старое поле, чтобы корректно мигрировать данные.
    unit: Any | None = None

    # Нормализация входных данных: если передан unit, домножаем rate на его множитель.
    @model_validator(mode="before")
    @classmethod
    def _normalize_to_hs(cls, data: Any):
        # data может быть уже экземпляром, dict-ом или чем-то совместимым
        if isinstance(data, dict):
            rate = data.get("rate")
            unit = data.get("unit", None)
            if rate is not None and unit is not None:
                mult = _extract_multiplier_from_unit(unit)
                if mult and isinstance(rate, (int, float)):
                    data = dict(data)  # не мутируем исходный
                    data["rate"] = float(rate) * float(mult)
                    data["unit"] = None
        return data

    # Сериализация в число при dump/json
    @model_serializer(mode="plain")
    def _serialize(self):
        return self.rate

    # Числовая семантика
    def __float__(self):
        return float(self.rate)

    def __int__(self):
        return int(self.rate)

    def __repr__(self):
        # Без единиц — только число в H/s
        return f"{self.rate}"

    def __round__(self, n: int | None = None):
        return round(self.rate, n)

    # Арифметика
    def __add__(self, other: Self | Number) -> Self:
        if isinstance(other, AlgoHashRateType):
            return self.__class__(rate=self.rate + other.rate)
        return self.__class__(rate=self.rate + float(other))

    # Поддержка sum(..., start=0)
    def __radd__(self, other: Number) -> Self:
        return self.__add__(other)

    def __sub__(self, other: Self | Number) -> Self:
        if isinstance(other, AlgoHashRateType):
            return self.__class__(rate=self.rate - other.rate)
        return self.__class__(rate=self.rate - float(other))

    def __truediv__(self, other: Self | Number) -> float:
        if isinstance(other, AlgoHashRateType):
            return self.rate / other.rate
        return self.rate / float(other)

    def __floordiv__(self, other: Self | Number) -> float:
        if isinstance(other, AlgoHashRateType):
            return self.rate // other.rate
        return self.rate // float(other)

    def __mul__(self, other: Number) -> Self:
        return self.__class__(rate=self.rate * float(other))


# Совместимость со старым кодом
class GenericHashrate(AlgoHashRateType):
    rate: float = 0.0
