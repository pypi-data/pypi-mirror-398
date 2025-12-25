#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2024
#

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt

from sciveo.tools.logger import *
from sciveo.tools.common import *


class AudioFFT:
  def decimate(self, audio_data, ratio):
    # Define the cutoff frequency and the order of the filter
    cutoff = 0.1
    order = 4
    # Create the Butterworth filter
    b, a = butter(order, cutoff, btype='low', analog=False, output='ba')
    # Apply the filter to the signal
    filtered_signal = lfilter(b, a, audio_data)
    # Decimate the filtered signal
    return filtered_signal[::ratio]

  def fft(self, sample_rate, audio_data):
    debug("audio_data.shape", audio_data.shape)
    # Check for stereo, pick the first channel.
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
      audio_data = audio_data[:,0]

    if audio_data.shape[0] > 3000000:
      #audio_data = self.decimate(audio_data, 100)
      audio_data = audio_data[:3000000]

    debug("audio_data.shape", audio_data.shape)

    result = {}
    result["length"] = audio_data.shape[0] / sample_rate

    fft = np.fft.fft(audio_data)
    fft_mag = (fft.real**2 + fft.imag**2) ** 0.5

    result["audio_time"] = np.linspace(0., result["length"], audio_data.shape[0])
    freq = np.fft.fftfreq(result["audio_time"].shape[-1]) * sample_rate

    result["audio_data"] = self.normalize(audio_data)

    result["fft"], result["freq"] = self.half_fft(fft_mag, freq)
    result["fft"] = self.normalize(result["fft"])

    result["fft_bins"], result["freq_bins"] = self.bin_fft(result["fft"], result["freq"], bins=16)
    result["fft_bins"] = self.normalize(result["fft_bins"])

    result["hist"], result["hist_bins"] = np.histogram(np.absolute(result["audio_data"]), bins=4)
    result["hist"] = self.normalize(result["hist"])

    result["freq_fft_max"] = result["freq"][np.argmax(result["fft"])] * 2 / sample_rate
    result["freq_fft_min"] = result["freq"][np.argmin(result["fft"])] * 2 / sample_rate

    return result

  def half_fft(self, fft, freq, cutoff_freq=0):
    bool_freq = freq >= cutoff_freq
    return fft[bool_freq], freq[bool_freq]

  def bin_fft(self, fft, freq, bins=16):
    l = len(fft)
    l1 = int(l / bins)
    l2 = l1 * bins
    fft = fft[l - l2:].reshape((bins, l1)).sum(axis=1)
    freq = freq[l - l2:].reshape((bins, l1)).max(axis=1)
    return fft, freq

  def binning(self, data, bins=16):
    l = len(data)
    l1 = int(l / bins)
    l2 = l1 * bins
    data = data[l - l2:].reshape((bins, l1)).sum(axis=1)
    return data

  def normalize(self, data):
    # return data / np.linalg.norm(data)
    # return data / max(data) # scaling here...
    min_data = data.min()
    max_data = data.max()

    if max_data - min_data < 1:
      return data

    return (data - min_data) / (max_data - min_data)


def plot_audio(width, height, sampling_rate, aac_audio_local_path, image_audio_local_path):
  debug("Audio Extractor", aac_audio_local_path)
  try:
    wav_audio_local_path = aac_audio_local_path.replace(".aac", ".wav")
    cmd = f"ffmpeg -i '{aac_audio_local_path}' -ar {sampling_rate} '{wav_audio_local_path}'"
    os.system(cmd)

    sample_rate, audio_data = wavfile.read(wav_audio_local_path)
    debug("Audio Extractor sample_rate", sample_rate, "audio_data shape", audio_data.shape)
    os.remove(wav_audio_local_path)

    # Check for stereo, pick the first channel.
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
      audio_data = audio_data[:,0]

    dpi = 100
    fig = plt.figure(figsize=(int(width)/dpi, int(height)/dpi), dpi=dpi)
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)

    ax1.plot(audio_data)
    ax1.set_xlabel('samples')
    ax1.set_ylabel('Amplitude')
    ax1.set_title("Audio Time domain")

    fft = AudioFFT().fft(sample_rate, audio_data)

    ax2.plot(fft["freq"], fft["fft"])
    ax2.set_xlabel('frequency')
    ax2.set_ylabel('Amplitude')
    ax2.set_title("Audio Frequency domain")

    plt.subplots_adjust(hspace=0.5)
    plt.savefig(image_audio_local_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
  except Exception as e:
    exception(e, aac_audio_local_path)
