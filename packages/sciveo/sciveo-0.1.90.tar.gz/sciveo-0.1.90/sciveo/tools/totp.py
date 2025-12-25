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


import os
import hmac
import base64
import struct
import hashlib
import time

from sciveo.tools.logger import *


class AuthTOTP:
  def __init__(self, secret: str, interval: int = 30, digits: int = 6, algo=hashlib.sha1):
    """
    secret: the private key
    interval: time step in seconds (default 30)
    digits: number of digits in code (default 6)
    algo: hash function (default SHA1, per RFC 6238)
    """
    self.secret = secret
    self.interval = interval
    self.digits = digits
    self.algo = algo

  @staticmethod
  def new_private_key(length: int = 20) -> str:
    """
    Generate a new Base32 secret key.
    """
    raw = os.urandom(length)
    return base64.b32encode(raw).decode("utf-8").replace("=", "")

  def _generate_otp(self, for_time: int) -> int:
    """
    Internal: generate OTP for given time counter.
    """
    pad_len = (8 - len(self.secret) % 8) % 8
    secret_padded = self.secret + ("=" * pad_len)
    key = base64.b32decode(secret_padded, casefold=True)

    counter = struct.pack(">Q", for_time)
    hmac_digest = hmac.new(key, counter, self.algo).digest()

    offset = hmac_digest[-1] & 0x0F
    code = struct.unpack(">I", hmac_digest[offset:offset+4])[0] & 0x7FFFFFFF
    return code % (10 ** self.digits)

  def next_token(self, for_time: int = None) -> str:
    """
    Return the TOTP token for current (or given) time.
    """
    if for_time is None:
      for_time = int(time.time())
    counter = for_time // self.interval
    return str(self._generate_otp(counter)).zfill(self.digits)

  def verify_token(self, token: str, for_time: int = None, window: int = 1) -> bool:
    """
    Verify a token, allowing ±window intervals (to handle clock skew).
    """
    if for_time is None:
      for_time = int(time.time())
    counter = for_time // self.interval
    for delta in range(-window, window + 1):
      candidate = str(self._generate_otp(counter + delta)).zfill(self.digits)
      # debug("verify", token, "delta", delta, "candidate", candidate)
      if hmac.compare_digest(candidate, token):
        return True
    return False
