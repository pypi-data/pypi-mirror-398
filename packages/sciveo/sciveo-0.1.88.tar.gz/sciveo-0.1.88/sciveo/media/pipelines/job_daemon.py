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

import time
import os
import boto3

from sciveo.tools.logger import *
from sciveo.tools.daemon import *
from sciveo.tools.synchronized import ListQueue
from sciveo.tools.os import *
from sciveo.tools.http import *
from sciveo.media.pipelines.pipeline import *
from sciveo.media.pipelines.queues import MediaJobState


class JobQueueDaemon(DaemonBase):
  _queue = None

  @staticmethod
  def queue():
    if JobQueueDaemon._queue is None:
      JobQueueDaemon._queue = ListQueue("pipeline jobs")
    return JobQueueDaemon._queue

  def __init__(self, base_tmp_path):
    super().__init__()
    self.s3 = boto3.client('s3')
    self.base_tmp_path = base_tmp_path

  def run(self):
    while(self.is_running):
      try:
        job = JobQueueDaemon.queue().pop()
        job = self.process_job(job)
      except Exception as e:
        exception(e, type(self).__name__)
        time.sleep(3)

  def process_job(self, job):
    debug("process_job job", job)
    job["input"] = job["content"]
    MediaJobState.queue().start(job["id"])
    MediaJobState.queue().inc_progress(job["id"], 10)

    pipeline = MediaPipeline(job)
    job = pipeline.run()

    MediaJobState.queue().finish(job["id"], job)
    # debug("job output", job["output"])
    return job
