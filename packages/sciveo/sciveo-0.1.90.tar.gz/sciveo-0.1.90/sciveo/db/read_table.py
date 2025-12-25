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
import json
import psycopg2
import numpy as np
import pandas as pd
from sciveo.tools.logger import *


class BaseTable:
  def __init__(self, table_name, config=None, batch_size=10_000, save_path=None, id_col="id"):
    self.table_name = table_name
    self.batch_size = batch_size
    self.save_path = save_path
    self.id_col = id_col
    self.last_id = None

    if config is None:
      self.config = {
        'dbname':   os.environ.get('DB_NAME'),
        'user':     os.environ.get('DB_USERNAME'),
        'password': os.environ.get('DB_PASSWORD'),
        'host':     os.environ.get('DB_HOST', 'localhost'),
        'port':     int(os.environ.get('DB_PORT', 5432)),
      }
    else:
      self.config = config

    self.conn = psycopg2.connect(**self.config)
    self.cursor = self.conn.cursor()
    self.df = pd.DataFrame()

  def load_file(self, file_path=None):
    if not os.path.exists(file_path):
      warning(f"File not found: {file_path}")
      self.latest_df = pd.DataFrame()
      return self.latest_df

    if file_path.endswith(".parquet"):
      self.latest_df = pd.read_parquet(file_path)
    else:
      self.latest_df = pd.read_csv(file_path)
    info(f"Loaded {len(self.latest_df)} records from {file_path}")
    return self.latest_df

  def load(self, base_path=None):
    if base_path is None and self.save_path is not None:
      base_path = self.save_path

    if base_path is None:
      self.df = pd.DataFrame()
      return self.df

    files = [os.path.join(base_path, f) for f in os.listdir(base_path) if f.startswith(self.table_name) and f.endswith(".parquet")]

    if not files:
      info(f"There are no files in {base_path} to read")
      self.df = pd.DataFrame()
      return self.df

    dfs = []
    for file_path in sorted(files):
      try:
        df_part = self.load_file(file_path)
        from_id = int(df_part[self.id_col].min())
        to_id = int(df_part[self.id_col].max())
        dfs.append(df_part)
        debug(f"Loaded {len(df_part)} records from {file_path} id: [{from_id} - {to_id}]")
      except Exception as e:
        warning(f"Failed to load {file_path}: {e}")

    if dfs:
      self.df = pd.concat(dfs, ignore_index=True)
    else:
      self.df = pd.DataFrame()

    self.last_id = int(self.df[self.id_col].max()) if not self.df.empty else None

    info(f"Total loaded records: {len(self.df)} last_id: {self.last_id}")
    return self.df

  def _sanitize_df(self, df):
    PANDAS_MIN_YEAR = 1677
    PANDAS_MAX_YEAR = 2262
    datetime_cols = []

    # datetime cleanup
    for col in df.columns:
      if pd.api.types.is_datetime64_any_dtype(df[col]) or 'date' in col.lower() or 'time' in col.lower():
        datetime_cols.append(col)

    for col in datetime_cols:
      def safe_dt(x):
        if pd.isna(x):
          return pd.NaT
        if isinstance(x, str):
          return pd.to_datetime(x, errors='coerce')
        if hasattr(x, 'year'):
          year = x.year
        else:
          return pd.NaT
        if PANDAS_MIN_YEAR <= year <= PANDAS_MAX_YEAR:
          return pd.Timestamp(x)
        return pd.NaT
      df[col] = df[col].apply(safe_dt)

    # drop rows with invalid datetime
    df = df.dropna(subset=datetime_cols)

    # object columns: convert dict/list to JSON string
    for col in df.columns:
      if df[col].dtype == object:
        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else str(x) if x is not None else None)

    df = df.reset_index(drop=True)
    return df

  def fetch_next_batch(self, last_id=None):
    query = f"SELECT * FROM {self.table_name}"
    if last_id is not None:
      query += f" WHERE id > {last_id}"
    query += f" ORDER BY id ASC LIMIT {self.batch_size};"

    self.cursor.execute(query)
    rows = self.cursor.fetchall()
    if not rows:
      return pd.DataFrame()

    colnames = [desc[0] for desc in self.cursor.description]
    df_new = pd.DataFrame(rows, columns=colnames)
    return self._sanitize_df(df_new)

  def append(self, df_new):
    if not df_new.empty:
      self.df = pd.concat([self.df, df_new], ignore_index=True)
      debug(f"Added {len(df_new)} new rows (total {len(self.df)})")
    self.last_id = int(self.df[self.id_col].max()) if not self.df.empty else None
    debug(f"last {self.id_col} [{self.last_id}]")

  def sync_incremental(self, last_id=None):
    if last_id is None:
      last_id = int(self.df[self.id_col].max()) if not self.df.empty else None
    debug("reading from", last_id)
    df_new = self.fetch_next_batch(last_id)
    self.append(df_new)
    if df_new.empty:
      info("No new rows found")
    return df_new

  def save(self, file_path=None):
    if self.latest_df.empty:
      info("Empty", self.latest_df)
      return

    if self.save_path is not None and self.last_id is not None:
      from_id = int(self.latest_df[self.id_col].min())
      to_id = int(self.latest_df[self.id_col].max())
      file_path = os.path.join(self.save_path, f"{self.table_name}--{from_id}-{to_id}.parquet")

    if file_path.endswith(".parquet"):
      self.latest_df.to_parquet(file_path, index=False)
    else:
      self.latest_df.to_csv(file_path, index=False)
    info(f"Saved {len(self.latest_df)} rows to {file_path}")

  def update(self, last_id=None):
    if self.df.empty:
      self.load()
    self.latest_df = self.sync_incremental(last_id=last_id)
    self.save()
    return self.latest_df

  def close(self):
    self.cursor.close()
    self.conn.close()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
