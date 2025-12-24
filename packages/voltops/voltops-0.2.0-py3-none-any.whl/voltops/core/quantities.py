"""Physics-aware electrical quantity objects used across VoltOps."""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from enum import Enum
from numbers import Number
from typing import Optional, Tuple, Type, TypeVar, Union


class SignalKind(str, Enum):
    """Enumerates the supported waveform representations."""

    DC = "dc"
    AC_RMS = "ac_rms"
    AC_PEAK = "ac_peak"


@dataclass(frozen=True)
class SignalMetadata:
    """Metadata carried by every electrical quantity instance."""

    kind: SignalKind = SignalKind.DC
    phase_deg: float = 0.0
    frequency_hz: Optional[float] = None
    reference: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind is SignalKind.DC:
            if abs(self.phase_deg) > 1e-9:
                raise ValueError("DC metadata cannot include a phase offset.")
            if self.frequency_hz is not None:
                raise ValueError("DC metadata cannot define a frequency.")
        if self.frequency_hz is not None and self.frequency_hz <= 0:
            raise ValueError("Frequency metadata must be positive when provided.")

    def is_default(self) -> bool:
        return (
            self.kind is SignalKind.DC
            and abs(self.phase_deg) <= 1e-9
            and self.frequency_hz is None
            and self.reference is None
        )

    def ensure_compatible_with(self, other: "SignalMetadata") -> None:
        if self.kind != other.kind:
            raise ValueError("Quantities must share the same signal kind (DC/AC RMS/AC peak).")
        if self.kind is not SignalKind.DC:
            if (
                self.frequency_hz is not None
                and other.frequency_hz is not None
                and not math.isclose(self.frequency_hz, other.frequency_hz, rel_tol=1e-9)
            ):
                raise ValueError("AC quantities must share the same frequency to combine.")
            if not math.isclose(self.phase_deg, other.phase_deg, abs_tol=1e-6):
                raise ValueError("AC quantities must share the same phase reference to combine.")
        if self.reference and other.reference and self.reference != other.reference:
            raise ValueError("Quantities cannot mix different reference designations.")

    def merge(self, other: "SignalMetadata") -> "SignalMetadata":
        """Return a metadata instance compatible with both operands."""

        if self.is_default():
            return other
        if other.is_default():
            return self
        self.ensure_compatible_with(other)
        return SignalMetadata(
            kind=self.kind,
            phase_deg=self.phase_deg if self.kind is not SignalKind.DC else 0.0,
            frequency_hz=self.frequency_hz or other.frequency_hz,
            reference=self.reference or other.reference,
        )

    def describe(self) -> str:
        parts = [self.kind.value]
        if self.kind is not SignalKind.DC:
            phase = f"phase={self.phase_deg:g}°"
            freq = f"f={self.frequency_hz:g}Hz" if self.frequency_hz else "f=?"
            parts.extend([phase, freq])
        if self.reference:
            parts.append(f"ref={self.reference}")
        return " | ".join(parts)


TQuantity = TypeVar("TQuantity", bound="ElectricalQuantity")


@dataclass(frozen=True)
class ElectricalQuantity:
    """Base class for voltage, current, power, etc."""

    value: float
    metadata: SignalMetadata = field(default_factory=SignalMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", float(self.value))

    # ------------------------------------------------------------------
    # Convenience utilities
    # ------------------------------------------------------------------
    def with_value(self: TQuantity, value: float) -> TQuantity:
        return replace(self, value=float(value))

    def with_metadata(self: TQuantity, metadata: SignalMetadata) -> TQuantity:
        return replace(self, metadata=metadata)

    def as_tuple(self) -> Tuple[float, SignalMetadata]:
        return self.value, self.metadata

    def __float__(self) -> float:  # pragma: no cover - trivial
        return self.value

    # ------------------------------------------------------------------
    # Arithmetic guarded by metadata compatibility
    # ------------------------------------------------------------------
    def _assert_compatible(self, other: "ElectricalQuantity") -> None:
        if type(self) is not type(other):
            raise TypeError("Quantities must share the same dimension to combine.")
        self.metadata.ensure_compatible_with(other.metadata)

    def __add__(self: TQuantity, other: TQuantity) -> TQuantity:
        self._assert_compatible(other)
        return self.with_value(self.value + other.value)

    def __sub__(self: TQuantity, other: TQuantity) -> TQuantity:
        self._assert_compatible(other)
        return self.with_value(self.value - other.value)

    def __mul__(self: TQuantity, other: Number) -> TQuantity:
        if not isinstance(other, Number):
            raise TypeError("Quantities can only be scaled by numeric constants.")
        return self.with_value(self.value * float(other))

    def __rmul__(self: TQuantity, other: Number) -> TQuantity:
        return self.__mul__(other)

    def __truediv__(self: TQuantity, other: Number) -> TQuantity:
        if not isinstance(other, Number):
            raise TypeError("Quantities can only be divided by numeric constants.")
        return self.with_value(self.value / float(other))

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"{self.__class__.__name__}({self.value:g}, metadata={self.metadata.describe()})"


@dataclass(frozen=True)
class Voltage(ElectricalQuantity):
    """Electrical potential difference in volts."""


@dataclass(frozen=True)
class Current(ElectricalQuantity):
    """Electrical current in amperes."""


@dataclass(frozen=True)
class Resistance(ElectricalQuantity):
    """Purely real resistance in ohms (steady-state)."""

    def __post_init__(self) -> None:
        if self.metadata.kind is not SignalKind.DC:
            raise ValueError("Resistance values must be tagged as DC metadata.")
        super().__post_init__()


@dataclass(frozen=True)
class Impedance(ElectricalQuantity):
    """Generalized impedance magnitude in ohms."""


@dataclass(frozen=True)
class Power(ElectricalQuantity):
    """Instantaneous or average power in watts."""


@dataclass(frozen=True)
class Frequency:
    """Scalar frequency helper to enrich metadata objects."""

    hertz: float
    reference: Optional[str] = None

    def __post_init__(self) -> None:
        value = float(self.hertz)
        if value < 0:
            raise ValueError("Frequency must be non-negative.")
        object.__setattr__(self, "hertz", value)

    @property
    def angular(self) -> float:
        return self.hertz * 2 * math.pi

    def with_reference(self, reference: str) -> "Frequency":
        return replace(self, reference=reference)


@dataclass(frozen=True)
class Phase:
    """Phase helper carried by measurement metadata."""

    degrees: float
    reference: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "degrees", float(self.degrees))

    @property
    def radians(self) -> float:
        return math.radians(self.degrees)

    def wrap(self) -> "Phase":
        return replace(self, degrees=((self.degrees + 180) % 360) - 180)


NumberLike = Union[Number, ElectricalQuantity]


def coerce_quantity(expected_cls: Type[TQuantity], value: NumberLike) -> TQuantity:
    """Convert floats to quantity instances while validating dimensions."""

    if isinstance(value, expected_cls):
        return value
    if isinstance(value, ElectricalQuantity):
        raise TypeError(
            f"Expected {expected_cls.__name__} but received {value.__class__.__name__}."
        )
    if isinstance(value, Number):
        return expected_cls(float(value))
    raise TypeError(f"Unsupported value for {expected_cls.__name__}: {value!r}")


def blend_metadata(*quantities: NumberLike) -> SignalMetadata:
    """Derive metadata shared by all provided quantities."""

    metadata: Optional[SignalMetadata] = None
    for q in quantities:
        if isinstance(q, ElectricalQuantity):
            metadata = q.metadata if metadata is None else metadata.merge(q.metadata)
    return metadata or SignalMetadata()
