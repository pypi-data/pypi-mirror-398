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

import re

from sciveo.tools.logger import *


class BPETokenizer:
  def __init__(self, max_size):
    self.initial_tokens = 256
    self.max_size = max_size
    self.max_merges = max_size - self.initial_tokens
    self.vocab = {}
    self.merges = {}

  def encode(self, text):
    tokens = list(map(int, text.encode("utf-8")))
    l1 = len(tokens)
    for k, v in self.merges.items():
      self.merge(tokens, k, v)
    debug(f"encoded ratio {len(tokens) / l1:.2}x")
    return tokens

  def decode_token(self, token):
    if token not in self.vocab:
      return [token]

    bigram = self.vocab[token]
    return self.decode_token(bigram[0]) + self.decode_token(bigram[1])

  def decode(self, tokens):
    decoded = []
    for token in tokens:
      decoded += self.decode_token(token)
    return bytes(decoded).decode("utf-8", errors="replace")

  def train(self, text, debug_step=100):
    tokens = list(map(int, text.encode("utf-8")))
    token_id = self.initial_tokens
    debug("max_merges", self.max_merges)
    while(len(self.merges) < self.max_merges):
      current_counts = self.counts(tokens)
      bigram = max(current_counts, key=current_counts.get)
      self.merge(tokens, bigram, token_id)
      self.merges[bigram] = token_id
      self.vocab[token_id] = bigram
      token_id += 1
      if len(self.merges) % debug_step == 0:
        debug("train", f"{len(self.merges)}/{self.max_merges}")

  def fit(self, x):
    return self.train(x)

  def counts(self, tokens):
    result = {}
    for bigram in zip(tokens, tokens[1:]):
      result.setdefault(bigram, 0)
      result[bigram] += 1
    return result

  def merge(self, tokens, bigram, token_id):
    i = 0
    while i < len(tokens) - 1:
      if tokens[i] == bigram[0] and tokens[i + 1] == bigram[1]:
        tokens[i] = token_id
        del tokens[i + 1]
      i += 1
