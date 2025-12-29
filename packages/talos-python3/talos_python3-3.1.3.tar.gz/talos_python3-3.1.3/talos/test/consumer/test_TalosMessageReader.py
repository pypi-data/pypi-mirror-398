#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

import unittest

from talos.thrift.message.ttypes import MessageAndOffset
from talos.thrift.message.ttypes import Message
from talos.thrift.consumer.ttypes import UpdateOffsetResponse
from talos.thrift.consumer.ttypes import QueryOffsetResponse
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.consumer.SimpleConsumer import SimpleConsumer
from talos.consumer.TalosMessageReader import TalosMessageReader
from talos.consumer.MessageProcessor import MessageProcessor
from talos.client.TalosClientFactory import ConsumerClient
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from mock import Mock


class TestMessageProcessor(MessageProcessor):
    topicAndPartition = TopicAndPartition
    messageOffset = long

    def init(self, topicAndPartition=None, messageOffset=None):
        self.topicAndPartition = topicAndPartition
        self.messageOffset = messageOffset

    def process(self, messages=None, messageCheckpointer=None):
        assert messageCheckpointer.checkpoint()
        # checkpoint low messageOffset
        assert not messageCheckpointer.checkpoint(self.messageOffset)
        # checkpoint high messageOffset
        assert not messageCheckpointer.checkpoint(messages.get(messages.size()-1).getMessageOffset())

    def shutdown(self, messageCheckpointer=None):
        assert not messageCheckpointer.checkpoint()

    def get_topic_and_partition(self):
        return self.topicAndPartition

    def get_message_offset(self):
        return self.messageOffset


class test_TalosMessageReader(unittest.TestCase):
    properties = dict()
    consumerConfig = TalosClientConfig
    topicName = "MyTopic"
    resourceName = "12345#MyTopic#34595fkdiso456i390"
    partitionId = 7
    consumerGroup = "MyConsumerGroup"
    workerId = "workerId"
    topicAndPartition = TopicAndPartition(topicName, TopicTalosResourceName(resourceName), partitionId)
    startMessageOffset = 1

    messageAndOffsetList = []
    messageAndOffsetList2 = []
    consumerClientMock = ConsumerClient
    simpleConsumerMock = SimpleConsumer

    messageProcessor = TestMessageProcessor()
    messageProcessorMock = TestMessageProcessor()
    messageReader = TalosMessageReader()

    def setUp(self):
        messageAndOffset1 = MessageAndOffset(Message("message1"), self.startMessageOffset)
        messageAndOffset2 = MessageAndOffset(Message("message2"), self.startMessageOffset + 1)
        messageAndOffset3 = MessageAndOffset(Message("message3"), self.startMessageOffset + 2)
        self.messageAndOffsetList = [messageAndOffset1, messageAndOffset2, messageAndOffset3]
        messageAndOffset4 = MessageAndOffset(Message("message4"), self.startMessageOffset + 3)
        messageAndOffset5 = MessageAndOffset(Message("message5"), self.startMessageOffset + 4)
        self.messageAndOffsetList2 = [messageAndOffset4, messageAndOffset5]

        self.consumerClientMock = ConsumerClient

    def test_DefaultCheckpointOffset(self):
        talosConfigKeys = TalosClientConfigKeys()
        self.properties[talosConfigKeys.GALAXY_TALOS_CONSUMER_CHECKPOINT_AUTO_COMMIT] = True
        self.properties[talosConfigKeys.GALAXY_TALOS_CONSUMER_FETCH_INTERVAL] = 0
        self.properties[talosConfigKeys.GALAXY_TALOS_CONSUMER_COMMIT_OFFSET_INTERVAL] = 0
        self.properties[talosConfigKeys.GALAXY_TALOS_CONSUMER_COMMIT_OFFSET_THRESHOLD] = 0
        self.properties[TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT] = "testURI"
        self.consumerConfig = TalosClientConfig(self.properties)

        self.messageProcessorMock = TestMessageProcessor()
        messageReader = TalosMessageReader(consumerConfig=self.consumerConfig)
        messageReader.set_simple_consumer(self.simpleConsumerMock)
        messageReader.set_consumer_client(self.consumerClientMock)
        messageReader.set_consumer_group(self.consumerGroup)
        messageReader.set_message_processor(self.messageProcessorMock)
        messageReader.set_topic_and_partition(self.topicAndPartition)
        messageReader.set_worker_id(self.workerId)

        self.messageProcessorMock.init(topicAndPartition=self.topicAndPartition,
                                       messageOffset=self.startMessageOffset)
        queryOffsetResponse = QueryOffsetResponse(self.startMessageOffset - 1)
        self.consumerClientMock.query_offset = Mock(return_value=queryOffsetResponse)
        self.simpleConsumerMock.fetch_message = Mock(side_effect=[self.messageAndOffsetList, self.messageAndOffsetList2])
        self.messageProcessorMock.process = Mock(return_value=None)
        updateOffsetResponse = UpdateOffsetResponse(True)
        self.consumerClientMock.update_offset = Mock(return_value=updateOffsetResponse)
        self.messageProcessorMock.shutdown = Mock(return_value=None)

        messageReader.init_start_offset()
        messageReader.fetch_data()
        messageReader.fetch_data()
        messageReader.commit_check_point()

    def test_UserCheckpointOffset(self):
        self.properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_CHECKPOINT_AUTO_COMMIT] = False
        self.properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_FETCH_INTERVAL] = 0
        self.properties[TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT] = "testURI"
        consumerConfig = TalosClientConfig(self.properties)

        messageReader = TalosMessageReader(consumerConfig)
        messageReader.set_simple_consumer(self.simpleConsumerMock)
        messageReader.set_consumer_client(self.consumerClientMock)
        messageReader.set_consumer_group(self.consumerGroup)
        messageReader.set_message_processor(self.messageProcessor)
        messageReader.set_topic_and_partition(self.topicAndPartition)
        messageReader.set_worker_id(self.workerId)

        queryOffsetResponse = QueryOffsetResponse(self.startMessageOffset - 1)
        self.consumerClientMock.query_offset = Mock(return_value=queryOffsetResponse)
        messageReader.init_start_offset()
        self.assertEquals(self.messageProcessor.get_message_offset(), self.startMessageOffset)
        self.assertEquals(self.messageProcessor.get_topic_and_partition(), self.topicAndPartition)

        self.simpleConsumerMock.fetch_message = self.messageAndOffsetList
        updateOffsetResponse = UpdateOffsetResponse(True)
        self.consumerClientMock.update_offset = Mock(return_value=updateOffsetResponse)
        self.simpleConsumerMock.fetch_message = self.messageAndOffsetList2

        messageReader.fetch_data()
        messageReader.fetch_data()
        messageReader.commit_check_point()


if __name__ == '__main__':
    unittest.main()
