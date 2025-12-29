#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.client.TalosClientConfig import TalosClientConfig
from talos.thrift.auth.ttypes import Credential
from talos.thrift.auth.ttypes import UserType
from talos.admin.TalosAdmin import TalosAdmin
from talos.client.TalosClientFactory import TalosClientFactory
from talos.thrift.topic.ttypes import GetTopicAttributeRequest
from talos.thrift.topic.ttypes import GetDescribeInfoRequest
from talos.thrift.topic.ttypes import CreateTopicRequest
from talos.thrift.topic.ttypes import DeleteTopicRequest
from talos.thrift.topic.ttypes import TopicAttribute
import logging


class TalosAdminDemo:
    logger = logging.getLogger("TalosAdminDemo")
    accessKey = "$yourAccessKey"
    accessSecret = "$yourSecretKey"
    topicName = "$yourTopicName"

    pro = dict()
    pro["galaxy.talos.service.endpoint"] = "$yourEndpoint"
    orgId = "$yourOrgId"
    cloudTopicName = orgId + "/" + topicName

    clientConfig = TalosClientConfig
    credential = Credential

    talosAdmin = TalosAdmin

    def __init__(self):
        self.clientConfig = TalosClientConfig(self.pro)
        # credential
        self.credential = Credential(UserType.DEV_XIAOMI,
                                     self.accessKey,
                                     self.accessSecret)
        # init admin
        talosClientFactory = TalosClientFactory(clientConfig=self.clientConfig,
                                                credential=self.credential)
        self.talosAdmin = TalosAdmin(talosClientFactory)

    def describe_topic(self):
        request = GetDescribeInfoRequest(self.topicName)
        response = self.talosAdmin.get_describe_info(request)
        print("topic: " + self.topicName + " resourceName is: "
              + response.topicTalosResourceName.topicTalosResourceName)
        print("topic: " + self.topicName + " partitionNumber is: "
              + str(response.partitionNumber))

    def get_topic_attribute(self):
        request = GetTopicAttributeRequest(self.topicName)
        response = self.talosAdmin.get_topic_attribute(request)
        print("topic: " + self.topicName + " resourceName is: "
              + response.topicTalosResourceName.topicTalosResourceName)
        print("topic: " + self.topicName + " partitionNumber is: "
              + str(response.topicAttribute.partitionNumber))

    def create_topic(self):
        topicAttribute = TopicAttribute(partitionNumber=2,
                                        messageRetentionSecs=7200)
        request = CreateTopicRequest(topicName=self.cloudTopicName,
                                     topicAttribute=topicAttribute)
        self.talosAdmin.create_topic(request)
        print("success create topic: " + self.topicName)

    def list_topic(self):
        response = self.talosAdmin.list_topics()
        for topicInfo in response:
            print("topicName is: " + topicInfo.topicName)

    def delete_topic(self):
        request = GetDescribeInfoRequest(self.topicName)
        response = self.talosAdmin.get_describe_info(request)
        resourceName = response.topicTalosResourceName
        deleteRequest = DeleteTopicRequest(topicTalosResourceName=resourceName)
        self.talosAdmin.delete_topic(deleteRequest)
        print("success delete topic: " + self.topicName)


talosAdminDemo = TalosAdminDemo()
# talosAdminDemo.delete_topic()
talosAdminDemo.create_topic()
# talosAdminDemo.describe_topic()
# talosAdminDemo.list_topic()
