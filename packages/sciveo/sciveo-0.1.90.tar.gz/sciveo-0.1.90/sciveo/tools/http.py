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
from urllib import request, parse
from urllib.error import HTTPError
import requests

from sciveo.tools.logger import *
from sciveo.tools.synchronized import ListQueue


def POST_JSON(url, data_json, headers={}, timeout=30):
  result = False
  try:
    #debug("POST", url, data_json, headers)
    response = requests.post(url, json=data_json, headers=headers, timeout=timeout)
    result = response.json()
    debug("POST", result)
  except HTTPError as e:
    error(e, data_json)
  except Exception as e:
    error(e, data_json)
  return result

def POST(url, data, headers={}, timeout=30):
  result = False
  try:
    debug("POST", url, data, headers)
    data = parse.urlencode(data).encode("utf-8")
    resp = request.urlopen(request.Request(url, data=data, headers=headers), timeout=timeout)
    result = json.loads(resp.read())
    debug("POST", resp.status, result)
  except HTTPError as e:
    error(e, data)
  except Exception as e:
    error(e, data)
  return result

def GET(url, headers={}, timeout=30):
  result = False
  try:
    # debug("GET", url)
    response = requests.get(url, headers=headers, timeout=timeout)
    result = response.json()
    # debug("GET", result)
  except HTTPError as e:
    error(e)
  except Exception as e:
    error(e)
  return result


class HTTPQueueSynchronized:
  _queue = None

  @staticmethod
  def queue():
    if HTTPQueueSynchronized._queue is None:
      HTTPQueueSynchronized._queue = ListQueue("HTTPQueue")
    return HTTPQueueSynchronized._queue

  @staticmethod
  def size():
    return HTTPQueueSynchronized.queue().size()

  @staticmethod
  def get(url,
          url_prefix="{}/api/v1".format(os.environ.get('API_BASE_URL', 'api.smiveo.com')),
          access_token=os.environ.get('AUTH_KEY_SENSORS_API', "none")
          ):
    debug("HTTPQueueSynchronized::GET", url)
    try:
      url = url_prefix + url
      url = HTTPQueueSynchronized.url_append(url, {"access_token": access_token})
      HTTPQueueSynchronized.queue().push({"method": "GET", "url": url, "data": None})
    except Exception as e:
      error(e, "HTTPQueueSynchronized::GET", url)

  @staticmethod
  def post(url, data,
           url_prefix="{}/api/v1".format(os.environ.get('API_BASE_URL', 'api.smiveo.com')),
           access_token=os.environ.get('AUTH_KEY_SENSORS_API', "none")
          ):
    debug("HTTPQueueSynchronized::POST", url, data)
    try:
      url = url_prefix + url
      data["access_token"] = access_token
      HTTPQueueSynchronized.queue().push({"method": "POST", "url": url, "data": parse.urlencode(data).encode("utf-8")})
    except Exception as e:
      error(e, "HTTPQueueSynchronized::POST", url, data)

  @staticmethod
  def pop(block=True, timeout=None, retries=5):
    req = HTTPQueueSynchronized.queue().pop(timeout=timeout)
    try:
      while(retries > 0):
        if HTTPQueueSynchronized.save(req["method"], req["url"], req["data"]):
          break
        retries -= 1
    except Exception as e:
      error(e, "HTTPQueueSynchronized::POP")

  @staticmethod
  def url_append(url, url_args):
    for k, v in url_args.items():
      if "?" in url:
        and_token = "&"
      else:
        and_token = "?"
      url += "{}{}={}".format(and_token, k, v)
    return url

  @staticmethod
  def save(method, url, data, timeout=10):
    try:
      debug("HTTPQueueSynchronized", method, url, data)
      resp = request.urlopen(request.Request(url, data=data), timeout=timeout)
      debug("HTTPQueueSynchronized", resp.status, resp.read())
    except HTTPError as e:
      error(e, "HTTPQueueSynchronized::HTTPError", method, url, data)
      return False
    except Exception as e:
      error(e, "HTTPQueueSynchronized::Exception", method, url, data)
      return False
    return True
