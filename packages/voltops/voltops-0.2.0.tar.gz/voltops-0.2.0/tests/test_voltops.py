import pytest
import numpy as np
from voltops.formulas.basic import BasicFormulas
from voltops.core.quantities import Voltage, Current, Resistance, Power, SignalMetadata, SignalKind
from voltops.signal_processing.filters import Filters
from voltops.signal_processing.transforms import Transforms

def test_ohms_law():
    voltage = BasicFormulas.ohms_law(current=2, resistance=5)
    assert isinstance(voltage, Voltage)
    assert voltage.value == pytest.approx(10)

    current = BasicFormulas.ohms_law(voltage=10, resistance=5)
    assert isinstance(current, Current)
    assert current.value == pytest.approx(2)

    resistance = BasicFormulas.ohms_law(voltage=10, current=2)
    assert isinstance(resistance, Resistance)
    assert resistance.value == pytest.approx(5)

def test_power():
    power = BasicFormulas.power(voltage=10, current=2)
    assert isinstance(power, Power)
    assert power.value == pytest.approx(20)

    ac_metadata = SignalMetadata(kind=SignalKind.AC_RMS, frequency_hz=60, phase_deg=0)
    voltage = Voltage(120, metadata=ac_metadata)
    current = Current(10, metadata=ac_metadata)
    ac_power = BasicFormulas.power(voltage=voltage, current=current)
    assert ac_power.metadata.kind is SignalKind.AC_RMS


def test_power_metadata_mismatch():
    meta_a = SignalMetadata(kind=SignalKind.AC_RMS, frequency_hz=50, phase_deg=0)
    meta_b = SignalMetadata(kind=SignalKind.AC_RMS, frequency_hz=60, phase_deg=0)
    voltage = Voltage(10, metadata=meta_a)
    current = Current(1, metadata=meta_b)
    with pytest.raises(ValueError):
        BasicFormulas.power(voltage=voltage, current=current)

def test_frequency_spectrum():
    t = np.linspace(0, 1, 1000, endpoint=False)
    signal = np.sin(2 * np.pi * 10 * t)
    freqs, amps = Transforms.frequency_spectrum(signal, sampling_rate=1000)
    assert len(freqs) == 500
    assert len(amps) == 500

def test_low_pass_filter():
    t = np.linspace(0, 1, 1000, endpoint=False)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    filtered_signal = Filters.low_pass_filter(signal, cutoff=15, sampling_rate=1000)
    assert len(filtered_signal) == len(signal)
    assert np.all(np.abs(filtered_signal) <= 1.5)

def test_high_pass_filter():
    t = np.linspace(0, 1, 1000, endpoint=False)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    filtered_signal = Filters.high_pass_filter(signal, cutoff=15, sampling_rate=1000)
    assert len(filtered_signal) == len(signal)
    assert np.all(np.abs(filtered_signal) <= 1.5)

def test_band_pass_filter():
    t = np.linspace(0, 1, 1000, endpoint=False)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    filtered_signal = Filters.band_pass_filter(signal, lowcut=5, highcut=15, sampling_rate=1000)
    assert len(filtered_signal) == len(signal)
    assert np.all(np.abs(filtered_signal) <= 1.5)

def test_band_stop_filter():
    t = np.linspace(0, 1, 1000, endpoint=False)
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    filtered_signal = Filters.band_stop_filter(signal, lowcut=5, highcut=15, sampling_rate=1000)
    assert len(filtered_signal) == len(signal)
    assert np.all(np.abs(filtered_signal) <= 1.5)

if __name__ == "__main__":
    pytest.main()