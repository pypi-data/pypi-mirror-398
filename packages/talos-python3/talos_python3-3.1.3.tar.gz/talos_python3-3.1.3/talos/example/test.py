# Talos Consumer 封装类
from talos.client.TalosClientConfig import TalosClientConfig
from talos.example.TalosConsumerDemo import MyMessageProcessorFactory
from talos.thrift.auth.ttypes import Credential
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.consumer.TalosConsumer import TalosConsumer
from talos.consumer.MessageProcessor import MessageProcessor
from talos.consumer.MessageProcessorFactory import MessageProcessorFactory
from talos.thrift.auth.ttypes import UserType
from atomic import AtomicLong
import logging
import traceback

class TalosConsumerWrapper:
    accessKey = "AKM5DDIDEBDWBBD2PV"
    accessSecret = "w8nium9H1/1milUJkHAVGhpiDRchLxnd4ZAUbdE6"
    consumerGroup = "ConsumerGroup-fcj"
    clientPrefix = "ClientPrefix"
    pro = {
        "galaxy.talos.service.endpoint": "http://ap-tjv1autopilotsrv-talos.api.xiaomi.net",
        "galaxy.talos.client.falcon.monitor.switch": False
    }
    count = 1

    def __init__(self):
        self.consumerConfig = TalosClientConfig(self.pro)
        self.credential = Credential(UserType.DEV_XIAOMI, self.accessKey, self.accessSecret)
        self.talosConsumer = None

    def start(self, topic_name, partitionCheckPoint=None):
        """
        启动消费者。
        """
        # logger.info(f"start consumer: service_manager={service_manager}, factory={factory}, topic_name={topic_name}")
        self.talosConsumer = TalosConsumer(
            consumerGroup=self.consumerGroup,
            consumerConfig=self.consumerConfig,
            credential=self.credential,
            topicName=topic_name,
            messageProcessorFactory= MyMessageProcessorFactory(),
            clientPrefix=self.clientPrefix
        )
        return self.talosConsumer

consumerDemo = TalosConsumerWrapper()
consumerDemo.start("geo_result_receive_preview")