#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2025
#

import time
import psutil

from sciveo.tools.logger import *
from sciveo.monitoring.watchdog.base import BaseWatchDogDaemon


class ProcessWatchDogDaemon(BaseWatchDogDaemon):
  def __init__(self, pid=None, process_cmd=None, period=5, command="echo '⚠️ process error!'", thread_inactive_threshold=None):
    self.process_cmd = process_cmd
    self.info_threads = {}
    self.thread_inactive_threshold = thread_inactive_threshold
    super().__init__(threshold_percent=10, period=period, command=command, monitored="Process", monitor_value="is dead")

    self.this_pid = psutil.Process().pid
    self.pids = self.get_pids_by_cmd()
    if pid is not None:
      self.pids.append(pid)

  def get_pids_by_cmd(self):
    matched_pids = []
    if self.process_cmd is not None:
      for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        if proc.info["pid"] == self.this_pid:
          continue
        try:
          cmdline = " ".join(proc.info["cmdline"])
          if self.process_cmd in cmdline:
            matched_pids.append(proc.info["pid"])
        except Exception:
          continue
      info(f"processes matching [{self.process_cmd}]", matched_pids)
    return matched_pids

  def get_threads(self, process, pid):
    current_time = time.time()
    for t in process.threads():
      cpu_time = t.user_time + t.system_time

      self.info_threads.setdefault(pid, {})
      self.info_threads[pid].setdefault(t.id, {
        "id": t.id,
        "start_at": current_time,
        "last_active": current_time,
        "last_cpu": cpu_time,
        "last_check": current_time
      })

      if cpu_time != self.info_threads[pid][t.id]["last_cpu"]:
        self.info_threads[pid][t.id]["last_active"] = current_time
      self.info_threads[pid][t.id]["last_cpu"] = cpu_time
      self.info_threads[pid][t.id]["last_check"] = current_time

  def check_threads(self, process, pid):
    current_time = time.time()
    delete_thread_info = []
    for tid, thr in self.info_threads[pid].items():
      check_time = int(current_time - thr["last_check"])
      if check_time > 1.5 * self.period:
        delete_thread_info.append(tid)
        continue
      elapsed_time = int(current_time - thr["last_active"])
      if elapsed_time > self.thread_inactive_threshold:
        warning(f"⚠️ process[{pid}] thread[{tid}] inactive for {elapsed_time}s.")
    for tid in delete_thread_info:
      self.info_threads[pid].pop(tid, None)

  def process_value(self, pid):
    try:
      p = psutil.Process(pid)
      if p.is_running():
        if p.status() != psutil.STATUS_ZOMBIE:

          if self.thread_inactive_threshold is not None:
            try:
              self.get_threads(p, pid)
              self.check_threads(p, pid)
            except psutil.NoSuchProcess as e:
              exception(e, pid)

          return 0
        else:
          return 50
    except psutil.NoSuchProcess:
      pass
    return 100

  def value(self):
    pv = 0.0
    for pid in self.pids:
      pv += self.process_value(pid)
    return {"percent": pv}


if __name__ == '__main__':
  daemons = [
    ProcessWatchDogDaemon(pid=87443, thread_inactive_threshold=10),
    ProcessWatchDogDaemon(process_cmd="sciveo monitor", thread_inactive_threshold=10),
  ]
  for d in daemons:
    d.start()

  while(True):
    time.sleep(30)