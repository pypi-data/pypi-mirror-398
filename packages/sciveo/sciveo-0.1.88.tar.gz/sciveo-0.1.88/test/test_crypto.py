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

from sciveo.tools.crypto import *


class TestCrypto(unittest.TestCase):
  def test_string(self):
    c = CryptoJsonData()
    m1 = "test message string encrypt and decrypt"
    m2 = c.decrypt(c.encrypt(m1))
    self.assertEqual(m1, m2)

  def test_json(self):
    c = CryptoJsonData()
    j1 = {"A": 1, "B": []}
    j2 = c.decrypt_json(c.encrypt_json(j1))
    self.assertEqual(json.dumps(j1, sort_keys=True), json.dumps(j2, sort_keys=True))

  def test_big_json(self):
    c = CryptoJsonData()
    j1 = {"test": 1, "L": [1,2,3,4], "W": "A", "B": "C", "D1": {1: 2, 2: 3, 3: 4}, "L2": [[1,2,3], [3,4,5]]}
    j2 = c.decrypt_json(c.encrypt_json(j1))
    self.assertEqual(json.dumps(j1, sort_keys=True), json.dumps(j2, sort_keys=True))

  def test_key(self):
    key = "OZ1IIdAh3b6h+E7fgIGo33rRsNT8Vg428GVC4FAGZGM="
    c = CryptoJsonData(key)
    m1 = "test message string encrypt and decrypt"
    m2 = c.decrypt(c.encrypt(m1))
    self.assertEqual(m1, m2)


if __name__ == '__main__':
    unittest.main()