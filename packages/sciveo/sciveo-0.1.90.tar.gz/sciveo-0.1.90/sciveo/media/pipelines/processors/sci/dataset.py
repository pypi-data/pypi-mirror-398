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

import pandas as pd

from sciveo.media.pipelines.processors.sci.base import *


class ProjectDatasetPlots(SciBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.s3 = boto3.client('s3')
    self.default.update({
      "x_col": None,
      "time_column": None,
      "time_format": "%Y-%m-%d %H:%M:%S",
      "plots": [],
      "fft_plots": [],
      "plot_from": 0,
      "plot_to": -1
    })

  def process(self, content):
    try:
      if self.job['content_type'] == "project":
        project_path = os.path.join(self.base_tmp_path, "projects", self.job['content_id'])
        mkdirs(project_path)

        # Datasets with S3 located files
        if "bucket" in content and "key" in content:
          remote_path = f"{content['owner']}/{content['key']}"
          local_file_name = content['key'].replace("/", "-")
          local_path = os.path.join(project_path, local_file_name)

          if os.path.isfile(local_path):
            debug("SKIP", local_path)
          else:
            debug("Dataset S3 DWN", content["bucket"], remote_path, local_path)
            self.s3.download_file(content["bucket"], remote_path, local_path)

          file_name, file_extension = os.path.splitext(local_file_name)

          # Process CSV files
          if file_extension == ".csv":
            df = pd.read_csv(local_path)
            # Time Series
            debug(f"time_column[{self['time_column']}] time_format[{self['time_format']}]")
            if self["time_column"] is not None:
              df[self["time_column"]] = pd.to_datetime(df[self["time_column"]], format=self["time_format"])
              df = df.set_index(self["time_column"]).sort_index()

              # Plot FFT
              for y_col in self["fft_plots"]:
                try:
                  self.content_next_df_fft(content, df, y_col, project_path)
                except Exception as e:
                  exception(e)

            else:
              x_col = content['data'].get("dataset", {}).get("x_col", self["x_col"])
              df.set_index(x_col)

            list_plots =  content['data'].get("render", {}).get("plots", self["plots"])
            debug("plots", list_plots)
            for y_col in list_plots:
              try:
                self.content_next_df_plot(content, df[self["plot_from"]:self["plot_to"]], y_col, project_path, "time series")
              except Exception as e:
                exception(e)

            text = f"""
              <h3 class='sci-section'>Shape {df.shape}</h3>
              <h2 class='sci-section'>head/tail of dataset</h2>
              <div>{self.df_to_html(pd.concat([df.head(), df.tail()]))}</div>
              <h2 class='sci-section'>describe of dataset</h2>
              <div>{self.describe_df(df)}</div>
            """
            content.setdefault("next", [])
            text_content = self.content_text(content, "dataset plots and tables", text)
            content["next"].append(text_content)

          MediaJobState.queue().inc_progress(self.job["id"], 10)
    except Exception as e:
      exception(e)
    return content

  def content_type(self):
    return "dataset"

  def name(self):
    return "project-datasets-plots"
