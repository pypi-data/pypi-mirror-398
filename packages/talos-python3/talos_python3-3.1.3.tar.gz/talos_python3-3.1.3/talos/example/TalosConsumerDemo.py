#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.client.TalosClientConfig import TalosClientConfig
from talos.thrift.auth.ttypes import Credential
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.consumer.TalosConsumer import TalosConsumer
from talos.consumer.MessageProcessor import MessageProcessor
from talos.consumer.MessageProcessorFactory import MessageProcessorFactory
from talos.thrift.auth.ttypes import UserType
from atomic import AtomicLong
import logging
import traceback


logger = logging.getLogger("TalosConsumerDemo")
successGetNumber = AtomicLong(0)


# callback for consumer to process messages, that is, consuming logic
class MyMessageProcessor(MessageProcessor):
    topicAndPartition = TopicAndPartition
    messageOffset = int

    def init(self, topicAndPartition=None, messageOffset=None):
        self.topicAndPartition = topicAndPartition
        self.messageOffset = messageOffset

    def process(self, messages=None, messageCheckPointer=None):
        try:
            # add your process logic for 'messages
            for messageAndOffset in messages:
                logger.info("Message content: " + messageAndOffset.message.message.decode("utf-8"))
                print("Message content: " + messageAndOffset.message.message.decode("utf-8"))
            successGetNumber.get_and_set(successGetNumber.value + len(messages))
            count = successGetNumber.value
            logger.info("Consuming total data so far: " + str(count))
            print("Consuming total data so far: " + str(count))

            # if user has set 'galaxy.talos.consumer.checkpoint.auto.commit' to false,
            # then you can call the 'checkpoint' to commit the list of messages.
            # messageCheckPointer.check_point()

        except Exception as e:
            logger.error("process error, " + str(traceback.format_exc()))

    def shutdown(self, messageCheckpointer=None):
        pass


# using for thread-safe when processing different partition data
class MyMessageProcessorFactory(MessageProcessorFactory):

    def create_processor(self):
        return MyMessageProcessor()


class TalosConsumerDemo():
    accessKey = "$yourAccessKey"
    accessSecret = "$yourSecretKey"
    topicName = "$yourTopicName"
    consumerGroup = "$yourConsumerGroupName"
    clientPrefix = "$department-prefix"

    pro = dict()
    pro["galaxy.talos.service.endpoint"] = "$yourEndpoint"
    consumerConfig = TalosClientConfig
    credential = Credential

    talosConsumer = TalosConsumer

    def __init__(self):
        self.consumerConfig = TalosClientConfig(self.pro)
        # credential
        self.credential = Credential(UserType.DEV_XIAOMI,
                                     self.accessKey,
                                     self.accessSecret)

    def start(self):
        self.talosConsumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                           consumerConfig=self.consumerConfig,
                                           credential=self.credential,
                                           topicName=self.topicName,
                                           messageProcessorFactory=
                                           MyMessageProcessorFactory(),
                                           clientPrefix=self.clientPrefix)


consumerDemo = TalosConsumerDemo()
consumerDemo.start()

