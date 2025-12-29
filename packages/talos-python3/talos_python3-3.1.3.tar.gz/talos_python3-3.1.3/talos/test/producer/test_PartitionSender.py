import unittest
from talos.producer.UserMessageCallback import UserMessageCallback
from talos.producer.TalosProducerConfigKey import TalosProducerConfigKeys
from talos.producer.UserMessage import UserMessage
from talos.producer.TalosProducer import TalosProducer
from talos.producer.PartitionSender import PartitionSender
from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from talos.client.TalosClientFactory import MessageClient
from talos.client.TalosClientConfig import TalosClientConfig
from talos.thrift.message.ttypes import Message
from talos.thrift.message.ttypes import MessageType
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.message.ttypes import PutMessageResponse
from talos.thrift.common.ttypes import GalaxyTalosException
from mock import Mock
from atomic import AtomicLong
from talos.utils import Utils
import threading
import logging

msgPutSuccessCount = 0
msgPutFailureCount = 0


def clearCounter():
	global msgPutFailureCount
	msgPutFailureCount = 0
	global msgPutSuccessCount
	msgPutSuccessCount = 0


class MessageCallback(UserMessageCallback):

	def on_success(self, userMessageResult=None):
		global msgPutSuccessCount
		test = msgPutSuccessCount
		msgPutSuccessCount += len(userMessageResult.get_message_list())

	def on_error(self, userMessageResult=None):
		global msgPutFailureCount
		msgPutFailureCount += len(userMessageResult.get_message_list())


class test_PartitionSender(unittest.TestCase):
	logging.basicConfig()

	producerMaxBufferedMillSecs = 0.01
	producerMaxPutMsgNumber = 5
	producerMaxPutMsgBytes = 50
	producerMaxBufferedMsgNum = 50

	resourceName0 = "12345#TopicName#july7777770009990"
	resourceName1 = "12345#TopicName#july7777770009991"
	resourceName2 = "12345#TopicName#july7777770009992"
	resourceName3 = "12345#TopicName#july7777770009993"

	topicName = "TopicName"
	partitionId = 0
	requestId = AtomicLong(1)
	globalLock = threading.Condition()

	def setUp(self):
		properties = dict()
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MILLI_SECS] \
			= self.producerMaxBufferedMillSecs
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER] \
			= self.producerMaxPutMsgNumber
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES] \
			= self.producerMaxPutMsgBytes
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MESSAGE_NUMBER] \
			= self.producerMaxBufferedMsgNum
		properties[TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT] = "testURI"
		self.talosProducerConfig = TalosClientConfig(properties)

		self.talosResourceName0 = TopicTalosResourceName(self.resourceName0)
		self.talosResourceName1 = TopicTalosResourceName(self.resourceName1)
		self.talosResourceName2 = TopicTalosResourceName(self.resourceName2)
		self.talosResourceName3 = TopicTalosResourceName(self.resourceName3)
		self.messageCallback = MessageCallback()
		self.messageCallbackExecutors = threading.Thread()
		self.messageClientMock = Mock(MessageClient)
		self.producerMock = Mock(TalosProducer)

		self.userMessageList = []
		timestamp = Utils.current_time_mills()
		self.userMessage1 = UserMessage(Message(message="hello", createTimestamp=timestamp, messageType=MessageType.BINARY))
		self.userMessage2 = UserMessage(Message(message="world", createTimestamp=timestamp, messageType=MessageType.BINARY))
		self.userMessage3 = UserMessage(Message(message="nice day", createTimestamp=timestamp, messageType=MessageType.BINARY))
		self.userMessage4 = UserMessage(Message(message="good guy", createTimestamp=timestamp, messageType=MessageType.BINARY))

	def tearDown(self):
		pass

	def test_partition_sender_success_put(self):
		self.userMessageList = [self.userMessage1, self.userMessage2, self.userMessage3, self.userMessage4]

		self.messageClientMock.put_message = Mock(return_value=PutMessageResponse())
		# self.producerMock.is_active = Mock(side_effect=[True, True,True, True, True, False])
		self.producerMock.is_active = Mock(return_value=True)
		self.producerMock.is_disabled = Mock(return_value=False)

		partitionSender = PartitionSender(partitionId=self.partitionId,
										  topicName=self.topicName,
										  topicTalosResourceName=self.talosResourceName1,
										  requestId=self.requestId,
										  clientId=Utils.generate_client_id(clientIp=self.talosProducerConfig.get_client_ip(), prefix=""),
										  talosProducerConfig=self.talosProducerConfig,
										  messageClient=self.messageClientMock,
										  userMessageCallback=self.messageCallback,
										  messageCallbackExecutors=self.messageCallbackExecutors,
										  globalLock=self.globalLock,
										  producer=self.producerMock)
		addCount = 1
		while addCount > 0:
			partitionSender.add_message(self.userMessageList)
			addCount -= 1

		partitionSender.shutdown()

		global msgPutSuccessCount
		self.assertEqual(4, msgPutSuccessCount)
		clearCounter()

	def test_partition_sender_failed_put(self):
		self.userMessageList = [self.userMessage1, self.userMessage2,
								self.userMessage3, self.userMessage4]

		self.messageClientMock.put_message = Mock(side_effect=GalaxyTalosException(errMsg="put failed"))
		self.producerMock.is_active = Mock(side_effect=[True, False])

		partitionSender = PartitionSender(partitionId=self.partitionId,
										  topicName=self.topicName,
										  topicTalosResourceName=self.talosResourceName1,
										  requestId=self.requestId,
										  clientId=Utils.generate_client_id(clientIp=self.talosProducerConfig.get_client_ip(), prefix=""),
										  talosProducerConfig=self.talosProducerConfig,
										  messageClient=self.messageClientMock,
										  userMessageCallback=self.messageCallback,
										  messageCallbackExecutors=self.messageCallbackExecutors,
										  globalLock=self.globalLock,
										  producer=self.producerMock)
		partitionSender.add_message(self.userMessageList)

		partitionSender.shutdown()
		self.assertEquals(0, msgPutSuccessCount)
		self.assertEquals(4, msgPutFailureCount)
		clearCounter()

	def testPartitionQueueWaitToPut(self):
		pass

	def testPartitiionNotServingDelay(self):
		pass


if __name__ == '__main__':
	unittest.main()
