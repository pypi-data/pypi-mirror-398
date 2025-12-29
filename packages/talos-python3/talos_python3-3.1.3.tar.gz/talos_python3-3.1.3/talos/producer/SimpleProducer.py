# -*- coding:utf8 -*-
#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.compression.Compression import Compression
from talos.client.TalosClientFactory import TalosClientFactory
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.thrift.topic.TopicService import GetDescribeInfoRequest
from talos.thrift.message import MessageService
from talos.thrift.message.ttypes import MessageType
from talos.thrift.message.ttypes import PutMessageRequest
from talos.client.ScheduleInfoCache import ScheduleInfoCache
from talos.thrift.transport.TSocket import TTransportException
from atomic import AtomicLong
from talos.utils import Utils
import logging
import traceback


class SimpleProducer(object):
    logger = logging.getLogger("SimpleConsumer")

    producerConfig = TalosClientConfig
    topicAndPartition = TopicAndPartition
    messageClient = MessageService.Iface
    talosClientFactory = TalosClientFactory
    requestId = AtomicLong
    clientId = str
    isActive = bool

    def __init__(self, producerConfig=None, topicName=None, topicAndPartition=None,
                 partitionId=None, credential=None, talosClientFactory=None,
                 messageClient=None, clientId=None, requestId=None):
        if talosClientFactory:
            self.talosClientFactory = talosClientFactory
        elif credential:
            self.talosClientFactory = TalosClientFactory(producerConfig, credential)
        if topicName:
            Utils.check_topic_name(topicName)
            self.get_topic_info(self.talosClientFactory.new_topic_client(), topicName,
                                partitionId)
        else:
            self.topicAndPartition = topicAndPartition
        self.producerConfig = producerConfig
        if messageClient:
            self.messageClient = messageClient
        else:
            self.messageClient = self.talosClientFactory.new_message_client()
        if clientId:
            self.clientId = clientId
        else:
            self.clientId = Utils.generate_client_id('SimpleProducer', '')
        if requestId:
            self.requestId = requestId
        else:
            self.requestId = AtomicLong(1)
        self.scheduleInfoCache = ScheduleInfoCache().get_schedule_info_cache(
            topicTalosResourceName=self.topicAndPartition.topicTalosResourceName,
            talosClientConfig=self.producerConfig, messageClient=self.messageClient,
            talosClientFactory=self.talosClientFactory)
        self.isActive = True

    def get_topic_info(self, topicClient=None, topicName=None, partitionId=None):
        response = topicClient.get_describe_info(GetDescribeInfoRequest(topicName))
        self.topicAndPartition = TopicAndPartition(topicName=topicName,
                                                   topicTalosResourceName=response.topicTalosResourceName,
                                                   partitionId=partitionId)

    def put_message(self, msgList=None):
        if (not msgList) or len(msgList) == 0:
            return True

        try:
            self.put_message_list(msgList)
            return True
        except Exception as e:
            self.logger.error("putMessage to " + str(self.topicAndPartition) + " error， please try to put again"
                              + str(traceback.format_exc()))

        return False

    def put_message_list(self, msgList=None):
        if (not msgList) or len(msgList) == 0:
            return

        # check data validity
        for message in msgList:
            # set timestamp and messageType if not set
            Utils.update_message(message, MessageType.BINARY)

        # check data validity
        Utils.check_message_list_validity(msgList, self.producerConfig)

        self.do_put(msgList)

    def do_put(self, msgList=None):
        messageBlock = self._compress_message_list(msgList)
        messageBlockList = [messageBlock]

        requestSequenceId = Utils.generate_request_sequence_id(self.clientId,
                                                               self.requestId)
        putMessageRequest = PutMessageRequest(self.topicAndPartition, messageBlockList,
                                              len(msgList), requestSequenceId)
        try:
            putMessageResponse = self.scheduleInfoCache.get_or_create_message_client(
                topicAndPartition=self.topicAndPartition).put_message(putMessageRequest)
        except Exception as e:
            if isinstance(e, TTransportException):
                if not self.scheduleInfoCache and self.scheduleInfoCache.get_is_auto_location():
                    self.logger.warn(
                        "can't connect to the host directly, refresh scheduleInfo and retry using url. "
                        + "The exception message is :" + e.message +
                        ". Ignore this if not frequently.")
                    self.scheduleInfoCache.update_schedule_info_cache()
                    putMessageResponse = self.messageClient.put_message(putMessageRequest)
                else:
                    self.logger.error("put message request to " + str(self.topicAndPartition) + " failed." + str(traceback.format_exc()))
                    raise e
            else:
                self.logger.error(
                    "put message request to " + str(self.topicAndPartition) + " failed." + str(traceback.format_exc()))
                raise e

        # update scheduleInfocache when request have been transfered and talos auto location was set up
        if self.scheduleInfoCache and self.scheduleInfoCache.get_is_auto_location():
            if putMessageResponse and putMessageResponse.isTransfer:
                self.logger.info("request has been transfered when talos auto location set up, refresh scheduleInfo")
                self.scheduleInfoCache.update_schedule_info_cache()

    def _compress_message_list(self, msgList=None):
        return Compression().compress(msgList, self.producerConfig.get_compression_type())

    def shut_down(self):
        if not self.isActive:
            self.logger.info("SimpleProducer which clientId is: " + str(self.clientId)
                             + " is already shutdown, don't do it again.")
            return

        self.scheduleInfoCache.shut_down(self.topicAndPartition.topicTalosResourceName)
        self.isActive = False




