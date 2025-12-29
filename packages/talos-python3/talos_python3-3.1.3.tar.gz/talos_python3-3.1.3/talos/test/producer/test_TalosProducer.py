import unittest
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.topic.ttypes import Topic
from talos.thrift.topic.ttypes import GetDescribeInfoResponse
from talos.thrift.topic.ttypes import GetTopicAttributeResponse
from talos.thrift.topic.ttypes import TopicAttribute
from talos.thrift.message.ttypes import Message
from talos.thrift.message.ttypes import PutMessageResponse
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientFactory import TalosClientFactory
from talos.client.TalosClientFactory import MessageClient
from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from talos.client.SimpleAbnormalCallback import SimpleAbnormalCallback
from talos.admin.TalosAdmin import TalosAdmin
from talos.producer.TalosProducer import TalosProducer
from talos.producer.PartitionSender import PartitionSender
from talos.producer.UserMessageCallback import UserMessageCallback
from talos.producer.TalosProducerConfigKey import TalosProducerConfigKeys
from talos.utils.Utils import synchronized
from random import Random
from mock import Mock
import time

base = "abcdefgh ijklmnopqr stuvwxyz 0123456789"


# generate random string as message for putMessage
def get_random_string(self, randomStrLen=None):
	random = Random()
	stringBuffer = ""

	i = 0
	while i < randomStrLen:
		number = random.randint(0, len(base))
		stringBuffer += base[number]
		i += 1
	return stringBuffer


@synchronized
def add_success_counter(self, counter=None):
	self.msgPutSuccessCount += counter


@synchronized
def add_failure_counter(self, counter=None):
	self.msgPutFailureCount += counter


class TestCallback(UserMessageCallback):
	def on_success(self, userMessageResult=None):
		add_success_counter(counter=len(userMessageResult.get_message_list()))

	def on_error(self, userMessageResult=None):
		add_failure_counter(counter=len(userMessageResult.get_message_list()))


class test_TalosProducer(unittest.TestCase):
	resourceName = "12345#TopicName#july777777000999"
	anotherResourceName = "12345#TopicName#july777777000629"
	topicName = "TopicName"
	ownerId = "12345"
	messageRetentionMs = 1
	partitionNumber = 8
	partitionNumber2 = 16
	randomStrLen = 15
	producerMaxBufferedMillSecs = 0.01
	producerMaxPutMsgNumber = 10
	producerMaxPutMsgBytes = 100
	checkPartitionInterval = 0.2
	talosResourceName = TopicTalosResourceName(topicTalosResourceName=resourceName)

	talosProducerConfig = TalosClientConfig
	talosProducer = TalosProducer
	messageList = []
	topic = Topic

	talosAdminMock = TalosAdmin
	talosClientFactoryMock = TalosClientFactory
	messageClientMock = MessageClient
	partitionSenderMock = PartitionSender
	msgPutSuccessCount = int
	msgPutFailureCount = int

	def setUp(self):
		# set properties
		properties = dict()
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MILLI_SECS] = \
			self.producerMaxBufferedMillSecs
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER] = \
			self.producerMaxPutMsgNumber
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES] = \
			self.producerMaxPutMsgBytes
		properties[TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL] = \
			self.checkPartitionInterval
		properties[TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT] = "testURI"
		self.talosProducerConfig = TalosClientConfig(properties)

		# construct a getDescribeInfoResponse
		self.getDescribeInfoResponse = GetDescribeInfoResponse(TopicTalosResourceName(
			topicTalosResourceName=self.talosResourceName), self.partitionNumber)

		# construct a getTopicAttributeResponse
		self.getTopicAttributeResponse = GetTopicAttributeResponse(self.talosResourceName,
																   TopicAttribute(partitionNumber=self.partitionNumber))

		# mock some return value
		self.talosAdminMock = Mock(TalosAdmin)
		self.talosClientFactoryMock = Mock(TalosClientFactory)
		self.messageClientMock = Mock(MessageClient)
		self.partitionSenderMock = Mock(PartitionSender)

		# generate 100 random messages
		messageList = []
		i = 0
		while i < 100:
			messageList.append(Message(get_random_string(self.randomStrLen)))
			i += 1

		# mock putMessageResponse
		self.msgPutFailureCount = 0
		self.msgPutSuccessCount = 0

		self.talosClientFactoryMock.new_message_client = Mock(return_value=self.messageClientMock)
		self.messageClientMock.put_message = Mock(return_value=PutMessageResponse())
		self.talosAdminMock.get_describe_info = Mock(return_value=self.getDescribeInfoResponse)
		self.talosAdminMock.get_topic_attribute = Mock(return_value=self.getTopicAttributeResponse)

	def tearDown(self):
		pass

	def test_asynchronously_addUser_message(self):
		self.talosProducer = TalosProducer(producerConfig=self.talosProducerConfig,
										   topicName=self.topicName,
										   topicTalosResourceName=TopicTalosResourceName(topicTalosResourceName=self.talosResourceName),
										   talosAdmin=self.talosAdminMock,
										   talosClientFactory=self.talosClientFactoryMock,
										   topicAbnormalCallback=SimpleAbnormalCallback(),
										   userMessageCallback=TestCallback())

		self.talosProducer.add_user_message(self.messageList)
		# wait for execute finished
		time.sleep(self.producerMaxBufferedMillSecs * 10)

	def test_producer_not_active_error(self):
		getDescribeInfoResponse = GetDescribeInfoResponse(TopicTalosResourceName(
			TopicTalosResourceName(self.talosResourceName)), self.partitionNumber)
		getDescribeInfoResponse2 = GetDescribeInfoResponse(TopicTalosResourceName(
			TopicTalosResourceName(self.anotherResourceName)), self.partitionNumber)
		self.talosAdminMock.get_describe_info = Mock(side_effcet=[getDescribeInfoResponse, getDescribeInfoResponse2])

		self.partitionSenderMock.shutdown = Mock(return_value=None)

		self.talosProducer = TalosProducer(producerConfig=self.talosProducerConfig,
										   topicName=self.topicName,
										   topicTalosResourceName=TopicTalosResourceName(topicTalosResourceName=self.talosResourceName),
										   talosAdmin=self.talosAdminMock,
										   talosClientFactory=self.talosClientFactoryMock,
										   topicAbnormalCallback=SimpleAbnormalCallback(),
										   userMessageCallback=TestCallback())

		# wait check partition interval
		time.sleep(self.checkPartitionInterval * 2)

		self.partitionSenderMock.add_message = Mock(return_value=None)
		self.talosProducer.add_user_message(self.messageList)

	# check partition change when producer running
	def test_partition_change_during_producer_running(self):
		getDescribeInfoResponse = GetDescribeInfoResponse(TopicTalosResourceName(
			TopicTalosResourceName(self.talosResourceName)), self.partitionNumber)
		getDescribeInfoResponse2 = GetDescribeInfoResponse(TopicTalosResourceName(
			TopicTalosResourceName(self.anotherResourceName)), self.partitionNumber)
		self.talosAdminMock.get_describe_info = Mock(side_effect=[getDescribeInfoResponse,
																  getDescribeInfoResponse2])

		self.talosProducer = TalosProducer(producerConfig=self.talosProducerConfig,
										   topicName=self.topicName,
										   topicTalosResourceName=TopicTalosResourceName(topicTalosResourceName=self.talosResourceName),
										   talosAdmin=self.talosAdminMock,
										   talosClientFactory=self.talosClientFactoryMock,
										   topicAbnormalCallback=SimpleAbnormalCallback(),
										   userMessageCallback=TestCallback())

		# wait check partition interval
		time.sleep(self.checkPartitionInterval * 2)
		# check the partition number and outgoingMessageMap changing by log info


if __name__ == '__main__':
	unittest.main()
