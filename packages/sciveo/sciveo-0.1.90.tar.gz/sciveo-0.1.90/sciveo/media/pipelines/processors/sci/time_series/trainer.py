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

import os
import pandas as pd
import tensorflow as tf
from tensorflow.keras.callbacks import Callback

from sciveo.tools.logger import *
from sciveo.media.pipelines.processors.sci.base import *
from sciveo.media.ml.time_series.predictor import *
from sciveo.media.ml.time_series.trainer import *


class TrainerProgressCallback(Callback):
  def __init__(self, job, epochs, max_progress):
    self.job = job
    self.progress_per_epoch = 2 * max_progress / epochs

  def on_epoch_end(self, epoch, logs=None):
    debug("epoch", epoch, "finished")
    MediaJobState.queue().inc_progress(self.job["id"], self.progress_per_epoch)


class TimeSeriesTrainerProcessor(SciBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.default.update({
      "model_name": "none",
      "time_column": "Date Time",
      "time_format": '%d.%m.%Y %H:%M:%S',
      "ratios": [["train", 0.70], ["val", 0.20], ["test", 0.10]],
      "max_epochs": 20, "patience": 2,
      "window_size": 24,
      "test_plot_from": 200, "test_plots": 20, "test_plot_column_id": 1
    })

  def run(self, job, input):
    progress_per_media = self.max_progress / max(1, len(input))
    debug("run", job["id"], progress_per_media, "input", input)
    next_media = []
    try:
      if job['content_type'] == "project":
        project_path = os.path.join(self.base_tmp_path, "projects", job['content_id'])
        mkdirs(project_path)

        self.download_content(job, project_path)
        MediaJobState.queue().inc_progress(job["id"], 10)

        list_content = {}

        dataset_df = []
        for content in job['content']:
          list_content.setdefault(content["content_type"], []).append(content)

          if content["content_type"] == "file":
            if content['key'].split(".")[-1] == "timeseries":
              list_content.setdefault("timeseries", []).append(content)

          if content["content_type"] == "dataset":
            # Datasets with S3 located files
            if "bucket" in content and "key" in content:
              remote_path, local_path, local_file_name = self.content_path(content, project_path)
              file_extension = local_file_name.split(".")[-1]

              if file_extension == "csv":
                df = pd.read_csv(local_path)
                x_col = content['data'].get("dataset", {}).get("x_col", df.keys()[0])
                df.set_index(x_col, inplace=True)
                dataset_df.append(df)

        dataset_df = pd.concat(dataset_df).drop_duplicates(keep='first').sort_index().reset_index()

        content_project = list_content["project"][0]
        MediaJobState.queue().inc_progress(job["id"], 5)

        if len(dataset_df) > 0:
          content_trainer = self.new_content(content_project, "training", name=f"Training on {dataset_df.shape}")
          next_media.append(content_trainer)

          ds = TimeSeriesDataSet(dataset_df, self["time_column"], format=self["time_format"])
          ds.normalize()
          ds.split(ratios=self["ratios"])

          trainer = TimeSeriesTrainer(ds, self["window_size"], self["window_size"], self["window_size"])
          trainer.create()
          progress_callback = TrainerProgressCallback(job, self["max_epochs"], 50)
          history = trainer.train(self["max_epochs"], self["patience"], progress_callback)
          trainer_eval = trainer.evaluate()

          model_name, model_path = trainer.save(project_path, self["model_name"])

          model_data = {
            "eval": trainer_eval,
            "history": {
              "loss": history.history["loss"],
              "val_loss": history.history["val_loss"]
            }
          }

          model_content = self.content_file(content_trainer, model_name, model_path, data=model_data)
          next_media.append(model_content)

          text = f"""
            Time series model.
            ....
            ....
            model name {model_name}
            model size {os.path.getsize(model_path)}

            eval
            {self.df_to_html(pd.DataFrame(trainer_eval))}

            train loss
            {self.df_to_html(pd.DataFrame({"loss": history.history["loss"], "val_loss": history.history["val_loss"]}))}
          """
          text_content = self.content_text(content_trainer, "Train timeseries model", text)
          next_media.append(text_content)

          # TODO: Create numeric from history.history["loss"], history.history["val_loss"]

          ds.denormalize("test")
          predictor = TimeSeriesPredictor(model_path)

          # Plot some test predictions
          columns = predictor.model_data["columns"]
          plot_progress_inc = 10 / self["test_plots"]
          y_col = columns[self["test_plot_column_id"]]
          for i in range(self["test_plot_from"], self["test_plot_from"] + self["test_plots"]):
            image_content = self.content_image(text_content, y_col, project_path)
            self.plot_chunk(ds.dataset["test"], predictor, i, self["test_plot_column_id"], image_content["local_path"])
            image_content["data"] = {
              "info": {
                "size": os.path.getsize(image_content["local_path"]),
                "plot": y_col
              }
            }
            next_media.append(image_content)
            MediaJobState.queue().inc_progress(job["id"], plot_progress_inc)

      MediaJobState.queue().inc_progress(job["id"], 10)

      if self["output"]:
        job["output"] += next_media
      if self["append-content"]:
        job["append-content"] += next_media
    except Exception as e:
      exception(e)
    return next_media

  def plot_chunk(self, df, predictor, k, i, image_local_path):
    k += 1
    L = predictor.model_data["window"]["input_width"]
    X = df[-(k + 1)*L:-k*L]

    predictions, X, x_plot = predictor.predict(X)

    idx_from = -k * L
    idx_to = -(k - 1) * L
    if idx_to != 0:
      labels = df[idx_from:idx_to]
    else:
      labels = df[idx_from:]
    labels = labels.values.reshape(X.shape).astype('float32')
    labels = tf.convert_to_tensor(labels)

    predictor.plot(
        predictions, X, x_plot, i, labels,
        image_local_path
    )

  def content_type(self):
    return None

  def name(self):
    return "sci-timeseries-trainer"
