#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

import abc


class TopicAbnormalCallback:
	#
	# User implement this method to process topic abnormal status such as 'TopicNotExist'
	#
	@abc.abstractmethod
	def abnormal_handler(self, topicTalosResourceName=None, throwable=None):
		pass
