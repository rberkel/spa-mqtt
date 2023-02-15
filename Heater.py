# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = heater_from_dict(json.loads(json_string))

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, TypeVar, Type, cast


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class OperationState(Enum):
    COOLING = "cooling"
    HEATING = "heating"
    IDLE = "idle"


@dataclass
class Heater:
    configured_setpoint: float
    temperature: float
    active_setpoint: Optional[float] = None
    operation_state: Optional[OperationState] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Heater':
        assert isinstance(obj, dict)
        configured_setpoint = from_float(obj.get("configuredSetpoint"))
        temperature = from_float(obj.get("temperature"))
        active_setpoint = from_union([from_float, from_none], obj.get("activeSetpoint"))
        operation_state = from_union([OperationState, from_none], obj.get("operationState"))
        return Heater(configured_setpoint, temperature, active_setpoint, operation_state)

    def to_dict(self) -> dict:
        result: dict = {}
        result["configuredSetpoint"] = to_float(self.configured_setpoint)
        result["temperature"] = to_float(self.temperature)
        result["activeSetpoint"] = from_union([to_float, from_none], self.active_setpoint)
        result["operationState"] = from_union([lambda x: to_enum(OperationState, x), from_none], self.operation_state)
        return result


def heater_from_dict(s: Any) -> Heater:
    return Heater.from_dict(s)


def heater_to_dict(x: Heater) -> Any:
    return to_class(Heater, x)
