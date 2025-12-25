#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2025
#

import time
import unittest

from sciveo.tools.totp import *


class TestTOTP(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.secret = AuthTOTP.new_private_key(length=32)
    cls.auth = AuthTOTP(cls.secret, digits=8)

  def test_pass(self):
    token = self.auth.next_token()
    self.assertTrue(self.auth.verify_token(token=token))

  def test_expiry_time_fail(self):
    auth = AuthTOTP(self.secret, interval=3, digits=8)
    token = auth.next_token()
    self.assertTrue(auth.verify_token(token=token))
    time.sleep(2)
    self.assertTrue(auth.verify_token(token=token))
    time.sleep(2)
    self.assertTrue(auth.verify_token(token=token))
    time.sleep(2)
    self.assertFalse(auth.verify_token(token=token))


if __name__ == '__main__':
  unittest.main()