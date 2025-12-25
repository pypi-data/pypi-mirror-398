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

import boto3
import json

from sciveo.tools.logger import *
from sciveo.tools.compress import *
from sciveo.tools.simple_counter import RunCounter


class SQSPriorityQueue:
  def __init__(self, queue_level, queue_id, base_queue_name="MEDIA-JOBS", region_name='us-east-1'):
    self.queue_level = queue_level
    self.queue_id = queue_id
    self.sqs = boto3.client('sqs', region_name=region_name)
    self.zip = CompressJsonData()
    self.base_queue_name = base_queue_name
    self.urls = {}
    self.name = f"{self.base_queue_name}-{self.queue_level}-{self.queue_id}"
    debug("init", self.name)

  def list(self):
    response = self.sqs.list_queues()
    if 'QueueUrls' in response:
      urls = response['QueueUrls']
    else:
      urls = []
    debug("list", urls)
    return urls

  def size(self):
    response = self.sqs.get_queue_attributes(
      QueueUrl=self.url(),
      AttributeNames=[
        'ApproximateNumberOfMessages',
        'ApproximateNumberOfMessagesNotVisible'
      ]
    )
    size_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    size_messages_invisible = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
    return max(size_messages, size_messages_invisible)

  def delete(self):
    return self.sqs.delete_queue(QueueUrl=self.url())

  def create(self):
    response = self.sqs.create_queue(QueueName=self.name)
    self.urls[self.name] = response['QueueUrl']
    debug((self.queue_level, self.queue_id), "url", response['QueueUrl'])
    return response['QueueUrl']

  def url(self):
    if self.name in self.urls:
      return self.urls[self.name]

    try:
      response = self.sqs.get_queue_url(QueueName=self.name)
      return response['QueueUrl']
    except Exception as e:
      warning("url missing", (self.queue_level, self.queue_id))
      return self.create()

  def push(self, msg):
    return self.sqs.send_message(
      QueueUrl=self.url(),
      MessageBody=json.dumps({"data": self.zip.compress(msg)})
    )

  def pull(self):
    response = self.sqs.receive_message(
      QueueUrl=self.url(),
      MaxNumberOfMessages=1,
      VisibilityTimeout=60,
      WaitTimeSeconds=20
    )
    if 'Messages' in response:
      message = response['Messages'][0]
      result = self.zip.decompress(json.loads(message['Body'])["data"])
      debug((self.queue_level, self.queue_id), "pulled", result)
      receipt_handle = message['ReceiptHandle']
      self.sqs.delete_message(
        QueueUrl=self.url(),
        ReceiptHandle=receipt_handle
      )
      return result
    else:
      return None

  def pull_wait(self):
    printer = RunCounter(1, lambda: debug((self.queue_level, self.queue_id), "pull_waiting..."))
    while(True):
      try:
        result = self.pull()
      except Exception as e:
        error(e)
        continue

      if result:
        return result
      printer.run()
