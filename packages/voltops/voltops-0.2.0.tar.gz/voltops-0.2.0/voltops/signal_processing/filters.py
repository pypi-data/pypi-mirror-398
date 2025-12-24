import numpy as np
from scipy import signal

class Filters:
    @staticmethod
    def low_pass_filter(signal_input: np.ndarray, cutoff: float, sampling_rate: float, order: int = 5) -> np.ndarray:
        """
        Apply a low-pass Butterworth filter to the input signal.
        """
        nyquist = 0.5 * sampling_rate
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        return signal.filtfilt(b, a, signal_input)

    @staticmethod
    def high_pass_filter(signal_input: np.ndarray, cutoff: float, sampling_rate: float, order: int = 5) -> np.ndarray:
        """
        Apply a high-pass Butterworth filter to the input signal.
        """
        nyquist = 0.5 * sampling_rate
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
        return signal.filtfilt(b, a, signal_input)

    @staticmethod
    def band_pass_filter(signal_input: np.ndarray, lowcut: float, highcut: float, sampling_rate: float, order: int = 5) -> np.ndarray:
        """
        Apply a band-pass Butterworth filter to the input signal.
        """
        nyquist = 0.5 * sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = signal.butter(order, [low, high], btype='band', analog=False)
        return signal.filtfilt(b, a, signal_input)

    @staticmethod
    def band_stop_filter(signal_input: np.ndarray, lowcut: float, highcut: float, sampling_rate: float, order: int = 5) -> np.ndarray:
        """
        Apply a band-stop Butterworth filter to the input signal.
        """
        nyquist = 0.5 * sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = signal.butter(order, [low, high], btype='bandstop', analog=False)
        return signal.filtfilt(b, a, signal_input)