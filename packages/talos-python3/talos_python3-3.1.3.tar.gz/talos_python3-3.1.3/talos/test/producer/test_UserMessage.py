import unittest

from talos.thrift.message.ttypes import Message
from talos.producer.UserMessage import UserMessage


class test_UserMessage(unittest.TestCase):
	partitionKey = "123456qwerty"
	sequenceNumber = "654321"
	data = "hello"

	def setUp(self):
		self.message = Message(message=self.data, partitionKey=self.partitionKey)
		self.userMessage = UserMessage(self.message)

	def tearDown(self):
		pass

	def test_get_message(self):
		self.assertEqual(self.message, self.userMessage.get_message())

	def test_get_timestamp(self):
		self.assertIsNotNone(self.userMessage.get_timestamp())

	def test_get_message_size(self):
		self.assertEqual(len(self.data), self.userMessage.get_message_size())

		self.message.sequenceNumber = self.sequenceNumber
		self.userMessage = UserMessage(self.message)
		self.assertEqual(len(self.data) + len(self.sequenceNumber), self.userMessage.get_message_size())


if __name__ == '__main__':
	unittest.main()
