import numpy as np
from typing import Tuple

class Transforms:
    @staticmethod
    def dft(signal_input: np.ndarray) -> np.ndarray:
        """
        Compute the Discrete Fourier Transform of the input signal.
        """
        N = len(signal_input)
        n = np.arange(N)
        k = n.reshape((N, 1))
        e = np.exp(-2j * np.pi * k * n / N)
        return np.dot(e, signal_input)

    @staticmethod
    def fft(signal_input: np.ndarray) -> np.ndarray:
        """
        Compute the Fast Fourier Transform of the input signal using NumPy.
        """
        return np.fft.fft(signal_input)

    @staticmethod
    def frequency_spectrum(signal_input: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the frequency spectrum of the input signal.
        """
        N = len(signal_input)
        fft_result = np.fft.fft(signal_input)
        frequencies = np.fft.fftfreq(N, 1 / sampling_rate)
        amplitudes = np.abs(fft_result) / N
        return frequencies[:N//2], amplitudes[:N//2]