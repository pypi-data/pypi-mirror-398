import unittest

from talos.thrift.message.ttypes import Message
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from talos.producer.TalosProducerConfigKey import TalosProducerConfigKeys
from talos.producer.TalosProducer import TalosProducer
from talos.producer.PartitionMessageQueue import PartitionMessageQueue
from talos.producer.UserMessage import UserMessage
from mock import Mock


class test_PartitionMessageQueue(unittest.TestCase):
	msgStr = "hello, partitionMessageQueueTest"
	msg = Message(message=msgStr)

	partitionId = 7
	maxPutMsgNumber = 3
	maxBufferedMillSecs = 200

	producerConfig = TalosClientConfig
	partitionMessageQueue = PartitionMessageQueue
	userMessage1 = UserMessage
	userMessage2 = UserMessage
	userMessage3 = UserMessage
	userMessageList = []
	messageList = []

	producer = Mock(TalosProducer)

	def setUp(self):
		properties = dict()
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER] \
			= self.maxPutMsgNumber
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MILLI_SECS] \
			= self.maxBufferedMillSecs
		properties[TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT] = "testURI"
		self.producerConfig = TalosClientConfig(properties)

		self.userMessage1 = UserMessage(self.msg)
		self.userMessage2 = UserMessage(self.msg)
		self.userMessage3 = UserMessage(self.msg)

		self.partitionMessageQueue = PartitionMessageQueue(self.producerConfig, self.partitionId, self.producer)

	def tearDown(self):
		pass

	def test_add_get_message_when_max_put_number(self):
		self.userMessageList = [self.userMessage1, self.userMessage2]
		self.messageList = [self.msg, self.msg]

		self.producer.increase_buffered_count = Mock(return_value=None)
		self.producer.is_active = Mock(return_value=True)
		self.producer.decrease_buffered_count = Mock(return_value=None)

		self.partitionMessageQueue.add_message(self.userMessageList)
		# check log has waiting time
		self.assertEqual(len(self.messageList), len(self.partitionMessageQueue.get_message_list()))

	def test_add_get_message_when_not_alive(self):
		userMessageList = [self.userMessage1, self.userMessage2, self.userMessage3]
		messageList = [self.msg, self.msg, self.msg]

		self.producer.increase_buffered_count = Mock(return_value=None)
		self.producer.is_active = Mock(side_effect=[True, False])
		self.producer.decrease_buffered_count = Mock(return_value=None)

		self.partitionMessageQueue.add_message(userMessageList)
		# check log has waiting time
		self.assertEqual(len(messageList), len(self.partitionMessageQueue.get_message_list()))
		self.assertEquals(0, len(self.partitionMessageQueue.get_message_list()))

	def test_add_get_wait_message_when_not_alive(self):
		userMessageList = [self.userMessage1, self.userMessage2]
		messageList = [self.msg, self.msg]

		self.producer.increase_buffered_count = Mock(return_value=None)
		self.producer.is_active = Mock(side_effect=[True, True, False])
		self.producer.decrease_buffered_count = Mock(return_value=None)

		self.partitionMessageQueue.add_message(userMessageList)
		# check log has waiting	time
		self.assertEqual(len(messageList), len(self.partitionMessageQueue.get_message_list()))
		self.assertEquals(0, len(self.partitionMessageQueue.get_message_list()))


if __name__ == '__main__':
	unittest.main()
