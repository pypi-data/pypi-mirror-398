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

import unittest
import json

from sciveo.tools.compress import *


class TestEncoders(unittest.TestCase):
  def test_compress_json(self):
    zip = CompressJsonData()
    j1 = {"AAA": [1, 2, 3], "BBB": {"CCC": 1, "DDD": 2, "EEE": 3}, "CC": 3}
    j2 = zip.decompress(zip.compress(j1))
    self.assertEqual(json.dumps(j1, sort_keys=True), json.dumps(j2, sort_keys=True))


if __name__ == '__main__':
  unittest.main()
