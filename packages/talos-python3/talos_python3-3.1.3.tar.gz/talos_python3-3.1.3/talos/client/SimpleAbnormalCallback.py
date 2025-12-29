#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.TopicAbnormalCallback import TopicAbnormalCallback
import logging


class SimpleAbnormalCallback(TopicAbnormalCallback):
	logger = logging.getLogger("SimpleAbnormalCallback")

	def __init__(self):
		pass

	def abnormal_handler(self, topicTalosResourceName=None, throwable=None):
		self.logger.error("Topic abnormal exception for: " + topicTalosResourceName.topicTalosResourceName + throwable.message)

