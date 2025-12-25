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

from sciveo.tools.logger import *
from sciveo.tools.configuration import GlobalConfiguration


class BaseML:
  def __init__(self, model_name="base", cache_dir=None, device=None) -> None:
    self.model_name = model_name
    self.config = GlobalConfiguration.get()

    if cache_dir is None:
      self.cache_dir = self.config['MODELS_BASE_PATH']
    else:
      self.cache_dir = cache_dir

    if device is None:
      self.device = os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu")
    else:
      self.device = device

    self.init_models()

  def init_models(self):
    debug("init_models not implemented")

  def init(self):
    debug("init not implemented")

  def post_init(self):
    debug("post_init not implemented")

  def predict_one(self, x):
    debug("predict_one not implemented")

  def predict(self, X):
    predictions = []
    for x in X:
      predictions.append(self.predict_one(x))
    return predictions

  def train(self, X, Y_true=None):
    debug("train not implemented")

  def describe(self):
    return f"{type(self).__name__}: {self.model_name}"
