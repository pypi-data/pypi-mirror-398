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

import numpy as np
import cv2


class BaseImageTransformer:
  def __init__(self, param=0):
    self.param = param

  def __call__(self, image, labels=None):
    return image, labels

  def transform(self, image, labels=None):
    return self(image, labels)


class RandomTransformer(BaseImageTransformer):
  def __init__(self, class_name, lower, upper, proba):
    self.class_name = class_name
    self.lower = lower
    self.upper = upper
    self.proba = proba
    self.transformer = class_name(1.0)

  def __call__(self, image, labels=None):
    p = np.random.uniform(0, 1)
    if p >= (1.0 - self.proba):
      self.transformer.param = np.random.uniform(self.lower, self.upper)
      return self.transformer(image, labels)
    else:
      return image, labels


class ConvertColor(BaseImageTransformer):
  def __init__(self, current='RGB', to='HSV', keep_3ch=True):
    if not ((current in {'RGB', 'HSV'}) and (to in {'RGB', 'HSV', 'GRAY'})): raise NotImplementedError
    self.current = current
    self.to = to
    self.keep_3ch = keep_3ch

  def __call__(self, image, labels=None):
    if self.current == 'RGB' and self.to == 'HSV':
      image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    elif self.current == 'RGB' and self.to == 'GRAY':
      image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
      if self.keep_3ch:
        image = np.stack([image] * 3, axis=-1)
    elif self.current == 'HSV' and self.to == 'RGB':
      image = cv2.cvtColor(image, cv2.COLOR_HSV2RGB)
    elif self.current == 'HSV' and self.to == 'GRAY':
      image = cv2.cvtColor(image, cv2.COLOR_HSV2GRAY)
      if self.keep_3ch:
        image = np.stack([image] * 3, axis=-1)
    return image, labels


class ConvertDataType(BaseImageTransformer):
  def __init__(self, to=np.uint8):
    self.to = to

  def __call__(self, image, labels=None):
    if self.to == np.uint8:
      image = np.round(image, decimals=0).astype(self.to)
    else:
      image = image.astype(np.float32)
    return image, labels


class ConvertTo3Channels(BaseImageTransformer):
  def __init__(self):
    pass

  def __call__(self, image, labels=None):
    if image.ndim == 2:
      image = np.stack([image] * 3, axis=-1)
    elif image.ndim == 3:
      if image.shape[2] == 1:
        image = np.concatenate([image] * 3, axis=-1)
      elif image.shape[2] == 4:
        image = image[:,:,:3]
    return image, labels


class Hue(BaseImageTransformer):
  def __init__(self, delta):
    if not (-180 <= delta <= 180):
      delta = 0
    super().__init__(delta)

  def __call__(self, image, labels=None):
    image[:, :, 0] = (image[:, :, 0] + self.param) % 180.0
    return image, labels


class Saturation(BaseImageTransformer):
  def __init__(self, factor):
    if factor <= 0.0:
      factor = 1e-10
    super().__init__(factor)

  def __call__(self, image, labels=None):
    image[:,:,1] = np.clip(image[:,:,1] * self.param, 0, 255)
    return image, labels


class Brightness(BaseImageTransformer):
  def __init__(self, delta):
    super().__init__(delta)

  def __call__(self, image, labels=None):
    image = np.clip(image + self.param, 0, 255)
    return image, labels


class Contrast(BaseImageTransformer):
  def __init__(self, factor):
    if factor <= 0.0: raise ValueError("factor <= 0.0")
    super().__init__(factor)

  def __call__(self, image, labels=None):
    image = np.clip(127.5 + self.param * (image - 127.5), 0, 255)
    return image, labels


class Gamma(BaseImageTransformer):
  def __init__(self, gamma):
    if gamma <= 0.0: raise ValueError("gamma <= 0.0")
    self.gamma = gamma
    self.gamma_inv = 1.0 / gamma
    self.lut = np.array([((i / 255.0) ** self.gamma_inv) * 255 for i in np.arange(0, 256)]).astype("uint8")

  def __call__(self, image, labels=None):
    image = cv2.LUT(image, self.lut)
    return image, labels


class RandomGamma(BaseImageTransformer):
  def __init__(self, lower=0.25, upper=2.0, prob=0.5):
    if lower >= upper: raise ValueError("lower >= upper")
    self.lower = lower
    self.upper = upper
    self.prob = prob

  def __call__(self, image, labels=None):
    p = np.random.uniform(0,1)
    if p >= (1.0-self.prob):
      gamma = np.random.uniform(self.lower, self.upper)
      change_gamma = Gamma(gamma=gamma)
      return change_gamma(image, labels)
    else:
      return image, labels


class HistogramEqualization(BaseImageTransformer):
  def __init__(self):
    pass

  def __call__(self, image, labels=None):
    image[:,:,2] = cv2.equalizeHist(image[:,:,2])
    return image, labels


class RandomHistogramEqualization(BaseImageTransformer):
  def __init__(self, prob=0.5):
    self.prob = prob
    self.equalize = HistogramEqualization()

  def __call__(self, image, labels=None):
    p = np.random.uniform(0,1)
    if p >= (1.0-self.prob):
      return self.equalize(image, labels)
    else:
      return image, labels


class ChannelSwap(BaseImageTransformer):
  def __init__(self, order):
    self.order = order

  def __call__(self, image, labels=None):
    image = image[:,:,self.order]
    return image, labels


class RandomChannelSwap(BaseImageTransformer):
  def __init__(self, prob=0.5):
    self.prob = prob
    self.permutations = [(0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]
    self.swap_channels = ChannelSwap(order=(0, 1, 2))

  def __call__(self, image, labels=None):
    p = np.random.uniform(0,1)
    if p >= (1.0-self.prob):
      i = np.random.randint(5)
      self.swap_channels.order = self.permutations[i]
      return self.swap_channels(image, labels)
    else:
      return image, labels


class BlackWhite(BaseImageTransformer):
  def __init__(self, param=0):
    super().__init__(param)

  def __call__(self, image, labels=None):
    image = np.transpose(np.tile(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (3, 1, 1)), [1, 2, 0])
    return image, labels


class GaussianNoise(BaseImageTransformer):
  def __init__(self, variance=64, mean=0):
    super().__init__(variance)
    self.mean = mean

  def __call__(self, image, labels=None):
    if image.ndim < 3:
      image = np.expand_dims(image, axis=-1)
    image = image.astype(np.float32)

    sigma = self.param ** 0.5
    noise = np.random.normal(self.mean, sigma, (image.shape[0], image.shape[1]))
    noise = np.transpose(np.tile(noise, (image.shape[-1], 1, 1)), [1, 2, 0])

    image += noise

    image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=-1)
    image = image.astype(np.uint8)

    return image, labels


class Pixelisator(BaseImageTransformer):
  def __init__(self, k):
    super().__init__(k)

  def __call__(self, image, labels=None):
    w = image.shape[0]
    h = image.shape[1]
    k = 1.0 / self.param
    image = cv2.resize(image, (int(w * k), int(h * k)))
    image = cv2.resize(image, (w, h))
    return image, labels


class Blur(BaseImageTransformer):
  def __init__(self, k):
    super().__init__(k)

  def __call__(self, image, labels=None):
    image = cv2.blur(image, (int(self.param), int(self.param)))
    return image, labels


class PhotometricTransformer:
  def __init__(self):
    self.sequences = [
                      [
                        ConvertTo3Channels(),
                        RandomTransformer(Brightness, lower=-32, upper=32, proba=0.5),
                        ConvertDataType(to=np.float32),
                        RandomTransformer(Contrast, lower=0.5, upper=1.5, proba=0.5),
                        ConvertDataType(to=np.uint8),
                        RandomTransformer(BlackWhite, lower=0, upper=0, proba=0.2),
                        RandomTransformer(GaussianNoise, lower=32, upper=256, proba=0.2),
                        RandomTransformer(Pixelisator, lower=1.0, upper=3.0, proba=0.2),
                        RandomTransformer(Blur, lower=2.0, upper=10.0, proba=0.2),
                        ConvertColor(current='RGB', to='HSV'),
                        ConvertDataType(to=np.float32),
                        RandomTransformer(Saturation, lower=0.5, upper=1.5, proba=0.5),
                        RandomTransformer(Hue, lower=-18, upper=18, proba=0.5),
                        ConvertDataType(to=np.uint8),
                        ConvertColor(current='HSV', to='RGB'),
                        RandomChannelSwap(prob=0.0)
                      ],
                      [
                        ConvertTo3Channels(),
                        ConvertDataType(to=np.uint8),
                        RandomTransformer(Brightness, lower=-64, upper=64, proba=0.5),
                        RandomTransformer(BlackWhite, lower=0, upper=0, proba=0.4),
                        RandomTransformer(GaussianNoise, lower=32, upper=256, proba=0.4),
                        RandomTransformer(Pixelisator, lower=1.0, upper=4.0, proba=0.2),
                        RandomTransformer(Blur, lower=2.0, upper=20.0, proba=0.2),
                        ConvertColor(current='RGB', to='HSV'),
                        ConvertDataType(to=np.float32),
                        RandomTransformer(Saturation, lower=0.5, upper=2.5, proba=0.5),
                        RandomTransformer(Hue, lower=-64, upper=64, proba=0.5),
                        ConvertDataType(to=np.uint8),
                        ConvertColor(current='HSV', to='RGB'),
                        ConvertDataType(to=np.float32),
                        RandomTransformer(Contrast, lower=0.5, upper=2.5, proba=0.5),
                        ConvertDataType(to=np.uint8),
                        RandomChannelSwap(prob=0.0)
                      ]
    ]

  def load_image(self, image_path):
    return cv2.imread(image_path)

  def __call__(self, image, labels=None):
    if isinstance(image, str):
      image = self.load_image(image)

    idx = np.random.choice(len(self.sequences))
    for transformer in self.sequences[idx]:
      image, labels = transformer(image, labels)
    return image, labels
