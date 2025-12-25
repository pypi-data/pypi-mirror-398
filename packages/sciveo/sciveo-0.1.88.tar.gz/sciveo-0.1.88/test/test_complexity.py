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

import math
import unittest

from sciveo.tools.complexity import *


class TestComplexity(unittest.TestCase):
  def _do_test(self, ce):
    self.assertTrue(ce(2e3)[0] == "N")
    self.assertTrue(ce(1e7)[0] == "N^2")
    self.assertTrue(ce(2e4)[0] == "NlogN")

  def test_1(self):
    ce = ComplexityEval(1024)
    self._do_test(ce)

  def test_input(self):
    ce = ComplexityEval(1024)
    self._do_test(ce)
    ce = ComplexityEval([1]*1024)
    self._do_test(ce)


if __name__ == '__main__':
  unittest.main()