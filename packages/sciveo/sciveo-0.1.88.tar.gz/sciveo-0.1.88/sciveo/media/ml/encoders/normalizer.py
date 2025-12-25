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

from sciveo.media.ml.encoders.base import *


class Normalizer:
  def __init(self):
    self.mean = 0
    self.std = 0

  def fit(self, X):
    self.mean = X.mean(axis=0)
    self.std = X.std(axis=0)

  def transform(self, X):
    return (X - self.mean) / self.std

  def fit_transform(self, X):
    self.fit(X)
    return self.transform(X)

  def inverse(self, X):
    return X * self.std + self.mean