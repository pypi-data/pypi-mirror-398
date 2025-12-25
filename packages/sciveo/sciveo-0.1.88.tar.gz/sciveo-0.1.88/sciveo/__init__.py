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

from builtins import ImportError

try:

  import os
  import time

  from sciveo.tools.logger import *
  from sciveo.tools.daemon import TasksDaemon, __upload_content__
  from sciveo.content.runner import ProjectRunner
  from sciveo.content.dataset import Dataset
  from sciveo.version import __version__


  TasksDaemon.current = TasksDaemon(num_threads=int(os.environ.get("SCIVEO_TASKS_NUM_THREADS", 1)))


  # New Experiment
  def open():
    if ProjectRunner.current is not None:
      return ProjectRunner.current.project
    else:
      error("there is no started project")

  def start(project, function, configuration={}, **kwargs):
    TasksDaemon.current.start()
    ProjectRunner.current = ProjectRunner(project=project, function=function, configuration=configuration, **kwargs)
    ProjectRunner.current.run()

  # Dataset info
  def dataset(info={}):
    return Dataset.get(info)

  # Monitoring start
  def monitor(**kwargs):
    from sciveo.monitoring.start import MonitorStart
    MonitorStart(**kwargs)()

  # Network tools
  def network(**kwargs):
    from sciveo.network.tools import NetworkTools
    return NetworkTools(**kwargs)

except ImportError as e:
  pass