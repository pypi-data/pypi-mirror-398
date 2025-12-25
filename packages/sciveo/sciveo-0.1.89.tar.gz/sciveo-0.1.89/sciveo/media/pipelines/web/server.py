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
import json

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
import uvicorn

from sciveo.tools.logger import *
from sciveo.tools.daemon import *
from sciveo.media.pipelines.job_daemon import *
from sciveo.media.pipelines.pipeline import *
from sciveo.media.pipelines.queues import MediaJobState


def check_auth(auth_key):
  if auth_key != os.environ['AUTH_KEY_MEDIA_PIPELINES_WEB']:
    raise Exception("no access, auth key invalid")

class JobData(BaseModel):
  auth_token: str
  data: Optional[Dict]


app = FastAPI()

@app.get("/")
async def index():
  return HTMLResponse(
      """
        <html>
          <head>
            <title>SMIVEO</title>
          </head>
          <body>
            <div>SMIVEO</div>
          </body>
        </html>
      """
  )

@app.get("/job/{job_id}")
async def job_info(job_id: int, auth_token: str, data: Union[str, None] = None):
  try:
    check_auth(auth_token)
    data = json.loads(data)
    return {"job": job_id, "data": data}
  except Exception as e:
    exception(e, "job_info")
    return {"error": str(e)}

@app.post("/job")
async def job_start(auth_token: str, job: Union[Dict, None] = None):
  try:
    check_auth(auth_token)
    debug("job_start", job.data)
    JobQueueDaemon.queue.push(job.data)
    return {"job": job.data}
  except Exception as e:
    exception(e, "job_start")
    return {"error": str(e)}


class WebMediaPipelinesDaemon(DaemonBase):
  def __init__(self, host="0.0.0.0", port=8001):
    super().__init__()
    self.host = host
    self.port = port

  def run(self):
    info("FastAPI", self.host, self.port)
    uvicorn.run(app, host=self.host, port=self.port, log_level="warning")

  def info(self):
    return "web media pipelines (FastAPI )"


if __name__ == "__main__":

  daemons = [
    JobQueueDaemon(os.environ["WEB_MEDIA_PIPELINES_TMP_PATH"]),
    WebMediaPipelinesDaemon(port=os.environ["WEB_MEDIA_PIPELINES_PORT"])
  ]

  for daemon in daemons:
    debug("start", type(daemon).__name__)
    daemon.start()

  while(True):
    time.sleep(300)
    debug("jobs queue size", JobQueueDaemon.queue.size())
    debug("running_jobs queue size", MediaJobState.queue().size())
    # debug("running_jobs queue", MediaJobState.queue().data())
