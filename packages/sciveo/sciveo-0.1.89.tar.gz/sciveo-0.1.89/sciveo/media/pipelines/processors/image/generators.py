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
import cv2
import gc
from PIL import Image

import torch
from diffusers import StableDiffusionPipeline, LMSDiscreteScheduler
from diffusers import StableDiffusionInstructPix2PixPipeline, EulerAncestralDiscreteScheduler
from transformers import AutoProcessor, AutoModelForCausalLM
from transformers import Blip2Processor, Blip2ForConditionalGeneration

from sciveo.tools.logger import *
from sciveo.tools.common import *
from sciveo.media.pipelines.processors.tpu_base import *
from sciveo.media.pipelines.base import ApiContent
from sciveo.ml.images.description import ImageToText


class ImageDiffusionText(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "prompt": "monkeys eating bananas and watching football",
      "iterations": 50,
      "model_version": 1,
      "dtype": 1,
      "width": 512,
      "height": 512,
      "num_images": 1,
      "bucket": "smiveo-images"
    })

    self.max_batch_size = 3 # GPU memory dependent
    self.width = self.get("width", 128, 512)
    self.height = self.get("height", 128, 512)

    cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")

    model_names = ["softel/stable-diffusion-v1.0", "softel/stable-diffusion-v1.1"]
    torch_dtypes = [torch.float16, torch.float32]

    model_name = model_names[max(0, min(len(model_names) - 1, self["model_version"]))]
    torch_dtype = torch_dtypes[max(0, min(len(torch_dtypes) - 1, self["dtype"]))]
    TPU = os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu")

    debug("init", model_name, torch_dtype, "on", TPU)

    # TODO: Add scheduler config param
    lms = LMSDiscreteScheduler(
      beta_start=0.00085,
      beta_end=0.012,
      beta_schedule="scaled_linear"
    )

    self.pipe = StableDiffusionPipeline.from_pretrained(
      model_name,
      scheduler=lms,
      torch_dtype=torch_dtype,
      cache_dir=cache_dir
    ).to(TPU)

    self.progress_per_media = self.max_batch_size * self.max_progress / self["iterations"] / self["num_images"]

  def on_progress(self, step, timestep, latents):
    debug("progress", step)
    MediaJobState.queue().inc_progress(self.job_id, self.progress_per_media)

  def generate(self, image_local_paths):
    image_samples = self.pipe(
      prompt=self["prompt"],
      width=self.width,
      height=self.height,
      num_inference_steps=self.get("iterations", 10, 300),
      num_images_per_prompt=len(image_local_paths),
      callback_steps=1,
      callback=self.on_progress
    )

    for i, image in enumerate(image_samples["images"]):
      debug("generate save", i, image_local_paths[i])
      image.save(image_local_paths[i])

    del image_samples

  def run(self, job, input):
    self.job_id = job["id"]
    parent_guid = job['content_id']

    next_media = {
      "media": [],
      "guid": [],
      "key": [],
      "local_path": []
    }

    for i in range(self.get("num_images", 1, 33)):
      # guid = f"{self.name()}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{parent_guid}"
      guid = self.new_guid()
      key = f"{guid}.jpg"
      next_media["key"].append(key)
      next_media["guid"].append(guid)
      next_media["local_path"].append(os.path.join(self.base_tmp_path, key))

    list_local_paths = [next_media["local_path"][i : i + self.max_batch_size] for i in range(0, len(next_media["local_path"]), self.max_batch_size)]
    debug("run list_local_paths", list_local_paths)
    for local_paths in list_local_paths:
      self.generate(local_paths)

    for i, guid in enumerate(next_media["guid"]):
      media = {
        "guid": guid,
        "parent": parent_guid,
        "content_type": "image",
        "owner": job["owner"],
        "name": f"[{self['prompt']}] {self['iterations']}",
        "local_path": next_media["local_path"][i],
        "w": self.width, "h": self.height,
        "height": self.height,
        "key": next_media["key"][i],
        "bucket": self["bucket"],
        "processor": self.name(),
        "layout": {"name": self.name(), "height": self.height, **self["layout"]}
      }

      if self["output"]:
        job["output"].append(media)
      if self["append-content"]:
        job["append-content"].append(media)
      next_media["media"].append(media)

    return next_media["media"]

  def content_type(self):
    return "image"

  def name(self):
    return "image-diffusion"

  def is_append_processor(self):
    return False


class ImageToTextProcessor(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)

    self.api = ApiContent()

    self.cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")
    self.device = os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu")

    self.default.update({
      "max_length": 64,
      "model_id": 0,
      "output": False
    })

    self.predictor = None

  def process(self, media):
    debug("process", media['guid'])
    if self.predictor is None:
      self.predictor = ImageToText(self['model_id'], self['max_length'], self.cache_dir, self.device)
    local_path = media["local_path"]
    predict = self.predictor.predict_one(local_path)
    return self.set_media(media, predict)

  def set_media(self, media, predict):
    media.setdefault("next", [])
    media["next"].append({
      "guid": f"TXT-{media['guid']}",
      "parent": media['guid'],
      "content_type": "comment",
      "content_text": predict,
      "owner": media["owner"],
      "name": f"{predict} [{self['max_length']}]",
      "processor": self.name()
    })

    self.api.update(media, {"description": predict})

    return media

  def content_type(self):
    return "image"

  def name(self):
    return "image-to-text"

  def is_append_processor(self):
    return True


class ImageDiffusionImageText(TPUBaseProcessor):
  def __init__(self, processor_config, max_progress) -> None:
    super().__init__(processor_config, max_progress)
    self.default.update({
      "prompt": "monkeys eating bananas and watching football",
      "iterations": 10,
      "dtype": 0,
      "max_dim": 512,
      # "num_images": 1,
      "bucket": "smiveo-images"
    })

    self.max_batch_size = 1 # GPU memory dependent
    self.max_dim = self.get("max_dim", 128, 512)

    cache_dir = os.path.join(os.environ['MEDIA_MODELS_BASE_PATH'], "models/")

    torch_dtypes = [torch.float16, torch.float32]
    model_name = "softel/image-instruct-v1.0"
    torch_dtype = torch_dtypes[max(0, min(len(torch_dtypes) - 1, self["dtype"]))]
    TPU = os.environ.get("MEDIA_PROCESSING_BACKEND", "cpu")

    debug("init", model_name, torch_dtype, "on", TPU)

    self.pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(
      model_name,
      torch_dtype=torch_dtype,
      safety_checker=None,
      cache_dir=cache_dir
    ).to(TPU)

    self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipe.scheduler.config)

    self.progress_per_media = self.max_progress / self["iterations"]
    # self.progress_per_media = self.max_batch_size * self.max_progress / self["iterations"] / self["num_images"]

  def on_progress(self, step, timestep, latents):
    debug("progress", step)
    MediaJobState.queue().inc_progress(self.job_id, self.progress_per_media)

  def process(self, media):
    try:
      self.media = media
      self.local_path = self.media["local_path"]
      frame = cv2.imread(self.local_path)

      tag = f"IT2I-{self['prompt'].replace(' ','')[:16]}"
      image_local_path = self.add_suffix_to_filename(self.local_path, tag)

      h, w = get_frame_resolution_max_dim(frame, self.max_dim)
      frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)

      image_samples = self.pipe(
        self["prompt"],
        image=Image.fromarray(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)),
        image_guidance_scale=1,
        num_inference_steps=self.get("iterations", 3, 100),
        num_images_per_prompt=1,
        callback=self.on_progress
      )

      image_samples["images"][0].save(image_local_path)
      del image_samples

      self.next_content(self.media, tag, image_local_path, w=frame_resized.shape[1], h=frame_resized.shape[0], name=f"[{self['prompt']}] {self['iterations']}")
    except Exception as e:
      exception(e, self.media)
    return self.media

  def content_type(self):
    return "image"

  def name(self):
    return "image-diffusion-image-text"

  def is_append_processor(self):
    return False
