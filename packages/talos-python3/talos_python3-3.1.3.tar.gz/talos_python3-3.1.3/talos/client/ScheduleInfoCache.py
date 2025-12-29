#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

import time
import logging
import threading
from atomic import AtomicLong
from threading import Timer
from talos.utils import Utils
from talos.utils.Utils import ReadWriteLock
from talos.utils.Utils import synchronized
from talos.thrift.message.MessageService import GetScheduleInfoRequest
import traceback


class ScheduleInfoCache:
	logger = logging.getLogger("ScheduleInfoCache")
	scheduleInfoCacheMap = dict()
	scheduleInfoMap = dict()

	def __init__(self, topicTalosResourceName=None, talosClientConfig=None, messageClient=None,
				 talosClientFactory=None):
		self.readWriteLock = ReadWriteLock()
		self.messageClientMap = dict()
		self.clientNum = AtomicLong(0)
		self.get_schedule_info_cacheLock = threading.Lock()
		self.synchronizedLock = threading.Lock()
		if talosClientConfig:
			self.isAutoLocation = talosClientConfig.get_is_auto_location()
			self.topicTalosResourceName = topicTalosResourceName
			self.talosClientConfig = talosClientConfig
			self.messageClient = messageClient
			self.talosClientFactory = talosClientFactory

			# GetScheduleInfoScheduleExecutor
			# for Schedule get work, cause ScheduledExecutorService
			# use DelayedWorkQueue storage its task, which is unbounded.To private OOM, use
			# GetScheduleInfoExecutor execute task when transfered, setting Queue size as 2.
			self.GetScheduleInfoScheduleExecutor = Timer

			if self.isAutoLocation:
				self.logger.info("Auto location is enabled for request of " +
								 str(self.topicTalosResourceName.topicTalosResourceName))
			else:
				self.logger.info("Auto location is forbidden for request of " +
								 str(self.topicTalosResourceName.topicTalosResourceName))

			try:
				# get and update scheduleInfoMap
				self.get_schedule_info(self.topicTalosResourceName)
			except Exception as e:
				self.logger.error("Exception in GetScheduleInfoTask: " + str(traceback.format_exc()))
				if Utils.is_topic_not_exist(e):
					return

	def get_schedule_info_task(self):
		maxRetry = self.talosClientConfig.get_schedule_info_max_retry() + 1

		while maxRetry > 0:
			try:
				# get and update scheduleInfoMap
				self.get_schedule_info(self.topicTalosResourceName)
				# to prevent frequent ScheduleInfo call
				time.sleep(10)
				return
			except Exception as e:
				# 1. if throwable instance of TopicNotExist, cancel all reading task
				# 2. if other throwable such as LockNotExist or HbaseOperationFailed, retry again
				# 3. if scheduleInfoMap didn't update success after maxRetry, just return and use
				# old data, it may update next time or targeted update when Transfered.
				if Utils.is_topic_not_exist(e):
					return
				if self.logger.isEnabledFor(logging.DEBUG):
					self.logger.debug("Exception in GetScheduleInfoTask: " + str(
						traceback.format_exc()))
			finally:
				maxRetry = maxRetry - 1

	def get_schedule_info_cache(self, topicTalosResourceName=None, talosClientConfig=None,
							   messageClient=None, talosClientFactory=None):
		self.get_schedule_info_cacheLock.acquire()
		try:
			if not self.scheduleInfoCacheMap.get(topicTalosResourceName):
				if not talosClientFactory:
					# this case should not exist normally, only when interface of simpleAPI improper used
					self.scheduleInfoCacheMap[topicTalosResourceName] = ScheduleInfoCache(topicTalosResourceName,
							  talosClientConfig, messageClient)
				else:
					self.scheduleInfoCacheMap[topicTalosResourceName] = ScheduleInfoCache(topicTalosResourceName,
					talosClientConfig, messageClient, talosClientFactory)

			clientNum = self.scheduleInfoCacheMap[topicTalosResourceName].clientNum.value
			self.scheduleInfoCacheMap[topicTalosResourceName].clientNum.get_and_set(clientNum + 1)
			self.logger.info("there were " + str(self.scheduleInfoCacheMap[topicTalosResourceName].clientNum.value) +
							 " partitions of " + str(topicTalosResourceName.topicTalosResourceName)
							 + " use same scheduleInfoCache together.")
			return self.scheduleInfoCacheMap[topicTalosResourceName]
		except Exception as e:
			self.logger.error("get_schedule_info_cache func error: " + traceback.format_exc())
		finally:
			self.get_schedule_info_cacheLock.release()

	def get_or_create_message_client(self, topicAndPartition):
		if not self.scheduleInfoMap:
			self.update_schedule_info_cache()
			return self.messageClient
		host = self.scheduleInfoMap.get(topicAndPartition, None)
		if not host:
			self.update_schedule_info_cache()
			return self.messageClient
		messageClient = None
		if host in self.messageClientMap:
			messageClient = self.messageClientMap[host]
		if not messageClient:
			messageClient = self.talosClientFactory.new_message_client("http://" + str(host))
			self.messageClientMap[host] = messageClient
		return messageClient

	def update_schedule_info_cache(self):
		if self.isAutoLocation:
			self.GetScheduleInfoScheduleExecutor = Timer(interval=0, function=self.get_schedule_info_task)
			self.GetScheduleInfoScheduleExecutor.setName(
				"talos-ScheduleInfoCache-" + str(self.topicTalosResourceName.topicTalosResourceName))
			self.GetScheduleInfoScheduleExecutor.start()

	def get_is_auto_location(self):
		return self.isAutoLocation

	@synchronized
	def shut_down(self, topicTalosResourceName=None):
		if not self.scheduleInfoCacheMap[topicTalosResourceName]:
			self.logger.error("there were no scheduleInfoCache for " +
							  str(self.topicTalosResourceName.topicTalosResourceName)
							  + " when call scheduleInfoCache shutDown")
			return
		# shutdown the scheduleInfoCache when there were no client of this topic.
		if self.scheduleInfoCacheMap[topicTalosResourceName].clientNum.value == 1:
			self.logger.info("scheduleInfoCache of " + str(self.topicTalosResourceName.topicTalosResourceName)
							 + " is shutting down...")
			self.scheduleInfoCacheMap[topicTalosResourceName].GetScheduleInfoScheduleExecutor.cancel()
			if topicTalosResourceName in self.scheduleInfoCacheMap:
				del self.scheduleInfoCacheMap[topicTalosResourceName]
			self.logger.info("scheduleInfoCache of " + topicTalosResourceName + " shutdown.")
		else:
			self.logger.info("there were still " + str(self.scheduleInfoCacheMap[topicTalosResourceName].clientNum.value)
							 +" partitions of " + str(self.topicTalosResourceName.topicTalosResourceName)
							 + " use this scheduleInfoCache. skip it")

	def shut_down_all(self):
		self.logger.info("scheduleInfoCache is shutting down...")
		for key in self.scheduleInfoCacheMap.keys():
			self.scheduleInfoCacheMap[key].GetScheduleInfoScheduleExecutor.cancel()
		self.scheduleInfoCacheMap.clear()
		self.logger.info("scheduleInfoCache shutdown.")

	def get_schedule_info(self, topicTalosResourceName):
		# judge isAutoLocation serveral place to make sure request server only when need.
		# 1.before send Executor task make sure send Executor task when need;
		# 2.judge in getScheduleInfo is the Final guarantee good for code extendibility;
		if self.isAutoLocation:
			topicScheduleInfoMap = self.messageClient.get_schedule_info(
				GetScheduleInfoRequest(topicTalosResourceName))
			self.readWriteLock.write_acquire()
			self.scheduleInfoMap = topicScheduleInfoMap
			self.readWriteLock.write_release()
		if self.logger.isEnabledFor(logging.DEBUG):
			self.logger.debug("getScheduleInfo success" + str(self.scheduleInfoMap))

	# update message client just for Talos Canary
	def set_message_client(self, messageClient=None):
		self.messageClient = messageClient

