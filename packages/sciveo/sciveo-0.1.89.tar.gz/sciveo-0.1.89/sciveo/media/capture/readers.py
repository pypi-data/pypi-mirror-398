#
# Stanislav Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact s.georgiev@softel.bg.
#
# 2025
#

import os
import select
import json
import subprocess
import ffmpeg
import json
import numpy as np
from sciveo.tools.logger import *
from sciveo.tools.timers import Timer


class VideoReaderFFMPEG:
  def __init__(self, path, resolution=720, RGB=False, gpu_id=-1) -> None:
    self.path = path
    self.resolution = resolution
    self.RGB = RGB
    self.gpu_id = gpu_id

  @staticmethod
  def get_dim(w, h, resolution):
    if resolution <= 0:
      return w, h

    if h > resolution:
      ratio = resolution / h
    else:
      ratio = 1.0
    width = int(w * ratio)
    height = int(h * ratio)
    width += width % 2
    height += height % 2
    return width, height

  @staticmethod
  def read(file_path, resolution=720, RGB=False, gpu_id=-1, timeout=30, fps=None, framestep=None):
    timer_video_read = Timer()
    frames = []

    probe = subprocess.check_output([
      "ffprobe", "-v", "error",
      "-select_streams", "v:0",
      "-show_entries", "stream=width,height,codec_name",
      "-of", "json", file_path
    ])
    stream_data = json.loads(probe)["streams"][0]

    in_w, in_h = int(stream_data["width"]), int(stream_data["height"])
    out_w, out_h = VideoReaderFFMPEG.get_dim(in_w, in_h, resolution)
    frame_size = out_w * out_h * 3

    gpu_nvdec_id = int(os.environ.get("GPU_NVDEC_H264_ID", gpu_id))

    codec = stream_data["codec_name"]
    if codec in ["h264", "avc1"]:
      decoder = "h264_cuvid"
    elif codec in ["hevc", "h265", "hvc1"]:
      decoder = "hevc_cuvid"
      gpu_nvdec_id = int(os.environ.get("GPU_NVDEC_H265_ID", gpu_nvdec_id))

    HW = "CPU"
    pix_fmt = "rgb24" if RGB else "bgr24"

    if min(gpu_id, gpu_nvdec_id) < 0:
      HW = "CPU"
      ffmpeg_input = ffmpeg.input(file_path)
    else:
      HW = "GPU"
      ffmpeg_input = ffmpeg.input(file_path, hwaccel='cuda', hwaccel_device=gpu_nvdec_id, c=decoder)

    if in_w != out_w or in_h != out_h:
      ffmpeg_input = ffmpeg_input.filter('scale', out_w, out_h)

    if fps is not None:
      ffmpeg_input = ffmpeg_input.filter('fps', fps=fps)
    if framestep is not None:
      ffmpeg_input = ffmpeg_input.filter('framestep', step=framestep)

    process = (
      ffmpeg_input
      .output('pipe:', format='rawvideo', pix_fmt=pix_fmt, vsync='vfr')
      .global_args('-v', 'quiet')
      .run_async(pipe_stdout=True, pipe_stderr=subprocess.DEVNULL)
    )

    fd = process.stdout.fileno()

    while True:
      ready, _, _ = select.select([fd], [], [], timeout)
      if not ready:
        warning("VideoReaderFFMPEG::read", file_path, f"[{HW}][{gpu_id}] not ready FAIL")
        process.kill()
        process.wait()
        frames = []
        break

      in_bytes = process.stdout.read(frame_size)
      if not in_bytes:
        break
      frame = np.frombuffer(in_bytes, np.uint8).reshape([out_h, out_w, 3]).copy()
      frames.append(frame)

    process.wait()

    if gpu_id >= 0 and len(frames) == 0:
      warning("VideoReaderFFMPEG::read", file_path, f"[{HW}][{gpu_id}] reading not successful, fallback to CPU")
      return VideoReaderFFMPEG.read(file_path, resolution, RGB, gpu_id=-1)

    elapsed = timer_video_read.stop()
    FPS = round(len(frames) / elapsed, 2)
    debug("VideoReaderFFMPEG::read", file_path, f"[{HW}] video reading {len(frames)} frames, codec[{codec}] decoder[{decoder}] pix_fmt[{pix_fmt}] [{out_w}x{out_h}], elapsed {round(elapsed, 1)} FPS {FPS}")
    return frames

  def __call__(self):
    return VideoReaderFFMPEG.read(self.path, self.resolution, RGB=self.RGB, gpu_id=self.gpu_id)


