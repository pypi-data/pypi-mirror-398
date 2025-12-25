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

import random
import string
import datetime
import uuid


def new_guid_uuid():
  return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4()).replace("-", "")

def random_token(num_characters):
  characters = string.ascii_letters + string.digits
  return ''.join(random.choices(characters, k=num_characters))

def new_guid(num_characters=32):
  return datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + random_token(num_characters)


def random_password(length):
  lower = string.ascii_lowercase
  upper = string.ascii_uppercase
  digits = string.digits
  special = '!@#$%&'

  # Ensure the password contains at least one character from each set
  password = [
    random.choice(lower),
    random.choice(upper),
    random.choice(digits),
    random.choice(special)
  ]

  all_chars = lower + upper + (2 * digits) + (3 * special)
  password += random.choices(all_chars, k=length - 4)
  random.shuffle(password)
  return ''.join(password)
