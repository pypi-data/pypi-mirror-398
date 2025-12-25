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

import unittest

from sciveo.common.sampling import RandomSampler
from sciveo.common.configuration import Configuration


class TestConfiguration(unittest.TestCase):
  def test_bool(self):
    c = Configuration({
      "bool": True
    })

    self.assertTrue(str(c) == "{\"bool\": true}")
