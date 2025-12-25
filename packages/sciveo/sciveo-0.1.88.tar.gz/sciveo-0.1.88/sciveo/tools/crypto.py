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

import json
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from sciveo.tools.logger import *


class CryptoJsonData:
  def __init__(self, base64_key=None) -> None:
    if base64_key is None:
      self.gen_key()
    else:
      self.key = base64.b64decode(base64_key)

  def get_key(self):
    return base64.b64encode(self.key).decode("utf-8")

  def gen_key(self):
    self.key = get_random_bytes(32)
    return self.get_key()

  def read_key(self, key_path):
    with open(key_path, 'rb') as fp:
      self.key = fp.read(32)

  def write_key(self, key_path):
    with open(key_path, 'wb') as fp:
      fp.write(self.key)

  def encrypt(self, plaintext, mode=AES.MODE_GCM):
    iv = get_random_bytes(12)
    cipher = AES.new(self.key, mode, nonce=iv)
    data_encrypted, auth_tag = cipher.encrypt_and_digest(plaintext.encode())
    return {
      "encrypted": base64.b64encode(data_encrypted).decode("utf-8"),
      "auth_tag": base64.b64encode(auth_tag).decode("utf-8"),
      "iv": base64.b64encode(iv).decode("utf-8")
    }

  def decrypt(self, cipher_data, mode=AES.MODE_GCM):
    cipher_text = base64.b64decode(cipher_data["encrypted"])
    auth_tag = base64.b64decode(cipher_data["auth_tag"])
    iv = base64.b64decode(cipher_data["iv"])
    cipher = AES.new(self.key,  mode, nonce=iv)
    return cipher.decrypt_and_verify(cipher_text, auth_tag).decode("utf-8")

  def encrypt_json(self, data):
    data = json.dumps(data)
    data = base64.b64encode(data.encode()).decode("utf-8")
    return self.encrypt(data)

  def decrypt_json(self, encrypted_data):
    data = self.decrypt(encrypted_data)
    data = base64.b64decode(data)
    data = json.loads(data)
    return data
