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
import time

from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
from sciveo.tools.os import *
from sciveo.tools.simple_counter import RunCounter
from sciveo.tools.configuration import ConfigurationArguments
from sciveo.tools.aws.priority_queue import SQSPriorityQueue
from sciveo.media.pipelines.pipeline import *
from sciveo.media.pipelines.queues import MediaJobState


class MaintenanceDaemon(DaemonBase):
  def __init__(self, **kwargs):
    self.arguments = ConfigurationArguments({
      "period": 3600,
      "run_period_files": 24,
      "retention_period_files": 30,
    }, **kwargs)

    super().__init__(period=self.arguments["period"])

    self.base_tmp_path = os.environ["WEB_MEDIA_PIPELINES_TMP_PATH"]

    self.timers = [
      RunCounter(self.arguments['run_period_files'], lambda: run_system_cmd(f"find {self.base_tmp_path} -mtime +{self.arguments['retention_period_files']} -type f -delete")),
      # RunCounter(3, self.print_me),
    ]

  def loop(self):
    for timer in self.timers:
      timer.run()


class MediaJobQueueDaemon(DaemonBase):
  def __init__(self):
    super().__init__()
    self.queue_level = int(os.environ.get("WEB_MEDIA_QUEUE_LEVEL", 1))
    self.queue_id = int(os.environ.get("WEB_MEDIA_QUEUE_ID", 1))
    self.queue = SQSPriorityQueue(self.queue_level, self.queue_id)

  def loop(self):
    job = self.queue.pull_wait()

    debug("new process job", job)
    job["input"] = job["content"]
    MediaJobState.queue().start(job["id"])
    MediaJobState.queue().inc_progress(job["id"], 10)

    pipeline = MediaPipeline(job)
    job = pipeline.run()

    MediaJobState.queue().finish(job["id"], job)


def __START_SCIVEO_MEDIA_SERVER__():
  daemons = [
    MaintenanceDaemon(period=3600, run_period_files=24, retention_period_files=30),
    MediaJobQueueDaemon(),
  ]

  for daemon in daemons:
    daemon.start()

  while(True):
    time.sleep(12 * 3600)

if __name__ == "__main__":
  __START_SCIVEO_MEDIA_SERVER__()
