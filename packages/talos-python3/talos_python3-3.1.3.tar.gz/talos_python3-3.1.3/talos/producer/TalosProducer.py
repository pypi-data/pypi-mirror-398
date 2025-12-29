#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.thrift.topic.ttypes import GetTopicAttributeRequest
from talos.thrift.topic.ttypes import GetTopicAttributeResponse
from talos.thrift.topic.ttypes import GetDescribeInfoRequest
from talos.thrift.message.ttypes import MessageType
from talos.client.Constants import Constants
from talos.client.ScheduleInfoCache import ScheduleInfoCache
from atomic import AtomicLong
from talos.producer.BufferedMessageCount import BufferedMessageCount
from talos.producer.UserMessage import UserMessage
from talos.producer.ProducerNotActiveException import ProducerNotActiveException
from talos.client.TalosClientFactory import TalosClientFactory
from talos.client.TalosErrors import InvalidArgumentError
from talos.admin.TalosAdmin import TalosAdmin
from talos.utils import Utils
from talos.utils.FalconWriter import FalconWriter
from talos.utils.Utils import synchronized
from talos.producer.PartitionSender import PartitionSender
from talos.thrift.common.ttypes import GalaxyTalosException
from threading import Timer
import threading
import random
import logging
import traceback


class PRODUCER_STATE:
    ACTIVE = 0
    DISABLED = 1
    SHUTDOWN = 2


class TalosProducer(object):
    logger = logging.getLogger("TalosProducer")
    partitionKeyMinLen = Constants.TALOS_PARTITION_KEY_LENGTH_MINIMAL
    partitionKeyMaxLen = Constants.TALOS_PARTITION_KEY_LENGTH_MAXIMAL
    partitionNumber = int
    curPartitionId = int

    messageCallbackExecutors = threading.Thread
    partitionCheckExecutor = threading.Timer

    falconWriter = FalconWriter
    producerMonitorThread = threading.Timer

    def __init__(self, producerConfig=None, credential=None, topicName=None, talosAdmin=None,
                 talosClientFactory=None, topicTalosResourceName=None, partitioner=None,
                 topicAbnormalCallback=None, userMessageCallback=None):
        self.globalLock = threading.Condition()
        self.requestId = AtomicLong(1)
        self.partitionSenderMap = dict()
        self.lock = threading.Lock()
        self.talosProducerConfig = producerConfig
        self.producerState = PRODUCER_STATE.ACTIVE
        if talosClientFactory:
            self.talosClientFactory = talosClientFactory
        else:
            self.talosClientFactory = TalosClientFactory(self.talosProducerConfig, credential)
        if talosAdmin:
            self.talosAdmin = talosAdmin
        else:
            self.talosAdmin = TalosAdmin(self.talosClientFactory)
        self.topicName = topicName
        if topicTalosResourceName:
            self.topicTalosResourceName = topicTalosResourceName
        else:
            self.topicTalosResourceName = self.talosAdmin.get_describe_info(
                GetDescribeInfoRequest(self.topicName))
        self.partitioner = partitioner
        self.topicAbnormalCallback = topicAbnormalCallback
        self.userMessageCallback = userMessageCallback
        self.updatePartitionIdInterval = producerConfig.get_check_partition_interval()
        self.lastUpdatePartitionIdTime = Utils.current_time_mills()
        self.updatePartitionIdMsgNumber = producerConfig.get_update_partition_msg_number()
        self.lastAddMsgNumber = 0
        self.maxBufferedMsgTime = producerConfig.get_max_buffered_msg_time()
        self.maxBufferedMsgNumber = producerConfig.get_max_buffered_msg_number()
        self.maxBufferedMsgBytes = producerConfig.get_max_buffered_msg_bytes()
        self.bufferedCount = BufferedMessageCount(self.maxBufferedMsgNumber,
                                                  self.maxBufferedMsgBytes)
        self.clientId = Utils.generate_client_id(producerConfig.get_client_ip(), "producer")
        self.synchronizedLock = threading.Lock()
        self.add_user_messageLock = threading.Lock()
        self.do_add_user_messageLock = threading.Lock()
        self.create_partition_senderLock = threading.Lock()
        self.release_partition_senderLock = threading.Lock()

        # get scheduleInfo
        self.scheduleInfoCache = ScheduleInfoCache().get_schedule_info_cache(
            topicTalosResourceName=self.topicTalosResourceName.topicTalosResourceName,
            talosClientConfig=producerConfig,
            messageClient=self.talosClientFactory.new_message_client(),
            talosClientFactory=self.talosClientFactory)
        self.falconWriter = FalconWriter(falconUrl=self.talosProducerConfig.get_falcon_url())

        # getTopicTalosResourceName(producerConfig, credential);
        self.check_and_get_topic_info(self.topicTalosResourceName.topicTalosResourceName)

        self.init_partition_sender()
        self.init_check_partition_task()
        self.init_producer_monitor_task()

        self.logger.info("Init a producer for topic: " +
                         self.topicTalosResourceName.topicTalosResourceName +
                         ", partitions: " + str(self.partitionNumber))

    def check_partition_task(self):
        response = GetTopicAttributeResponse()
        try:
            response = self.talosAdmin.get_topic_attribute(
                GetTopicAttributeRequest(topicName=self.topicName))
        except Exception as e:
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.error("Exception in CheckPartitionTask: "
                              + str(traceback.format_exc()))
            if Utils.is_topic_not_exist(e):
                self.disable_producer(e)
            return

        if not self.topicTalosResourceName == response.topicTalosResourceName:
            errMsg = "The topic: " + self.topicTalosResourceName.topicTalosResourceName + \
                     " not exist. It might have been deleted. The putMessage threads" + \
                     " will be cancel."

            self.logger.error(errMsg)
            # cancel the putMessage thread
            self.disable_producer(Exception(errMsg))
            return

        topicPartitionNum = response.topicAttribute.partitionNumber
        if not self.partitionNumber == topicPartitionNum:
            self.logger.info("Adjust partitionSender and partitionNumber from: " +
                             str(self.partitionNumber) + " to: " + str(topicPartitionNum))
            # adjust partitionSender(allow decreasing)
            self.adjust_partition_sender(topicPartitionNum)
            # update partitionNumber
            self.set_partition_number(topicPartitionNum)

        self.partitionCheckExecutor = threading.Timer(interval=self.talosProducerConfig
                                                      .get_producer_check_partition_interval(),
                                                      function=self.check_partition_task)
        self.partitionCheckExecutor.setName("talos-producer-partitionCheck-" + self.topicName)
        self.partitionCheckExecutor.start()

    def producer_monitor_task(self):
        try:
            self.push_metric_data()
        except Exception as throwable:
            self.logger.error("push metric data to falcon failed." + str(traceback.format_exc()))
        self.producerMonitorThread = threading.Timer(interval=self.talosProducerConfig
                                                     .get_report_metric_interval_millis() / 1000,
                                                     function=self.producer_monitor_task)
        self.producerMonitorThread.setName("talos-producer-monitor-" + self.topicName)
        self.producerMonitorThread.start()

    def add_user_message(self, msgList=None, partitionId=None):
        self.add_user_messageLock.acquire()
        try:
            if not self.is_active():
                raise ProducerNotActiveException("Producer is not active, current state: "
                                                 + str(self.producerState))

            # check total buffered message number
            while self.bufferedCount.is_full():
                with self.lock:
                    try:
                        self.logger.info("too many buffered messages, globalLock is active."
                                         + " message number: " +
                                         str(self.bufferedCount.get_buffered_msg_number())
                                         + ", message bytes:  " +
                                         str(self.bufferedCount.get_buffered_msg_bytes()))
                        # release global lock but no notify
                        self.globalLock.acquire()
                        self.globalLock.wait()
                        self.globalLock.release()
                    except Exception as e:
                        if isinstance(e, GalaxyTalosException):
                            self.logger.error(e.errMsg)
                        self.logger.error("addUserMessage global lock wait is interrupt."
                                          + str(traceback.format_exc()))

            if partitionId is None:
                self.logger.debug("add_user_message without assign specific partition id for："
                                  + self.topicName)
                self.do_add_user_message(msgList)
            else:
                userMessageList = []

                for message in msgList:
                    # set timestamp and messageType if not set
                    Utils.update_message(message, MessageType.BINARY)
                    # check data validity
                    Utils.check_message_validity(message, self.talosProducerConfig)
                    userMessageList.append(UserMessage(message))

                assert partitionId in self.partitionSenderMap
                self.partitionSenderMap.get(partitionId).add_message(userMessageList)
        except Exception as e:
            self.logger.error("add_user_message func error: " + traceback.format_exc())
            raise e
        finally:
            self.add_user_messageLock.release()

    def do_add_user_message(self, msgList=None):
        self.do_add_user_messageLock.acquire()
        try:
            # user can optionally set 'partitionKey' and 'sequenceNumber' when construct Message
            partitionBufferMap = dict()

            # check / update curPartitionId
            if self.should_update_partition():
                self.curPartitionId = (self.curPartitionId + 1) % self.partitionNumber
                self.logger.debug("change cur partition id to: " + str(self.curPartitionId))
                self.lastUpdatePartitionIdTime = Utils.current_time_mills()
                self.lastAddMsgNumber = 0
            currentPartitionId = self.curPartitionId
            self.lastAddMsgNumber += len(msgList)

            partitionBufferMap[currentPartitionId] = []

            for message in msgList:
                # set timestamp and messageType if not set;
                Utils.update_message(message, MessageType.BINARY)
                # check data validity
                Utils.check_message_validity(message, self.talosProducerConfig)

                # check partitionKey setting and validity
                if not message.partitionKey:
                # straight forward put to cur partitionId queue
                    userMessage = UserMessage(message)
                    partitionBufferMap.get(currentPartitionId).append(userMessage)
                else:
                    self.check_message_partition_key_validity(message.partitionKey)
                    # construct UserMessage and dispatch to buffer by partitionId
                    partitionId = self.get_partition_id(message.partitionKey)
                    if partitionId not in partitionBufferMap:
                        partitionBufferMap[partitionId] = []
                        userMessage = UserMessage(message)
                        partitionBufferMap.get(partitionId).append(userMessage)

            # add to partitionSender
            for key, value in partitionBufferMap.items():
                partitionId = key
                assert partitionId in self.partitionSenderMap
                self.partitionSenderMap.get(partitionId).add_message(value)
        except Exception as e:
            self.logger.error("do_add_user_message func error: " + traceback.format_exc())
            raise e
        finally:
            self.do_add_user_messageLock.release()

    def should_update_partition(self):
        return (Utils.current_time_mills() - self.lastUpdatePartitionIdTime >=
                self.updatePartitionIdInterval) or (self.lastAddMsgNumber >=
                                                    self.updatePartitionIdMsgNumber)

    def check_message_partition_key_validity(self, partitionKey=None):
        if not partitionKey:
            raise InvalidArgumentError("Field \"partitionKey\" must be set")

        if len(partitionKey) < self.partitionKeyMinLen or len(partitionKey) > self.partitionKeyMaxLen:
            raise InvalidArgumentError("Invalid partition key which length must be at "
                                       + "least " + str(self.partitionKeyMinLen) +
                                       " and at most " + str(self.partitionKeyMinLen) +
                                       ", got " + partitionKey.length())

    def get_partition_id(self, partitionKey=None):
        return self.partitioner.partition(partitionKey, self.partitionNumber)

    # cancel the putMessage threads and checkPartitionTask
    # when topic not exist during producer running
    def disable_producer(self, exception=None):
        if not self.is_active():
            return

        self.producerState = PRODUCER_STATE.DISABLED
        self.stop_and_wait()
        self.topicAbnormalCallback.abnormal_handler(self.topicTalosResourceName, exception)

    def is_active(self):
        return self.producerState == PRODUCER_STATE.ACTIVE

    def is_disabled(self):
        return self.producerState == PRODUCER_STATE.DISABLED

    def is_shutdown(self):
        return self.producerState == PRODUCER_STATE.SHUTDOWN

    def shutdown(self):
        if not self.is_active():
            return
        self.producerState = PRODUCER_STATE.SHUTDOWN
        self.stop_and_wait()

    def stop_and_wait(self):
        for key, value in self.partitionSenderMap.items():
            value.shutdown()
        self.partitionCheckExecutor.cancel()
        if self.talosProducerConfig.is_open_client_monitor():
            self.producerMonitorThread.cancel()
        self.scheduleInfoCache.shut_down(self.topicTalosResourceName)

    def adjust_partition_sender(self, newPartitionNum=None):
        if self.partitionNumber < newPartitionNum:
            partitionId = self.partitionNumber
            while partitionId < newPartitionNum:
                self.create_partition_sender(partitionId)
                partitionId += 1
        elif self.partitionNumber > newPartitionNum:
            partitionId = newPartitionNum
            while partitionId < self.partitionNumber:
                self.release_partition_sender(partitionId)
                partitionId += 1

    def create_partition_sender(self, partitionId=None):
        self.create_partition_senderLock.acquire()
        try:
            partitionSender = PartitionSender(partitionId=partitionId,
                                              topicName=self.topicName,
                                              topicTalosResourceName=
                                              self.topicTalosResourceName,
                                              requestId=self.requestId, clientId=self.clientId,
                                              talosProducerConfig=self.talosProducerConfig,
                                              messageClient=self.talosClientFactory.
                                              new_message_client(), userMessageCallback=
                                              self.userMessageCallback,
                                              messageCallbackExecutors=
                                              self.messageCallbackExecutors,
                                              globalLock=self.globalLock, producer=self)
            self.partitionSenderMap[partitionId] = partitionSender
            self.logger.debug("init partition sender for: " + self.topicName
                              + "for partitionId : " + str(partitionId))
        except Exception as e:
            self.logger.error("create_partition_sender func error: " + traceback.format_exc())
        finally:
            self.create_partition_senderLock.release()

    def release_partition_sender(self, partitionId=None):
        self.release_partition_senderLock.acquire()
        try:
            self.partitionSenderMap.get(partitionId).close()
            del self.partitionSenderMap[partitionId]
        except Exception as e:
            self.logger.error("release_partition_sender func error: " + traceback.format_exc())
        finally:
            self.release_partition_senderLock.release()

    def set_partition_number(self, partitionNum=None):
        self.partitionNumber = partitionNum

    def check_and_get_topic_info(self, topicTalosResourceName=None):
        topicName = Utils.get_topic_name_by_resource_name(topicTalosResourceName.topicTalosResourceName)
        response = self.talosAdmin.get_topic_attribute(
            GetTopicAttributeRequest(topicName))

        if not topicTalosResourceName == response.topicTalosResourceName:
            raise InvalidArgumentError("The topic: " +
                                       topicTalosResourceName.topicTalosResourceName
                                       + " not found")

        self.partitionNumber = response.topicAttribute.partitionNumber
        self.curPartitionId = random.randint(0, self.partitionNumber-1)
        self.topicTalosResourceName = topicTalosResourceName

    def init_partition_sender(self):
        partitionId = 0
        while partitionId < self.partitionNumber:
            self.create_partition_sender(partitionId)
            partitionId += 1

    @synchronized
    def init_check_partition_task(self):
        self.partitionCheckExecutor = Timer(interval=self.talosProducerConfig.
                                            get_producer_check_partition_interval(),
                                            function=self.check_partition_task)
        self.partitionCheckExecutor.setName("talos-producer-partitionCheck-" + self.topicName)
        self.partitionCheckExecutor.start()

    def init_producer_monitor_task(self):
        if self.talosProducerConfig.is_open_client_monitor():
            # push metric data to falcon every minutes
            self.producerMonitorThread = Timer(interval=self.talosProducerConfig.
                                               get_report_metric_interval_millis() / 1000,
                                               function=self.producer_monitor_task)
            self.producerMonitorThread.setName("talos-producer-monitor-" + self.topicName)
            self.producerMonitorThread.start()

    def increase_buffered_count(self, incrementNumber=None, incrementBytes=None):
        self.bufferedCount.increase(incrementNumber, incrementBytes)

    def decrease_buffered_count(self, decrementNumber=None, decrementBytes=None):
        self.bufferedCount.decrease(decrementNumber, decrementBytes)

    def push_metric_data(self):
        jsonArray = []
        for key, value in self.partitionSenderMap.items():
            jsonArray += value.get_falcon_data()
        self.falconWriter.push_falcon_data(jsonArray)
