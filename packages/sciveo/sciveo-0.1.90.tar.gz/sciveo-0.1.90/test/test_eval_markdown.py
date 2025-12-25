#
# Stanislav Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact s.georgiev@softel.bg.
#
# 2025
#

import math
import unittest

from sciveo.tools.logger import *
from sciveo.ml.evaluation.markdown import *


class TestEvalMarkdown(unittest.TestCase):
  def test_1(self):
    md_true = """
      "# Breaking News"
      "A major fire broke out in the city center."
      "Authorities are investigating the cause."
    """

    md_predicted = """
      "# BREAKING NEWS",
      "A major fire broke out in city center.",
      "Authorities investigate the cause.",
      "Stay tuned for updates."
    """

    em = EvalMarkdown(md_true, md_predicted)
    results = em.evaluate()
    info(results)
    info("Score", em.score())


if __name__ == '__main__':
  unittest.main()