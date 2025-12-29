#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.thrift.auth.ttypes import Credential
from talos.thrift.auth.ttypes import UserType
from talos.thrift.message.ttypes import Message
from talos.client.TalosClientConfig import TalosClientConfig
from talos.producer.SimpleProducer import SimpleProducer
from atomic import AtomicLong
import time
import logging
import traceback


class SimpleProducerDemo:
    logger = logging.getLogger("SimpleProducerDemo")
    accessKey = "$yourAccessKey"
    accessSecret = "$yourSecretKey"
    topicName = "$yourTopicName"
    partitionId = 0

    pro = dict()
    pro["galaxy.talos.service.endpoint"] = "$yourEndpoint"
    clientConfig = TalosClientConfig
    credential = Credential
    successPutNumber = AtomicLong(0)

    simpleProducer = SimpleProducer

    def __init__(self):
        self.clientConfig = TalosClientConfig(self.pro)
        # credential
        self.credential = Credential(UserType.DEV_XIAOMI, self.accessKey, self.accessSecret)

    def start(self):
        # init producer
        self.simpleProducer = SimpleProducer(producerConfig=self.clientConfig,
                                             topicName=self.topicName,
                                             partitionId=self.partitionId,
                                             credential=self.credential)
        message = Message()
        message.message = "test message: this message is a text string."

        messageList = [message]
        # a toy demo for putting messages to Talos server continuously
        # by using a infinite loop
        while True:
            try:
                self.simpleProducer.put_message_list(messageList)
                time.sleep(2)
            except Exception as e:
                self.logger.warn("put message failed, try again", traceback.print_exc())
                raise e
            successNum = self.successPutNumber.value
            self.successPutNumber.get_and_set(successNum + 1)
            self.logger.info("success put message count: " +
                             str(self.successPutNumber.value))
            print("success put message count: " + str(self.successPutNumber.value))


simpleProducerDemo = SimpleProducerDemo()
# add message list to producer continuously
simpleProducerDemo.start()
