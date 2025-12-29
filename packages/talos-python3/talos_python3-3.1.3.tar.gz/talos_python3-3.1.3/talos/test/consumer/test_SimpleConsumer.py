#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

import unittest

from talos.thrift.message.ttypes import MessageAndOffset
from talos.thrift.message.ttypes import Message
from talos.thrift.consumer.ttypes import UpdateOffsetResponse
from talos.thrift.consumer.ttypes import LockPartitionResponse
from talos.thrift.consumer.ttypes import QueryOffsetResponse
from talos.thrift.consumer.ttypes import QueryOffsetRequest
from talos.thrift.consumer.ttypes import UpdateOffsetRequest
from talos.thrift.consumer.ttypes import CheckPoint
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.thrift.common.ttypes import GalaxyTalosException
from talos.thrift.common.ttypes import ErrorCode
from talos.consumer.SimpleConsumer import SimpleConsumer
from talos.consumer.MessageReader import MessageReader
from talos.consumer.TalosMessageReader import TalosMessageReader
from talos.consumer.PartitionFetcher import PartitionFetcher
from talos.consumer.MessageProcessor import MessageProcessor
from talos.client.TalosClientFactory import ConsumerClient
from talos.client.TalosClientFactory import MessageClient
from talos.client.TalosClientFactory import TopicClient
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from mock import Mock
import time


class test_SimpleConsumer(unittest.TestCase):
    topicName = "MyTopic"
    resourceName = "12345#MyTopic#34595fkdiso456i390"
    talosResourceName = TopicTalosResourceName(resourceName)
    partitionId = 7
    partitionNum = 10
    startOffset = 0
    topicAndPartition = TopicAndPartition
    producerConfig = TalosClientConfig
    consumerConfig = TalosClientConfig
    messageClientMock = MessageClient
    topicClientMock = TopicClient
    messageList = []
    messageAndOffsetList = []
    simpleConsumer = SimpleConsumer
