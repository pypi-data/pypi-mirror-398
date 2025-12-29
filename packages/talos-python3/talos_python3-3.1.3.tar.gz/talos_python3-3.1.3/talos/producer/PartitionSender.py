#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.thrift.common.ttypes import GalaxyTalosException
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.producer.TalosProducerConfig import TalosProducerConfig
from talos.producer.UserMessageResult import UserMessageResult
from talos.producer.SimpleProducer import SimpleProducer
from talos.utils.Utils import synchronized
from talos.utils import Utils
from talos.client.Constants import Constants
from talos.producer.PartitionMessageQueue import PartitionMessageQueue
from concurrent.futures import ThreadPoolExecutor
import logging
import json
import threading
import traceback


class TASK_STATE:
    ACTIVE = 0
    CLOSE = 1


class ProducerMetrics(object):
    falconEndpoint = str
    putMsgDuration = int
    maxPutMsgDuration = int
    minPutMsgDuration = int
    putMsgTimes = int
    putMsgFailedTimes = int
    producerMetricsMap = dict
    talosProducerConfig = TalosProducerConfig
    topicAndPartition = TopicAndPartition

    def __init__(self, talosProducerConfig=None, topicAndPartition=None):
        self.init_metrics()
        self.talosProducerConfig = talosProducerConfig
        self.topicAndPartition = topicAndPartition
        self.falconEndpoint = self.talosProducerConfig.get_producer_metric_falcon_endpoint() \
                              + self.topicAndPartition.topicName
        self.producerMetricsMap = dict()

    def init_metrics(self):
        self.putMsgDuration = 0
        self.maxPutMsgDuration = 0
        self.minPutMsgDuration = 0
        self.putMsgTimes = 0
        self.putMsgFailedTimes = 0

    def mark_put_msg_duration(self, putMsgDuration=None):
        if putMsgDuration > self.maxPutMsgDuration:
            self.maxPutMsgDuration = putMsgDuration

        if self.minPutMsgDuration == 0 or putMsgDuration < self.minPutMsgDuration:
            self.minPutMsgDuration = putMsgDuration

        self.putMsgDuration = putMsgDuration
        self.putMsgTimes += 1

    def mark_put_msg_failed_times(self):
        self.putMsgFailedTimes += 1

    def to_json_data(self):
        self.update_metrics_map()
        jsonArray = list()
        for key, value in self.producerMetricsMap.items():
            jsonDict = self.get_basic_data()
            jsonDict["metric"] = key
            jsonDict["value"] = value
            jsonArray.append(jsonDict)
        self.init_metrics()
        return jsonArray

    def update_metrics_map(self):
        self.producerMetricsMap[Constants.PUT_MESSAGE_TIME] = self.putMsgDuration
        self.producerMetricsMap[Constants.MAX_PUT_MESSAGE_TIME] = self.maxPutMsgDuration
        self.producerMetricsMap[Constants.MIN_PUT_MESSAGE_TIME] = self.minPutMsgDuration
        self.producerMetricsMap[Constants.PUT_MESSAGE_TIMES] = int(self.putMsgTimes / 60.0)
        self.producerMetricsMap[Constants.PUT_MESSAGE_FAILED_TIMES] = int(self.putMsgFailedTimes/ 60.0)

    def get_basic_data(self):
        tag = "clusterName=" + self.talosProducerConfig.get_cluster_name()
        tag += ",topicName=" + self.topicAndPartition.topicName
        tag += ",partitionId=" + str(self.topicAndPartition.partitionId)
        tag += ",ip=" + self.talosProducerConfig.get_client_ip()
        tag += ",type=" + self.talosProducerConfig.get_alert_type()

        basicData = dict()
        basicData["endpoint"] = self.falconEndpoint
        basicData["timestamp"] = int(Utils.current_time_mills() / 1000)
        basicData["step"] = int(self.talosProducerConfig.get_metric_falcon_step() / 1000)
        basicData["counterType"] = "GAUGE"
        basicData["tags"] = tag
        return basicData


class MessageWriter(threading.Thread):

    def __init__(self, partitionSender=None, globalLock=None):
        threading.Thread.__init__(self, name="messageWriter-" +
                                             partitionSender.topicAndPartition.topicName
                                             + "-" + str(partitionSender.topicAndPartition.partitionId))
        self.partitionSender = partitionSender
        self.globalLock = globalLock
        self.simpleProducer = SimpleProducer(
            producerConfig=partitionSender.talosProducerConfig,
            topicAndPartition=partitionSender.topicAndPartition,
            messageClient=partitionSender.messageClient,
            clientId=partitionSender.clientId,
            requestId=partitionSender.requestId)
        self.synchronizedLock = threading.Lock()

    def run(self):
        while self.partitionSender.get_cur_state() == TASK_STATE.ACTIVE:
            try:
                messageList = self.partitionSender.partitionMessageQueue.get_message_list()

                # when messageList return no message, this means TalosProducer not
                # alive and there is no more message to send, then we should exit
                # write message right now;
                if len(messageList) == 0:
                    # notify to wake up producer's global lock
                    with self.synchronizedLock:
                        if self.globalLock.acquire():
                            self.globalLock.notifyAll()
                            self.globalLock.release()
                    break

                self.partitionSender.put_message(messageList, self.simpleProducer)
            except Exception as e:
                if isinstance(e, GalaxyTalosException):
                    self.partitionSender.logger.error(e.errMsg)
                self.partitionSender.logger.error(
                    "PutMessageTask for topicAndPartition: " +
                    str(self.partitionSender.topicAndPartition)
                    + " failed" + str(traceback.format_exc()))
            finally:
                # notify to wake up producer's global lock
                with self.synchronizedLock:
                    if self.globalLock.acquire():
                        self.globalLock.notifyAll()
                        self.globalLock.release()

        self.partitionSender.process_buffered_message()


class MessageCallbackTask(threading.Thread):
    def __init__(self, userMessageResult=None, userMessageCallback=None):
        threading.Thread.__init__(self)
        self.userMessageCallback = userMessageCallback
        self.userMessageResult = userMessageResult

    def run(self):
        if self.userMessageResult.is_successful():
            self.userMessageCallback.on_success(self.userMessageResult)
        else:
            self.userMessageCallback.on_error(self.userMessageResult)


class PartitionSender:
    logger = logging.getLogger("PartitionSender")

    def __init__(self, partitionId=None, topicName=None, topicTalosResourceName=None,
                 requestId=None, clientId=None, talosProducerConfig=None,
                 messageClient=None, userMessageCallback=None, messageCallbackExecutors=None,
                 globalLock=None, producer=None):
        self.partitionId = partitionId
        # a static attribute of TalosProducer which will guarantee that
        # the requestId of all PartitionSender always be global unique
        self.requestId = requestId
        self.clientId = clientId
        self.talosProducerConfig = talosProducerConfig
        self.messageClient = messageClient
        self.userMessageCallback = userMessageCallback
        self.messageCallbackExecutors = messageCallbackExecutors
        self.globalLock = globalLock
        self.producer = producer
        self.synchronizedLock = threading.Lock()
        self.update_stateLock = threading.Lock()

        self.curState = TASK_STATE.ACTIVE
        self.topicAndPartition = TopicAndPartition(topicName,
                                                   topicTalosResourceName,
                                                   partitionId)
        self.partitionMessageQueue = PartitionMessageQueue(talosProducerConfig,
                                                           partitionId, producer)
        self.producerMetrics = ProducerMetrics(talosProducerConfig=self.talosProducerConfig,
                                               topicAndPartition=self.topicAndPartition)
        self.singleExecutor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="talos-producer-" +
                                              self.topicAndPartition.topicName
                                              + " " + str(self.topicAndPartition.partitionId))

        self.executor = MessageWriter(self, self.globalLock)
        self.executor.start()

    def put_message(self, messageList=None, simpleProducer=None):
        userMessageResult = UserMessageResult(messageList,
                                              self.topicAndPartition.topicName,
                                              self.partitionId)
        try:
            # when TalosProducer is disabled, we just fail the message and inform user;
            # but when TalosProducer is shutdown, we will send the left message.
            if self.producer.is_disabled():
                e = Exception()
                e.message = "The Topic: " + self.topicAndPartition.topicName + \
                            " with resourceName: " + self.topicAndPartition.topicTalosResourceName.topicTalosResourceName \
                            + " no longer exist. Please check the topic and" +  \
                            " reconstruct the TalosProducer again"
                raise e
            else:
                startPutMsgTime = Utils.current_time_mills()
                simpleProducer.do_put(messageList)
                self.producerMetrics.mark_put_msg_duration(Utils.current_time_mills()
                                                           - startPutMsgTime)
                # putMessage success callback
                userMessageResult.set_successful(True)
                self.messageCallbackExecutors = MessageCallbackTask(userMessageResult,
                                                                    self.userMessageCallback)
                self.messageCallbackExecutors.start()
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug("put " + str(len(messageList)) +
                                      " message success for partition: "
                                      + str(self.partitionId))
        except Exception as e:
            self.producerMetrics.mark_put_msg_failed_times()

            # 1. backoff sleep and retry according to configuration
            # 2. clear partition buffer when long time failed and
            # queue size greater than threshold
            # 3. truly failed, execute callback task
            self.process_fetched_exception(e, userMessageResult, simpleProducer)

    def process_fetched_exception(self, e=None, userMessageResult=None, simpleProducer=None):
        retrySuccess = self.retry_put_message(e, userMessageResult, simpleProducer)
        if not retrySuccess:
            # execute putMessage failed callback when all retry failed
            userMessageResult.set_successful(False)
            userMessageResult.set_cause(e)
            self.messageCallbackExecutors = MessageCallbackTask(userMessageResult,
                                                                self.userMessageCallback)
            self.messageCallbackExecutors.start()
            if self.logger.isEnabledFor(logging.DEBUG):
                for message in userMessageResult.get_message_list():
                    self.logger.error(message.sequenceNumber + ": " + str(message.message))

            if not Utils.is_partition_not_serving(e):
                if isinstance(e, GalaxyTalosException):
                    self.logger.error(e.errMsg)
                self.logger.error("Failed to put " + str(len(userMessageResult.get_message_list())) +
                                  " messages for partition: " + str(self.partitionId)
                                  + str(traceback.format_exc()) )

    def retry_put_message(self, e=None, userMessageResult=None, simpleProducer=None):
        if self.talosProducerConfig.get_max_retry() <= 0:
            return False

        retry = 0
        while retry <= self.talosProducerConfig.get_max_retry():
            pauseTime = Utils.get_put_msg_failed_delay(retry, self.talosProducerConfig)
            retry += 1
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.warn("putMessage failed " + str(retry) +
                                 " times for partition: " + str(self.partitionId) +
                                 ", sleep " + str(pauseTime) +
                                 "ms for avoid infinitely retry." + e.message)
            # 1. sleep
            Utils.sleep_pause_time(pauseTime)

            # 2. retry putMessage, just return if retry success
            try:
                startPutMsgTime = Utils.current_time_mills()
                simpleProducer.do_put(userMessageResult.get_message_list())
                self.producerMetrics.mark_put_msg_duration(Utils.current_time_mills()
                                                           - startPutMsgTime)
                userMessageResult.set_successful(True)
                self.messageCallbackExecutors = MessageCallbackTask(userMessageResult,
                                                                    self.userMessageCallback)
                self.messageCallbackExecutors.start()
                return True
            except Exception as ex:
                self.producerMetrics.mark_put_msg_failed_times()
                if isinstance(ex, GalaxyTalosException):
                    self.logger.error(ex.errMsg)
                self.logger.error("retry put message failed. " + str(traceback.format_exc()))

            # 3. clear messageQueue when retry > 10 and partition buffer size > 10MB
            if retry >= self.talosProducerConfig.get_put_message_max_failed_times() and \
                    self.partitionMessageQueue.get_cur_message_bytes() > \
                    self.talosProducerConfig.get_max_put_msg_bytes():
                self.clear_message_queue(e)

        return False

    def clear_message_queue(self, e=None):
        # clear MessageQueue, and execute onError callback
        bufferedUserMsgResult = UserMessageResult(
            self.partitionMessageQueue.get_all_message_list(),
            self.topicAndPartition.topicName(), self.partitionId)
        bufferedUserMsgResult.set_successful(False)
        bufferedUserMsgResult.set_cause(e)
        self.messageCallbackExecutors = MessageCallbackTask(bufferedUserMsgResult,
                                                            self.userMessageCallback)
        self.messageCallbackExecutors.start()
        self.logger.warn("partition: " + str(self.partitionId)
                         + " already reach clearMessageQueue limit," +
                         " clear " + str(len(bufferedUserMsgResult.get_message_list()))
                         + " messages in buffer")

    def process_buffered_message(self):
        remainingMessages = self.partitionMessageQueue.get_all_message_list()
        if len(remainingMessages) > 0:
            userMessageResult = UserMessageResult(
                remainingMessages, self.topicAndPartition.topicName, self.partitionId)
            userMessageResult.set_successful(False)
            galaxyTalosException = GalaxyTalosException()
            galaxyTalosException.details = str(self.topicAndPartition) + \
                                           "'s buffer not empty," + \
                                           " do callback when shutdown this partitionSender."
            galaxyTalosException.errMsg = str(self.topicAndPartition) + "'s buffer not empty"
            userMessageResult.set_cause(galaxyTalosException)
            self.messageCallbackExecutors = MessageCallbackTask(userMessageResult,
                                                                self.userMessageCallback)
            self.messageCallbackExecutors.start()

    def shutdown(self):
        # notify PartitionMessageQueue::getMessageList return;
        self.add_message([])
        self.update_state(TASK_STATE.CLOSE)
        self.executor.join()
        self.logger.info("PartitionSender for partition: "
                         + str(self.topicAndPartition.partitionId) + " finish stop")

    def add_message(self, userMessageList=None):
        self.partitionMessageQueue.add_message(userMessageList)
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("add " + str(len(userMessageList)) +
                              " messages to partition: " + str(self.partitionId))

    def close(self):
        self.update_state(TASK_STATE.CLOSE)

    @synchronized
    def get_cur_state(self):
        return self.curState

    def update_state(self, targetState=None):
        self.update_stateLock.acquire()
        try:
            self.logger.info("PartitionSender for Partition: " + str(self.partitionId)
                             + " update status from: " + str(self.curState) + " to: " +
                             str(targetState))
            if targetState == TASK_STATE.ACTIVE:
                self.logger.error("targetState can never be ACTIVE, updateState error for: "
                                  + str(self.partitionId))
                return
            if targetState == TASK_STATE.CLOSE:
                if self.curState == TASK_STATE.ACTIVE:
                    self.curState = TASK_STATE.CLOSE
                else:
                    self.logger.error("targetState is CLOSE, but curState is: " +
                                      str(self.curState) + " for partition: " +
                                      str(self.partitionId))
            return
        except Exception as e:
            self.logger.error("update_state func error: " + traceback.format_exc())
        finally:
            self.update_stateLock.release()

    def is_flush_finish(self):
        messageQueueSize = self.partitionMessageQueue.get_cur_message_bytes()
        if messageQueueSize > 0:
            return False
        else:
            return True

    def get_producer_metrics(self):
        return self.producerMetrics

    def get_falcon_data(self):
        return self.get_producer_metrics().to_json_data()


