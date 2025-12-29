#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#
from talos.thrift.auth.ttypes import Credential
from talos.client.TalosClientFactory import MessageClient
from talos.client.TalosClientFactory import ConsumerClient
from talos.client.TalosClientFactory import TopicClient
from talos.client.TalosClientFactory import QuotaClient
import logging


class TalosAdmin(object):
    logger = logging.getLogger("TalosAdmin")
    topicClient = TopicClient
    messageClient = MessageClient
    consumerClient = ConsumerClient
    quotaClient = QuotaClient
    credential = Credential()

    def __init__(self, talosClientFactory=None):
        self.topicClient = talosClientFactory.new_topic_client()

    # topicAttribute for partitionNumber required

    def get_describe_info(self, request=None):
        return self.topicClient.get_describe_info(request)

    def get_topic_attribute(self, request=None):
        return self.topicClient.get_topic_attribute(request)

    def create_topic(self, request=None):
        return self.topicClient.create_topic(request)

    def delete_topic(self, request=None):
        return self.topicClient.delete_topic(request)

    def change_topic_attribute(self, request=None):
        return self.topicClient.change_topic_attribute(request)

    def list_topics(self):
        return self.topicClient.list_topics()

    def list_permissions(self):
        return self.topicClient.list_permission()

    def set_permission(self, request=None):
        return self.topicClient.set_permission(request)

    def revoke_permission(self, request=None):
        return self.topicClient.revoke_permission(request)

    def get_schedule_info(self, request=None):
        return self.messageClient.get_schedule_info(request)

    def apply_quota(self, request=None):
        return self.quotaClient.apply_quota(request)

    def revoke_quota(self, request=None):
        return self.quotaClient.revoke_quota(request)

    def list_quota(self):
        return self.quotaClient.list_quota

    def get_topic_offset(self, request=None):
        return self.messageClient.get_topic_offset(request)

    def get_partition_offset(self, request=None):
        return self.messageClient.get_partition_offset(request)


