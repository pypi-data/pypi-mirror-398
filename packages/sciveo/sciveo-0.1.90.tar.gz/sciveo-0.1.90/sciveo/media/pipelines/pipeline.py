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

from sciveo.tools.logger import *

from sciveo.media.pipelines.processors.audio.audio import *

from sciveo.media.pipelines.processors.video.video_resample import *
from sciveo.media.pipelines.processors.video.video_frames import *
from sciveo.media.pipelines.processors.video.motion_detection import *
from sciveo.media.pipelines.processors.video.resize import *
from sciveo.media.pipelines.processors.video.video_album import *
from sciveo.media.pipelines.processors.video.generators import *

from sciveo.media.pipelines.processors.image.histogram import *
from sciveo.media.pipelines.processors.image.resize import *
from sciveo.media.pipelines.processors.image.album import *
from sciveo.media.pipelines.processors.image.album_in_image import *
from sciveo.media.pipelines.processors.image.filters import *
from sciveo.media.pipelines.processors.image.generators import *
from sciveo.media.pipelines.processors.image.embeddings import *
from sciveo.media.pipelines.processors.image.depth_esimation import *
from sciveo.media.pipelines.processors.image.mask import *
from sciveo.media.pipelines.processors.image.segmentation import *
from sciveo.media.pipelines.processors.image.watermark import *
from sciveo.media.pipelines.processors.image.object_detection import ImageObjectDetectionProcessor

from sciveo.media.pipelines.processors.file.archive import *

from sciveo.media.pipelines.processors.sci.time_series.predictor import *
from sciveo.media.pipelines.processors.sci.time_series.trainer import *
from sciveo.media.pipelines.processors.sci.dataset import *

from sciveo.media.pipelines.processors.nlp.address import *

from sciveo.media.pipelines.processors.aws import *
from sciveo.media.pipelines.processors.media_info import *
from sciveo.media.pipelines.processors.qr import *

from sciveo.media.pipelines.postprocessors.default import *


class MediaPipeline:
  def __init__(self, job) -> None:
    self.job = job
    self.configuration = job["configuration"]
    debug("configuration", self.configuration)
    self.pipeline = []

    # TODO: Should have subscription-based processors list instead
    # TODO: Replace/simplify with a list of classes only and build this map
    self.available_processors = {
      "s3-download": S3MediaDownload,
      "archive-zip": FileArchiveZIP,
      "media-info": MediaInfo,
      "QR-generator": QRGenerator,

      "audio-extract": AudioExtract,

      "video-resize": VideoResize,
      "video-downsample": VideoDownsample,
      "video-frames-extract": VideoFramesExtract,
      "video-motion-detector": VideoMotionDetector,
      "video-album": VideoAlbum,
      "video-to-text": VideoToTextProcessor,

      "image-resize": ImageResize,
      "image-histogram": ImageHistogram,
      "image-album": Album,
      "album-in-image": AlbumInImage,
      "image-filters": ImageFilters,
      "image-watermark": ImageWatermark,
      "image-diffusion": ImageDiffusionText,
      "image-diffusion-image-text": ImageDiffusionImageText,
      "image-to-text": ImageToTextProcessor,
      "image-fgbg-filter": ImageFGBGFilter,
      "image-segmentation": ImageSegmentation,
      "image-depth-estimation": ImageDepthEstimation,
      "image-embedding": ImageEmbeddingProcessor,
      "image-object-detection": ImageObjectDetectionProcessor,

      "sci-timeseries-predictor": TimeSeriesPredictorProcessor,
      "sci-timeseries-trainer": TimeSeriesTrainerProcessor,
      "project-datasets-plots": ProjectDatasetPlots,

      "nlp-address-standard": AddressStandard,
      "nlp-address-geocode": AddressGeocode,
    }

    self.available_postprocessors = {
      "s3-upload": S3UploadPostprocessor,
      "append-content": AppendContentPostprocessor,
      "update-content-data": UpdateContentDataPostprocessor,
      "resized-resolutions": ResizedResolutionsPostprocessor,
      "channel-create-simple": ChannelCreateSimplePostprocessor
    }

    self.count_processors = 0
    self.count_processors_dfs(0, self.configuration["processors"])
    debug("count_processors", self.count_processors)

  def describe(self):
    d = {"processors": {}, "postprocessors": {}}
    for processor_name, processor in self.available_processors.items():
      d["processors"][processor_name] = processor({}, 100).describe()
    for postprocessor_name, postprocessor in self.available_postprocessors.items():
      d["postprocessors"][postprocessor_name] = postprocessor(self.job, {}, 100).describe()
    return d

  def count_processors_dfs(self, level, processors):
    for processor_name, processor_definition in processors.items():
      debug(level, processor_name)
      self.count_processors += 1
      if "next" in processor_definition:
        self.count_processors_dfs(level + 1, processor_definition["next"])

  # Walk processors and filter input
  def walk_processors_dfs(self, level, input, processors, result, max_level=1):
    if level > max_level:
      return

    for processor_name, processor_definition in processors.items():
      # debug("walk", level, processor_name)

      processor = self.available_processors[processor_name](processor_definition.get("configuration", {}), 100)

      for i, media in enumerate(input):
        # Check if the media really needs this processor, add to input if should be processed by it.
        if processor.is_processor_run(self.job, media) and processor.is_processor_output():
          debug("walk add media", media['guid'], media.get('processors', ""), "because of", processor.append_name(), [processor.is_processor_run(self.job, media), processor.is_processor_output()])
          result[media['guid']] = media

      if "next" in processor_definition:
        self.walk_processors_dfs(level + 1, input, processor_definition["next"], result)

  def run_processors_dfs(self, level, input, processors):
    for processor_name, processor_definition in processors.items():
      debug(level, processor_name)

      processor = self.available_processors[processor_name](processor_definition.get("configuration", {}), 40 / self.count_processors) # Account 60% for all processors
      next_input = processor.run(self.job, input)

      processor.post_process()

      if "next" in processor_definition:
        self.run_processors_dfs(level + 1, next_input, processor_definition["next"])

  def run_postprocessors(self):
    postprocessors = self.configuration.get("postprocessors", {
      "s3-upload": {}, "append-content": {}, "update-content-data": {},"resized-resolutions": {},
    })

    for postprocessor_name, postprocessor_definition in postprocessors.items():
      if postprocessor_name in self.available_postprocessors:
        postprocessor = self.available_postprocessors[postprocessor_name](self.job, postprocessor_definition.get("configuration", {}), 60 / len(postprocessors))
        postprocessor.run()
      else:
        warning("postprocessor", postprocessor_name, "is not available")

  def run(self):
    self.job["output"] = []

    for k, v in self.available_postprocessors.items():
      self.job[k] = []

    list_media = {}
    max_walk_level = self.configuration["processors"].get("max_walk_level", 1)
    self.walk_processors_dfs(0, self.job["input"], self.configuration["processors"], list_media, max_walk_level)
    self.job["input"] = list(list_media.values())
    self.job["content"] = self.job["input"]
    debug("filtered content for processing", list(list_media.keys()))

    self.run_processors_dfs(0, self.job["input"], self.configuration["processors"])

    self.run_postprocessors()

    return self.job
