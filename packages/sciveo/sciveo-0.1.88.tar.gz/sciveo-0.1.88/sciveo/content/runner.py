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

import os

from sciveo.tools.logger import *
from sciveo.common.sampling import RandomSampler, GridSampler, AutoSampler
from sciveo.content.project import RemoteProject, LocalProject


class ProjectRunner:
  current = None

  def __init__(self, project, function, configuration={}, **kwargs):
    self.project_name = project
    self.function = function
    self.kwargs = kwargs

    self.arguments = {
      'count': None,
      'remote': True,
      'sampler': "random",
    }

    self.count = self.get('count')
    remote = self.get('remote')
    sampler = self.get('sampler')

    if remote:
      self.project = RemoteProject(self.project_name)
    else:
      self.project = LocalProject(self.project_name)

    if sampler == "random":
      self.configuration_sampler = RandomSampler(configuration)
    elif sampler == "grid":
      self.configuration_sampler = GridSampler(configuration)
    elif sampler == "auto":
      self.configuration_sampler = AutoSampler(configuration, self.project, **kwargs)
    else:
      self.configuration_sampler = RandomSampler(configuration)

    debug(f"start remote[{remote}] count[{self.count}] sampler[{sampler}]", configuration)

  def get(self, a):
    return self.kwargs.get(a, self.arguments[a])

  def describe(self):
    return {
      "arguments": self.arguments,
      "sampler": self.configuration_sampler.describe()
    }

  def run(self):
    for i, configuration_sample in enumerate(self.configuration_sampler):
      if self.count is not None and i >= self.count:
        break

      self.project.config = configuration_sample
      self.project.config.set_name(f"[{self.project.list_content_size + i + 1}]")
      debug("run", i, self.project.config)
      self.function()
