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

import sciveo


class TestRunner(unittest.TestCase):
  def dummy_loop(self):
    with sciveo.open() as E:
      self.assertTrue(E.config.configuration.keys() == self.configuration.keys())

  def test_dummy_train(self):
    self.configuration = {
        "input_window": {
            "values": [10, 20, 30, 40, 50, 100, 200]
        },
        "steps": {
            "min": 1, "max": 100
        },
        "max_epochs": {
            "min": 1, "max": 3
        },
        "patience": {
            "min": 2, "max": 3
        },
        "idx": {
            "seq": 1
        }
    }

    for sampler in ["random", "grid", "auto"]:
      sciveo.start(
        project="SCIVEO Dummy Test",
        configuration=self.configuration,
        function=self.dummy_loop,
        remote=False,
        count=10,
        sampler=sampler
      )

  def test_init_args(self):
    self.configuration = {
      "lr": (1e-5, 1e-6, 11)
    }

    sciveo.start(
        project="test_init_args",
        configuration=self.configuration,
        function=self.dummy_loop,
        remote=False,
        count=10,
        sampler="auto",
        num_random_samples=20,
        next_sample_ratio=0.99,
        min_delta_score=1e-5,
        optimizer="base",
        learning_rate=0.2,
        learning_rate_decay=0.01
      )