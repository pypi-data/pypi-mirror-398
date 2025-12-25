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
import boto3

from sciveo.tools.logger import *
from sciveo.media.pipelines.processors.sci.base import *
from sciveo.media.ml.time_series.predictor import *


class TimeSeriesPredictorProcessor(SciBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.default.update({
      "time_column": "Date Time",
      "time_format": '%d.%m.%Y %H:%M:%S'
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
                x_col = content['data'].get("dataset", {}).get("x_col", self["time_column"])
                df.set_index(x_col, inplace=True)
                dataset_df.append(df)

        dataset_df = pd.concat(dataset_df).drop_duplicates(keep='first').sort_index().reset_index()

        content_project = list_content["project"][0]

        MediaJobState.queue().inc_progress(job["id"], 5)

        if "timeseries" in list_content:
          content_predictor = self.new_content(content_project, "prediction", name=f"Prediction on {dataset_df.shape}")
          next_media.append(content_predictor)

          text_content = self.content_text(content_predictor, "timeseries predictions plots", f"""Time series predictions.\n\n{self.describe_df(dataset_df)}""")
          next_media.append(text_content)

          content = list_content["timeseries"][0]
          remote_path, local_path, local_file_name = self.content_path(content, project_path)
          predictor = TimeSeriesPredictor(local_path)
          ds = TimeSeriesDataSet(dataset_df, self["time_column"], format=self["time_format"])
          predictions, X, x_plot = predictor.predict(ds.data)

          MediaJobState.queue().inc_progress(job["id"], 5)

          columns = predictor.model_data["columns"][:11] # TODO: Should be configurable in the Predictor, so plot only few columns
          plot_progress_inc = 20 / len(columns)
          for i, y_col in enumerate(columns):
            image_content = self.content_image(text_content, y_col, project_path)
            predictor.plot(predictions, X, x_plot, i, image_local_path=image_content["local_path"])
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

  def name(self):
    return "sci-timeseries-predictor"
