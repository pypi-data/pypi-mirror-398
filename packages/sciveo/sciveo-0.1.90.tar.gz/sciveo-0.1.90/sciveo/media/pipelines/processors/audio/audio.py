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

import os
from scipy.io import wavfile
import matplotlib.pyplot as plt

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.base import *


class AudioExtract(BaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    # TODO: Add more audio params like sampling rate (currently using 8KHz), perhaps output file type (currently AAC) etc.
    self.default.update({"width": 640, "height": 480, "sampling_rate": 16000})

  def plot_inprocess(self, w, h, aac_audio_local_path, image_audio_local_path):
    debug("plot_inprocess", aac_audio_local_path)
    try:
      wav_audio_local_path = aac_audio_local_path.replace(".aac", ".wav")

      cmd = "ffmpeg -i '{}' -ar 8000 '{}'".format(aac_audio_local_path, wav_audio_local_path)
      os.system(cmd)

      sample_rate, audio_data = wavfile.read(wav_audio_local_path)
      debug("sample_rate", sample_rate)
      os.remove(wav_audio_local_path)

      dpi = 100
      fig = plt.figure(figsize=(w/dpi, h/dpi), dpi=dpi)
      ax = fig.add_subplot(1, 1, 1)

      ax.plot(audio_data)
      ax.set_xlabel('samples')
      ax.set_ylabel('Amplitude')
      ax.set_title("Audio Waveform")

      plt.savefig(image_audio_local_path, dpi=dpi, bbox_inches='tight', pad_inches=0)
    except Exception as e:
      exception(e, aac_audio_local_path)

  def plot_new_process(self, w, h, sampling_rate, aac_audio_local_path, image_audio_local_path):
    cmd = "sciveo media-run --processor audio-plot "
    cmd += f"--width {w} --height {h} "
    cmd += f"--rate {sampling_rate} "
    cmd += f"--input-path '{aac_audio_local_path}' "
    cmd += f"--output-path '{image_audio_local_path}' "
    cmd += " 1>audio.log 2>audio-error.log"
    debug("plot_new_process cmd", cmd)
    os.system(cmd)

  def plot_audio(self, media, aac_audio_local_path):
    debug("draw", aac_audio_local_path)
    try:
      w, h = self["width"], self["height"]

      image_audio_local_path = aac_audio_local_path.replace(".aac", ".png")

      # self.plot_inprocess(w, h, aac_audio_local_path, image_audio_local_path)
      self.plot_new_process(w, h, self["sampling_rate"], aac_audio_local_path, image_audio_local_path)

      key = self.replace_ext(f"audio-wave-{media['key']}", ".png")
      self.next_content(media, f"audio-plot-{h}", image_audio_local_path, content_type="image", key=key, w=w, h=h)
    except Exception as e:
      exception(e, aac_audio_local_path)
    return media

  def process(self, media):
    video_local_path = media["local_path"]
    aac_audio_local_path = self.replace_ext(video_local_path)

    cmd_ffmpeg = "ffmpeg -i '{}' -acodec copy -vn '{}'".format(video_local_path, aac_audio_local_path)
    os.system(cmd_ffmpeg)
    result = os.path.isfile(aac_audio_local_path)
    debug("run", cmd_ffmpeg, result)

    if result:
      self.next_content(media, "audio", aac_audio_local_path, content_type="audio", key=self.replace_ext(media['key']), w=200, h=100)
      self.plot_audio(media, aac_audio_local_path)
    else:
      info("video does not have audio", aac_audio_local_path)

    return media

  def content_type(self):
    return "video"

  def name(self):
    return "audio-extract"
