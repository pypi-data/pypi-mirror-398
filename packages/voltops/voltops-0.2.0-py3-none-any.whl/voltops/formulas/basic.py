"""Closed-form formulas built on physics-aware quantities."""

from __future__ import annotations

from numbers import Number
from typing import Optional, Union

from voltops.core.quantities import (
    Current,
    ElectricalQuantity,
    Impedance,
    Power,
    Resistance,
    SignalKind,
    Voltage,
    blend_metadata,
    coerce_quantity,
)

NumberLike = Union[Number, ElectricalQuantity]


def _to_value(value: NumberLike) -> float:
    if isinstance(value, ElectricalQuantity):
        return value.value
    return float(value)


def _coerce_resistance_like(res_value: NumberLike) -> ElectricalQuantity:
    if isinstance(res_value, Resistance):
        return res_value
    if isinstance(res_value, Impedance):
        return res_value
    if isinstance(res_value, ElectricalQuantity):
        raise TypeError(
            "Resistance slot expects a Resistance/Impedance or a scalar, "
            f"not {res_value.__class__.__name__}."
        )
    if isinstance(res_value, Number):
        return Resistance(float(res_value))
    raise TypeError("Unsupported resistance value provided.")


class BasicFormulas:
    @staticmethod
    def ohms_law(
        *,
        voltage: Optional[NumberLike] = None,
        current: Optional[NumberLike] = None,
        resistance: Optional[NumberLike] = None,
    ) -> ElectricalQuantity:
        """Solve for the missing variable in Ohm's Law (V = I * R).

        Exactly two parameters must be provided. Scalars are automatically promoted to
        physics-aware quantity objects.
        """

        provided = [voltage, current, resistance]
        if sum(value is not None for value in provided) != 2:
            raise ValueError("Provide exactly two parameters: voltage, current, or resistance.")

        if voltage is None:
            cur_q = coerce_quantity(Current, current)
            res_q = _coerce_resistance_like(resistance)
            metadata = blend_metadata(cur_q, res_q)
            return Voltage(cur_q.value * res_q.value, metadata=metadata)

        if current is None:
            volt_q = coerce_quantity(Voltage, voltage)
            res_q = _coerce_resistance_like(resistance)
            metadata = blend_metadata(volt_q, res_q)
            return Current(volt_q.value / res_q.value, metadata=metadata)

        # Otherwise solve for resistance/impedance
        volt_q = coerce_quantity(Voltage, voltage)
        cur_q = coerce_quantity(Current, current)
        metadata = blend_metadata(volt_q, cur_q)
        value = volt_q.value / cur_q.value
        if metadata.kind is SignalKind.DC:
            return Resistance(value, metadata=metadata)
        return Impedance(value, metadata=metadata)

    @staticmethod
    def power(voltage: NumberLike, current: NumberLike) -> Power:
        """Calculate electrical power enforcing metadata consistency (P = V * I)."""

        volt_q = coerce_quantity(Voltage, voltage)
        cur_q = coerce_quantity(Current, current)
        metadata = blend_metadata(volt_q, cur_q)
        return Power(volt_q.value * cur_q.value, metadata=metadata)