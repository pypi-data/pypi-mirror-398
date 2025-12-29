#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientConfig import TalosClientConfigKeys
from talos.thrift.auth.ttypes import Credential
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.utils import Utils
from talos.client.TalosClientFactory import TalosClientFactory
from talos.client.TalosClientFactory import MessageClient
from talos.thrift.topic.TopicService import GetDescribeInfoRequest
from talos.thrift.message.MessageService import GetMessageRequest
from talos.thrift.message.MessageService import GetMessageResponse
from atomic import AtomicLong
from talos.client.compression.Compression import Compression
from talos.thrift.transport.TSocket import TTransportException
from talos.thrift.message.ttypes import MessageOffset
from talos.client.ScheduleInfoCache import ScheduleInfoCache
import traceback
import logging


class SimpleConsumer:
    logger = logging.getLogger("SimpleConsumer")
    consumerConfig = TalosClientConfig
    topicName = str
    partitionId = int
    credential = Credential
    topicAndPartition = TopicAndPartition
    messageClient = MessageClient
    simpleConsumerId = str
    requestId = AtomicLong

    def __init__(self, clientConfig=None, topicName=None, partitionId=None,
                 topicAndPartition=None, credential=None, messageClient=None):
        self.consumerConfig = clientConfig
        self.talosClientFactory = TalosClientFactory(clientConfig, credential)
        if topicName:
            Utils.check_topic_name(topicName)
            self.topicName = topicName
            self.partitionId = partitionId
            self.credential = credential
            self.messageClient = self.talosClientFactory.new_message_client()
            self.get_topic_info(self.talosClientFactory.new_topic_client(), topicName,
                                partitionId)
        else:
            self.messageClient = messageClient
            self.topicAndPartition = topicAndPartition
        self.simpleConsumerId = Utils.generate_client_id(clientConfig.get_client_ip(), "")
        self.requestId = AtomicLong(1)
        self.scheduleInfoCache = ScheduleInfoCache().get_schedule_info_cache(
            topicTalosResourceName=self.topicAndPartition.topicTalosResourceName,
            talosClientConfig=self.consumerConfig, messageClient=self.messageClient,
            talosClientFactory=self.talosClientFactory)
        self.isActive = True

    def get_topic_info(self, topicClient=None, topicName=None, partitionId=None):
        response = topicClient.get_describe_info(GetDescribeInfoRequest(topicName))
        self.topicAndPartition = TopicAndPartition(topicName,
                                                   response.topicTalosResourceName,
                                                   partitionId)

    def get_topic_talos_resource_name(self):
        return self.topicAndPartition.topicTalosResourceName

    def set_simple_consumer_id(self, simpleConsumerId=None):
        self.simpleConsumerId = simpleConsumerId

    def fetch_message(self, startOffset=None, maxFetchedNumber=None):
        Utils.check_start_offset_validity(startOffset)
        Utils.check_start_offset_validity(startOffset)
        Utils.check_parameter_range(TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_RECORDS,
                                    maxFetchedNumber,
                                    TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_RECORDS_MINIMUM,
                                    TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_RECORDS_MAXIMUM)
        requestSequenceId = Utils.generate_request_sequence_id(self.simpleConsumerId,
                                                               self.requestId)

        # limit the default max fetch bytes 2M
        getMessageRequest = GetMessageRequest(self.topicAndPartition, startOffset)
        getMessageRequest.sequenceId = requestSequenceId
        getMessageRequest.maxGetMessageNumber = maxFetchedNumber
        getMessageRequest.maxGetMessageBytes = self.consumerConfig.get_max_fetch_msg_bytes()
        clientTimeout = self.consumerConfig.get_client_timeout()
        getMessageRequest.timeoutTimestamp = (Utils.current_time_mills() + clientTimeout)

        getMessageResponse = GetMessageResponse(messageBlocks=[])
        try:
            getMessageResponse = self.scheduleInfoCache.get_or_create_message_client(
                topicAndPartition=self.topicAndPartition).get_message(getMessageRequest)
        except Exception as e:
            if isinstance(e, TTransportException) or isinstance(e, ConnectionRefusedError):
                if self.scheduleInfoCache and self.scheduleInfoCache.get_is_auto_location():
                    self.logger.warn("can't connect to the host directly, refresh scheduleInfo and retry using url. "
                                     + "The exception message is : %s. Ignore this if not frequently.", e)
                    self.scheduleInfoCache.update_schedule_info_cache()
                    getMessageResponse = self.messageClient.get_message(getMessageRequest)
                else:
                    self.logger.error("fetch message failed! " + str(traceback.format_exc()))
                    raise e
            else:
                self.logger.error("fetch message failed! " + str(traceback.format_exc()))
                raise e

        # update scheduleInfocache when request have been transfered and talos auto location was set up
        if self.scheduleInfoCache and self.scheduleInfoCache.get_is_auto_location():
            if getMessageResponse and getMessageResponse.isTransfer:
                self.logger.info("request has been transfered when talos auto location set up, refresh scheduleInfo")
                self.scheduleInfoCache.update_schedule_info_cache()

        messageAndOffsetList = Compression().decompress(getMessageResponse.messageBlocks,
                                                        getMessageResponse.unHandledMessageNumber)

        if len(messageAndOffsetList) <= 0:
            return messageAndOffsetList

        actualStartOffset = messageAndOffsetList[0].messageOffset

        if messageAndOffsetList[0].messageOffset == startOffset or startOffset == \
                MessageOffset.START_OFFSET or startOffset == MessageOffset.LATEST_OFFSET:
            return messageAndOffsetList
        else:
            start = int(startOffset - actualStartOffset)
            try:
                assert start > 0
            except AssertionError as e:
                self.logger.error("Exception in fetch_message: %s", e)
                raise e
            end = len(messageAndOffsetList)
            return messageAndOffsetList[start:end]

    def shut_down(self):
        if not self.isActive:
            self.logger.info("SimpleConsumer which simpleConsumerId is: " + str(self.simpleConsumerId) +
                             " is already shutdown, don't do it again.")
            return
        self.logger.info("consumer of " + self.topicAndPartition.topicTalosResourceName + " is shutting down.")
        self.scheduleInfoCache.shut_down(self.topicAndPartition.topicTalosResourceName)
        self.logger.info("consumer of " + self.topicAndPartition.topicTalosResourceName + " shutdown.")
        self.isActive = False

