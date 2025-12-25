#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2023
#

import threading
import signal
import time

from sciveo.tools.logger import *
from sciveo.tools.synchronized import ListQueue
from sciveo.api.upload import APIFileUploader


class SignalHandler:
  def __init__(self, daemons):
    self.daemons = daemons

    signal.signal(signal.SIGINT, self.handler_int)
    signal.signal(signal.SIGUSR1, self.handler_usr1)

  def handler_int(self, signum, frame):
    info("INT signal received", signum, frame)
    for daemon in self.daemons:
      daemon.stop()

  def handler_usr1(self, signum, frame):
    info("USR1 signal received", signum, frame)


class DaemonBase:
  def __init__(self, num_threads=1, period=0):
    self.is_running = False
    self.is_started = False
    self.num_threads = num_threads
    self.period = period

  def start(self):
    if self.is_started:
      return

    self.is_running = True
    self.is_started = True

    self.threads = []
    for i in range(self.num_threads):
      T = threading.Thread(target = self.safe_run)
      T.setDaemon(True)
      T.start()
      self.threads.append(T)

  def stop(self):
    self.is_running = False

  def finalise(self):
    pass

  def join(self):
    for i in range(self.num_threads):
      self.threads[i].join()

  def loop(self):
    pass

  def run(self):
    while(self.is_running):
      try:
        self.loop()
      except Exception as e:
        exception(e)
      time.sleep(self.period)

  def safe_run(self):
    try:
      self.run()
    except Exception as e:
      exception(e)


class TasksDaemon(DaemonBase):
  current = None
  queue = ListQueue("tasks")

  def loop(self):
    task = TasksDaemon.queue.pop()
    task()


def __upload_content__(content_type, local_path, parent_guid):
  TasksDaemon.queue.push(APIFileUploader(content_type, local_path, parent_guid))