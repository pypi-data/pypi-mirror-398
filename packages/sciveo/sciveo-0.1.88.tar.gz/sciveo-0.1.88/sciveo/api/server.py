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
import time
from flask import Flask, jsonify, render_template, request, url_for, Response, abort
from waitress import serve

from sciveo.tools.logger import *
from sciveo.tools.daemon import DaemonBase
from sciveo.tools.timers import Timer
from sciveo.tools.compress import CompressJsonData
from sciveo.tools.configuration import GlobalConfiguration
from sciveo.api.predictors import Predictors


CONFIG = GlobalConfiguration.get()
SCI_API_AUTH_TOKEN = CONFIG["api_auth_token"]
SCI_API_PREFIX = CONFIG["api_prefix"]


app = Flask(__name__)


def authenticate():
  token = request.headers.get('Authorization')
  if token != f"Bearer {SCI_API_AUTH_TOKEN}":
    abort(401, 'Unauthorized')

@app.before_request
def before_request_func():
  authenticate()

@app.route(f'/{SCI_API_PREFIX}/predict', methods=['POST'])
def predict_endpoint():
  result = {"error": "invalid data"}
  try:
    if request.is_json:
      data = request.json
      if "predictor" in data and "X" in data:
        t = Timer()
        predicted = Predictors.get().predict(data["predictor"], data["X"])

        if data.get("compressed", 0) > 0:
          predicted = CompressJsonData().compress(predicted)

        result = {
          data["predictor"]: predicted,
          "stats": {
            "elapsed": t.stop(),
            "count": len(data["X"])
          }
        }
  except Exception as e:
    exception("predict_endpoint", e)
  return jsonify(result)


class WebServerDaemon(DaemonBase):
  def __init__(self, host="127.0.0.1", port=8901, predictors=None):
    super().__init__()
    self.host = host
    self.port = port

    if predictors is not None:
      Predictors.set(predictors)

  def run(self):
    info("run", [self.host, self.port])
    Predictors.get().print()

    serve(app, host=self.host, port=self.port, threads=1, connection_limit=10)
