# Voltops

**Voltops** is a Python library built for electronics and signal processing enthusiasts. Whether you're an engineer, student, or hobbyist, this package offers intuitive functions for working with electrical formulas and analyzing signals with ease. Every function is **physics-aware**—values carry metadata (DC/AC, RMS/peak, phase, frequency) so you catch mistakes before they propagate.

---

## Installation

```bash
pip install voltops
```

---

## Quick Start

### Basic Electronic Formulas

```python
from voltops.formulas.basic import BasicFormulas

# Calculate voltage using Ohm's Law: V = I * R
voltage = BasicFormulas.ohms_law(current=2, resistance=5)
print(f"Voltage: {voltage.value} V (kind={voltage.metadata.kind})")

# Calculate power: P = V * I
power = BasicFormulas.power(voltage=voltage, current=2)
print(f"Power: {power.value} W")
```

### Frequency Spectrum Analysis

```python
import numpy as np
from voltops.signal_processing.transforms import Transforms

# Generate a simple sine wave signal
t = np.linspace(0, 1, 1000, endpoint=False)
signal = np.sin(2 * np.pi * 10 * t)

# Get the frequency spectrum
freqs, amps = Transforms.frequency_spectrum(signal, sampling_rate=1000)
```

### Filtering Signals

```python
from voltops.signal_processing.filters import Filters

# Create a signal with multiple frequency components
t = np.linspace(0, 1, 1000, endpoint=False)
signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)

# Apply a low-pass filter with a cutoff at 15 Hz
filtered_signal = Filters.low_pass_filter(signal, cutoff=15, sampling_rate=1000)
```


## Features

- **Physics-aware quantities**: Voltage, Current, Resistance/Impedance, Power, Frequency, and Phase objects with waveform metadata.
- **Electronic Formulas**: Ohm's Law, power, and more—now returning safe quantity objects.
- **Signal Processing**: FFT, DFT, filtering, and spectral analysis.
- **Extensible API**: Easy-to-use, modular design for seamless integration.

Learn more about the design direction in [`docs/philosophy.md`](docs/philosophy.md).


## Contributing

Contributions are welcome!  
If you'd like to report a bug, request a feature, or contribute code, feel free to open an issue or submit a pull request on [GitHub](https://github.com/madhurthareja/voltops).


## Maintainers

This library is actively developed and maintained by **Madhur Thareja**.


## License

Licensed under the [MIT License](https://opensource.org/licenses/MIT).  
Feel free to use, modify, and distribute this library.
