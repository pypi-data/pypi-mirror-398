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

from sciveo.tools.logger import *
from sciveo.tools.synchronized import DataSynchronized
from sciveo.tools.http import *
from sciveo.tools.simple_counter import Timer


class PipelineQueue(DataSynchronized):
  def __init__(self, tag=""):
    super().__init__(tag)
    self.timer = Timer()

  def update_job_state(self, job_id, state):
    url = f"{os.environ['MEDIA_API_BASE_URL']}/api/v1/media_pipeline_job/state/?job_id={job_id}&transit_to={state}"
    headers = { "Auth-Token": os.environ['MEDIA_API_AUTH_TOKEN'] }
    response = GET(url, headers=headers)

  def update_job_progress(self, job_id, progress):
    elapsed = self.timer.stop()
    debug("progress", progress, self.data_sync[job_id]["progress"], "elapsed", elapsed)
    if elapsed > 1:
      progress = int(min(progress, 100.0))
      url = f"{os.environ['MEDIA_API_BASE_URL']}/api/v1/media_pipeline_job/progress/?job_id={job_id}&set={progress}"
      headers = { "Auth-Token": os.environ['MEDIA_API_AUTH_TOKEN'] }
      response = GET(url, headers=headers)
      self.timer.start()

  def start(self, job_id):
    with self.lock_data:
      self.data_sync[job_id] = {"state": "started", "progress": 0}
    self.update_job_progress(job_id, 0)
    self.update_job_state(job_id, "started")

  def inc_progress(self, job_id, inc_value):
    progress = 0
    with self.lock_data:
      self.data_sync[job_id]["progress"] += inc_value
      self.data_sync[job_id]["progress"] = min(self.data_sync[job_id]["progress"], 100)
      progress = self.data_sync[job_id]["progress"]
    self.update_job_progress(job_id, progress)

  def finish(self, job_id, job):
    with self.lock_data:
      self.data_sync[job_id] = {"state": "finished", "progress": 100, "job": job}
    self.update_job_progress(job_id, 100)
    self.update_job_state(job_id, "finished")


class MediaJobState:
  _queue = None

  @staticmethod
  def queue():
    if MediaJobState._queue is None:
      MediaJobState._queue = PipelineQueue("media jobs")
    return MediaJobState._queue
