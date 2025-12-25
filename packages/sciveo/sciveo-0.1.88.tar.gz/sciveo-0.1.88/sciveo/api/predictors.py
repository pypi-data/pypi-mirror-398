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
from sciveo.tools.timers import Timer
from sciveo.tools.configuration import GlobalConfiguration


class Predictors:
  instance = None

  def __init__(self, predictors=None):
    if predictors is not None:
      self.list_predictors = predictors
    else:
      from sciveo.ml.images.embeddings import ImageEmbedding
      from sciveo.ml.nlp.embeddings import TextEmbedding
      self.list_predictors = {
        "TextEmbedding": TextEmbedding(),
        "ImageEmbedding": ImageEmbedding(),
      }

    self.stats = {}

  @staticmethod
  def get():
    if Predictors.instance is None:
      Predictors.instance = Predictors(GlobalConfiguration.get().data.get("API_PREDICTORS", None))
    return Predictors.instance

  @staticmethod
  def set(predictors):
    Predictors.instance = predictors

  def predict(self, predictor_name, X):
    t = Timer()
    predicted = self.list_predictors[predictor_name].predict(X)
    self.stats.setdefault(predictor_name, {"elapsed": 0.0, "count": 0})
    self.stats[predictor_name]["elapsed"] += t.stop()
    self.stats[predictor_name]["count"] += len(X)
    return predicted

  def train(self, predictor_name, X, Y_true=None):
    t = Timer()
    result = self.list_predictors[predictor_name].train(X, Y_true)
    self.stats.setdefault(predictor_name, {"elapsed": 0.0, "count": 0})
    self.stats[predictor_name]["elapsed"] += t.stop()
    self.stats[predictor_name]["count"] += len(X)
    return result

  def describe(self):
    result = []
    for k, v in self.list_predictors.items():
      result.append([k, v.describe(), self.stats.get(k, "")])
    return result

  def print(self):
    for k, v in self.list_predictors.items():
      info("predictor", k, v.describe())
