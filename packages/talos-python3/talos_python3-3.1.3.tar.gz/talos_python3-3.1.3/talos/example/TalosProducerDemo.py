#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.producer.UserMessageCallback import UserMessageCallback
from talos.producer.TalosProducer import TalosProducer
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.SimpleAbnormalCallback import SimpleAbnormalCallback
from talos.thrift.auth.ttypes import Credential
from talos.thrift.auth.ttypes import UserType
from talos.thrift.message.ttypes import Message
from atomic import AtomicLong
import logging
import time
import traceback

logger = logging.getLogger("TalosProducerDemo")
successPutNumber = AtomicLong(0)
talosProducer = TalosProducer


# callback for producer success/fail to put message
class MyMessageCallback(UserMessageCallback):
	# count when success

	def on_success(self, userMessageResult=None):
		successPutNumber.get_and_set(successPutNumber.value
			  + len(userMessageResult.get_message_list()))
		count = successPutNumber.value

		for message in userMessageResult.get_message_list():
			logger.info("success to put message: " + str(message.message) + " for topic： "
			  + userMessageResult.get_topic_name() + " for partition: "
			  + str(userMessageResult.get_partition_id()))

		logger.info("success to put message: " + str(count) + " so far.")
		print("success to put message: " + str(count) + " so far.")

	# retry when failed
	def on_error(self, userMessageResult=None):
		try:
			for message in userMessageResult.get_message_list():
				logger.info("failed to put message: " + message + " we will retry to put it.")
			talosProducer.add_user_message(userMessageResult.get_message_list())
		except Exception as e:
			print(str(traceback.format_exc()))


class TalosProducerDemo:
	accessKey = "$yourAccessKey"
	accessSecret = "$yourSecretKey"
	topicName = "$yourTopicName"

	pro = dict()
	pro["galaxy.talos.service.endpoint"] = "$youEndpoint"
	consumerConfig = TalosClientConfig
	credential = Credential
	toPutMsgNumber = 5

	def __init__(self):
		self.producerConfig = TalosClientConfig(self.pro)
		# credential
		self.credential = Credential(UserType.DEV_XIAOMI, self.accessKey, self.accessSecret)

	def start(self):
		# init producer
		talosProducer = TalosProducer(producerConfig=self.producerConfig,
									  credential=self.credential,
									  topicName=self.topicName,
									  topicAbnormalCallback=SimpleAbnormalCallback(),
									  userMessageCallback=MyMessageCallback())

		while True:
			messageList = []
			i = 0
			while i < self.toPutMsgNumber:
				message = Message(message="test message: this message is a text string.")
				messageList.append(message)
				i += 1
			talosProducer.add_user_message(messageList)
			time.sleep(10)

		# when call shutdown function,
		# the producer will wait all the messages in buffer to send to server
		# talosProducer.shutdown()


producerDemo = TalosProducerDemo()
producerDemo.start()

