import unittest

from talos.thrift.message.ttypes import MessageAndOffset
from talos.thrift.message.ttypes import Message
from talos.thrift.consumer.ttypes import UpdateOffsetResponse
from talos.thrift.consumer.ttypes import LockPartitionResponse
from talos.thrift.consumer.ttypes import QueryOffsetResponse
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.common.ttypes import GalaxyTalosException
from talos.thrift.common.ttypes import ErrorCode
from talos.consumer.SimpleConsumer import SimpleConsumer
from talos.consumer.MessageReader import MessageReader
from talos.consumer.PartitionFetcher import PartitionFetcher
from talos.client.TalosClientFactory import ConsumerClient
from mock import Mock
import time


class test_PartitionFetcher(unittest.TestCase):
    topicName = "MyTopic"
    resourceName = "12345#MyTopic#34595fkdiso456i390"
    partitionId = 7
    consumerGroup = "MyConsumerGroup"
    workerId = "workerId"

    def setUp(self):
        messageAndOffset1 = MessageAndOffset(Message("message1"), 1)
        messageAndOffset2 = MessageAndOffset(Message("message2"), 2)
        messageAndOffset3 = MessageAndOffset(Message("message3"), 3)
        messageAndOffsetList = [messageAndOffset1, messageAndOffset2, messageAndOffset3]
        messageAndOffset4 = MessageAndOffset(Message("message4"), 4)
        messageAndOffset5 = MessageAndOffset(Message("message5"), 5)
        messageAndOffsetList2 = [messageAndOffset4, messageAndOffset5]

        self.consumerClientMock = ConsumerClient
        self.simpleConsumerMock = SimpleConsumer
        self.messageReaderMock = Mock(MessageReader)

        self.partitionFetcher = PartitionFetcher(consumerGroup=self.consumerGroup,
                                                 topicName=self.topicName,
                                                 topicTalosResourceName=TopicTalosResourceName(self.resourceName),
                                                 partitionId=self.partitionId,
                                                 workerId=self.workerId,
                                                 consumerClient=self.consumerClientMock,
                                                 simpleConsumer=self.simpleConsumerMock,
                                                 messageReader=self.messageReaderMock)

        # mock value for simpleConsumerMock and consumerClientMock
        self.simpleConsumerMock.fetch_message = Mock(side_effect=[messageAndOffsetList, messageAndOffsetList2])
        self.consumerClientMock.update_offset = Mock(return_value=UpdateOffsetResponse(True))
        self.consumerClientMock.unlock_partition = Mock(return_value=None)

        successPartitionList = [self.partitionId]
        lockPartitionResponse = LockPartitionResponse(successPartitionList)
        self.consumerClientMock.lock_partition = Mock(return_value=lockPartitionResponse)
        queryOffsetResponse = QueryOffsetResponse(0)
        self.consumerClientMock.query_offset = Mock(return_value=queryOffsetResponse)

    def tearDown(self):
        self.partitionFetcher.shutdown()

    def test_LockFailedFromLockedToUnlocked(self):
        self.consumerClientMock.lock_partition = Mock(side_effect=Exception())

        self.partitionFetcher.lock()
        # sleep to wait stealing lock failed
        time.sleep(0.04)
        self.assertEqual(False, self.partitionFetcher.is_serving())

    def test_LockFailedWhenNullSuccessList(self):
        successPartitionList = []
        lockPartitionResponse = LockPartitionResponse(successPartitionList)
        self.consumerClientMock.lock_partition = Mock(return_value=lockPartitionResponse)

        self.partitionFetcher.lock()
        # sleep to wait lock
        time.sleep(0.05)
        self.assertEqual(False, self.partitionFetcher.is_serving())

    def test_LockFailedWhenGetStartOffset(self):
        self.messageReaderMock.init_start_offset = Mock(side_effect=Exception)

        self.partitionFetcher.lock()
        time.sleep(0.05)
        self.assertEqual(False, self.partitionFetcher.is_serving())

    def test_GetMessageAndCommitOffset(self):
        self.partitionFetcher.lock()
        self.assertEqual(True, self.partitionFetcher.is_holding_lock())
        time.sleep(0.1)
        self.assertEqual(True, self.partitionFetcher.is_holding_lock())
        self.partitionFetcher.unlock()
        self.assertEqual(True, self.partitionFetcher.is_holding_lock())
        time.sleep(0.05)
        self.assertEqual(False, self.partitionFetcher.is_serving())

    def test_CallGetMessageMultipleTimesAndCommitOffset(self):
        self.partitionFetcher.lock()
        self.assertEqual(True, self.partitionFetcher.is_holding_lock())
        time.sleep(0.5)
        self.assertEqual(True, self.partitionFetcher.is_holding_lock())
        self.partitionFetcher.unlock()

    def test_PartitionNotServing(self):
        self.simpleConsumerMock.fetch_message = Mock(side_effect=GalaxyTalosException(
            errorCode=ErrorCode.PARTITION_NOT_SERVING))
        self.partitionFetcher.lock()
        time.sleep(0.5)

    def test_OffsetOutOfRange(self):
        self.simpleConsumerMock.fetch_message = Mock(side_effect=GalaxyTalosException(
            errorCode=ErrorCode.MESSAGE_OFFSET_OUT_OF_RANGE))
        self.partitionFetcher.lock()
        time.sleep(0.5)

    def test_LockLock(self):
        self.partitionFetcher.lock()
        time.sleep(0.05)
        self.partitionFetcher.lock()
        time.sleep(0.05)

    def testUnlockUnlock(self):
        self.partitionFetcher.lock()
        self.partitionFetcher.unlock()
        time.sleep(0.05)
        self.partitionFetcher.unlock()

    def test_UnlockLock(self):
        self.partitionFetcher.lock()
        self.partitionFetcher.unlock()
        self.partitionFetcher.lock()


if __name__ == '__main__':
    unittest.main()
