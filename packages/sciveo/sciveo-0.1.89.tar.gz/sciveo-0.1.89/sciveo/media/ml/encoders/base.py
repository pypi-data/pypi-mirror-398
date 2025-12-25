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


class BaseEncoder:
  def fit(self, X):
    pass

  def transform(self, X):
    pass

  def fit_transform(self, X):
    pass

  def inverse(self, X):
    pass