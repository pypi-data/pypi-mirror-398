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

import base64
import requests

from sciveo.tools.logger import *
from sciveo.tools.configuration import GlobalConfiguration
from sciveo.tools.compress import CompressJsonData


class PredictorRemoteClient:
  def __init__(self, url="http://localhost:8901", verify=True, auth_token=None, api_prefix=None):
    debug("init url", url, verify)
    config = GlobalConfiguration.get()
    if auth_token is None:
      auth_token = config["api_auth_token"]
    if api_prefix is None:
      api_prefix = config["api_prefix"]
    self.auth_token = auth_token
    self.api_prefix = api_prefix
    self.url = f"{url}/{self.api_prefix}/predict"
    self.verify = verify
    requests.packages.urllib3.disable_warnings()

  def predict(self, params):
    try:
      debug("predict", params)
      headers = {"Authorization": f"Bearer {self.auth_token}"}
      response = requests.post(self.url, json=params, headers=headers, verify=self.verify)

      if response.status_code == 200:
        data = response.json()

        if params.get("compressed", 0) > 0 and params["predictor"] in data:
          predicted = data[params["predictor"]]
          predicted = CompressJsonData().decompress(predicted)
          data[params["predictor"]] = predicted
      else:
        error(f"Request [{self.url}] failed with status code {response.status_code}")
        data = {"error": response.status_code}
    except Exception as e:
      exception("predict", e)
      data = {"error": str(e)}
    return data

  def image_encoded(self, image=None, resize_to=(256, 256), local_path=None):
    import cv2
    if local_path is not None:
      image = cv2.imread(local_path)
    if resize_to is not None:
      image = cv2.resize(image, resize_to)
    buffer = cv2.imencode('.jpg', image)[1].tobytes()
    return base64.b64encode(buffer).decode('utf-8')

  def predict_image_embedding(self, image=None, resize_to=(256, 256), local_path=None):
    image_base64 = self.image_encoded(image=image, resize_to=resize_to, local_path=local_path)
    params = {
      'predictor': 'ImageEmbedding', 'compressed': 1,
      'X': [image_base64]
    }
    r = self.predict(params=params)
    return r[params["predictor"]][0]
