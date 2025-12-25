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
from sciveo.tools.os import add_suffix_to_filename
from sciveo.media.pipelines.queues import MediaJobState
from sciveo.media.pipelines.base import BaseContentProcessor


class BaseProcessor(BaseContentProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.base_tmp_path = os.environ["WEB_MEDIA_PIPELINES_TMP_PATH"]
    debug("init", processor_config, max_progress)

  def process(self, media):
    return media

  def post_process(self):
    pass

  def init_run(self):
    pass

  def run(self, job, input):
    self.job = job
    self.job_id = job["id"]
    next_media = []
    if len(input) == 0:
      return []
    progress_per_media = self.max_progress / max(1, len(input))
    debug("run", job["id"], progress_per_media, "input", input)

    self.init_run()

    for i, media in enumerate(input):
      if self.is_processor_run(job, media):
        try:
          media = self.process(media)

          if self.is_append_processor():
            self.append_processor(media)

          if "next" not in media:
            continue

          self.resized(job, media)

          next_media += media["next"]
          media["next"] = []
        except Exception as e:
          exception(e, media)
      MediaJobState.queue().inc_progress(job["id"], progress_per_media)

    if self["output"]:
      job["output"] += next_media
    if self["append-content"]:
      job["append-content"] += next_media
    if self["update-content"]:
      job["update-content-data"] += input

    return next_media

  def resized(self, job, parent_media):
    if self.is_resizer():
      parent_media.setdefault("heights", [])
      for media in parent_media["next"]:
        parent_media["heights"].append(media["h"])
      if len(parent_media["heights"]) > 0:
        job["resized-resolutions"].append(parent_media)

  def is_resizer(self):
    return False

  def add_suffix_to_filename(self, file_path, siffix):
    if self["output"] or self["append-content"]:
      return add_suffix_to_filename(file_path, siffix)
    else:
      return file_path
