#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.TalosClientConfig import TalosClientConfig
from talos.thrift.auth.ttypes import Credential
from talos.thrift.common.ttypes import Version
from talos.thrift.topic import TopicService
from talos.thrift.message import MessageService
from talos.thrift.consumer import ConsumerService
from talos.thrift.quota import QuotaService
from talos.client.TalosErrors import InvalidArgumentError
from talos.client.Constants import Constants
from talos.thrift.protocol.TCompactProtocol import TCompactProtocol
from talos.client.TalosHttpClient import TalosHttpClient
import threading
import logging
import platform
import http.client
import http


class ConsumerClient:
    talosHttpClient = TalosHttpClient
    consumerClientLock = threading.Lock()

    def __init__(self, talosHttpClient=None):
        self.talosHttpClient = talosHttpClient

    def renew(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=renew")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).renew(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def lock_worker(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=lockWorker")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).lockWorker(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def query_worker(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=queryWorker")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).queryWorker(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def lock_partition(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=lockPartition")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).lockPartition(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def unlock_partition(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=unlockPartition")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).unlockPartition(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def query_offset(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=queryOffset")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).queryOffset(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def update_offset(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=updateOffset")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).updateOffset(request)
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()

    def get_worker_id(self, request=None):
        self.consumerClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getWorkerId")
            iprot = TCompactProtocol(self.talosHttpClient)
            return ConsumerService.Client(iprot).getWorkerId(request).workerId
        except Exception as e:
            raise e
        finally:
            self.consumerClientLock.release()


class TopicClient:
    talosHttpClient = TalosHttpClient
    topicClientLock = threading.Lock()

    def __init__(self, talosHttpClient=None):
        self.talosHttpClient = talosHttpClient

    def create_topic(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=createTopic")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).createTopic(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def get_describe_info(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getDescribeInfo")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).getDescribeInfo(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def get_topic_attribute(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getTopicAttribute")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).getTopicAttribute(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def delete_topic(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=deleteTopic")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).deleteTopic(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def change_topic_attribute(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=changeTopicAttribute")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).changeTopicAttribute(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def list_topics(self):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=listTopics")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).listTopics().topicInfos
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def set_permission(self, request=None):
        self.topicClientLock.acquire()
        try:
            assert request.permission > 0
            self.talosHttpClient.set_query_string("type=setPermission")
            iprot = TCompactProtocol(self.talosHttpClient)
            TopicService.Client(iprot).setPermission(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def revoke_permission(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=revokePermission")
            iprot = TCompactProtocol(self.talosHttpClient)
            TopicService.Client(iprot).setPermission(request)
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()

    def list_permission(self, request=None):
        self.topicClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=listPermission")
            iprot = TCompactProtocol(self.talosHttpClient)
            return TopicService.Client(iprot).listPermission(request).permissions
        except Exception as e:
            raise e
        finally:
            self.topicClientLock.release()


class MessageClient:
    talosHttpClient = TalosHttpClient
    messageClientLock = threading.Lock()

    def __init__(self, talosHttpClient=None):
        self.talosHttpClient = talosHttpClient

    def get_message(self, request=None):
        self.messageClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getMessage")
            iprot = TCompactProtocol(self.talosHttpClient)
            return MessageService.Client(iprot).getMessage(request)
        except Exception as e:
            raise e
        finally:
            self.messageClientLock.release()

    def put_message(self, request=None):
        self.messageClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=putMessage")
            iprot = TCompactProtocol(self.talosHttpClient)
            return MessageService.Client(iprot).putMessage(request)
        except Exception as e:
            raise e
        finally:
            self.messageClientLock.release()

    def get_topic_offset(self, request=None):
        self.messageClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getTopicOffset")
            iprot = TCompactProtocol(self.talosHttpClient)
            return MessageService.Client(iprot).getTopicOffset(request).offsetInfoList
        except Exception as e:
            raise e
        finally:
            self.messageClientLock.release()

    def get_partition_offset(self, request=None):
        self.messageClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getPartitionOffset")
            iprot = TCompactProtocol(self.talosHttpClient)
            return MessageService.Client(iprot).getPartitionOffset(request).offsetInfo
        except Exception as e:
            raise e
        finally:
            self.messageClientLock.release()

    def get_schedule_info(self, request=None):
        self.messageClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=getScheduleInfo")
            iprot = TCompactProtocol(self.talosHttpClient)
            return MessageService.Client(iprot).getScheduleInfo(request).scheduleInfo
        except Exception as e:
            raise e
        finally:
            self.messageClientLock.release()


class QuotaClient:
    talosHttpClient = TalosHttpClient
    quotaClientLock = threading.Lock()

    def __init__(self, talosHttpClient=None):
        self.talosHttpClient = talosHttpClient

    def apply_quota(self, request=None):
        self.quotaClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=applyQuota")
            iprot = TCompactProtocol(self.talosHttpClient)
            QuotaService.Client(iprot).applyQuota(request)
        except Exception as e:
            raise e
        finally:
            self.quotaClientLock.release()

    def revoke_quota(self, request=None):
        self.quotaClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=revokeQuota")
            iprot = TCompactProtocol(self.talosHttpClient)
            return QuotaService.Client(iprot).revokeQuota(request)
        except Exception as e:
            raise e
        finally:
            self.quotaClientLock.release()

    def list_quota(self):
        self.quotaClientLock.acquire()
        try:
            self.talosHttpClient.set_query_string("type=listQuota")
            iprot = TCompactProtocol(self.talosHttpClient)
            return QuotaService.Client(iprot).listQuota()
        except Exception as e:
            raise e
        finally:
            self.quotaClientLock.release()


class TalosClientFactory:
    logger = logging.getLogger("TalosClientFactory")
    _USER_AGENT_HEADER = "User-Agent"
    _SID = "galaxytalos"
    _DEFAULT_CLIENT_CONN_TIMEOUT = 5000

    _version = Version
    _talosClientConfig = TalosClientConfig
    _credential = Credential
    _customHeaders = dict
    _httpClient = http.client.HTTPConnection
    _agent = str
    _clockOffset = int

    def __init__(self, clientConfig=None, credential=None):
        self._talosClientConfig = clientConfig
        self._credential = credential
        self._customHeaders = None
        self._version = Version()
        self._clockOffset = 0

    def new_topic_client(self):
        headers = dict()
        headers[self._USER_AGENT_HEADER] = self.create_user_agent_header()
        if self._customHeaders:
            for k in self._customHeaders:
                headers[k] = self._customHeaders[k]
        # setting 'supportAccountKey' to true for using Galaxy-V3 auth
        talosHttpClient = TalosHttpClient(self._talosClientConfig.get_service_endpoint()
                                          + Constants.TALOS_TOPIC_SERVICE_PATH,
                                          self._credential, self._clockOffset, True,
                                          self._talosClientConfig.get_is_open_dns_resolver())
        talosHttpClient.set_custom_headers(headers)
        talosHttpClient.set_timeout(self._talosClientConfig.get_client_conn_timeout())
        return TopicClient(talosHttpClient)

    def new_consumer_client(self):
        headers = dict()
        headers[self._USER_AGENT_HEADER] = self.create_user_agent_header()
        if self._customHeaders:
            for k in self._customHeaders:
                headers[k] = self._customHeaders[k]
        # setting 'supportAccountKey' to true for using Galaxy-V3 auth
        talosHttpClient = TalosHttpClient(self._talosClientConfig.get_service_endpoint()
                                          + Constants.TALOS_CONSUMER_SERVICE_PATH,
                                          self._credential, self._clockOffset, True,
                                          self._talosClientConfig.get_is_open_dns_resolver())
        talosHttpClient.set_custom_headers(headers)
        talosHttpClient.set_timeout(self._talosClientConfig.get_client_conn_timeout())
        return ConsumerClient(talosHttpClient)

    def set_custom_headers(self, customHeaders=None):
        self._customHeaders = customHeaders

    def new_message_client(self, endpoint=None):
        headers = dict()
        headers[self._USER_AGENT_HEADER] = self.create_user_agent_header()
        if self._customHeaders:
            for k in self._customHeaders:
                headers[k] = self._customHeaders[k]
        # setting 'supportAccountKey' to true for using Galaxy-V3 auth
        if not endpoint:
            talosHttpClient = TalosHttpClient(self._talosClientConfig.get_service_endpoint()
                                              + Constants.TALOS_MESSAGE_SERVICE_PATH,
                                              self._credential, self._clockOffset, True,
                                              self._talosClientConfig.get_is_open_dns_resolver())
        else:
            talosHttpClient = TalosHttpClient(endpoint + Constants.TALOS_MESSAGE_SERVICE_PATH,
                                              self._credential, self._clockOffset, True,
                                              self._talosClientConfig.get_is_open_dns_resolver())
        talosHttpClient.set_custom_headers(headers)
        talosHttpClient.set_timeout(self._talosClientConfig.get_client_conn_timeout())
        return MessageClient(talosHttpClient)

    def check_credential(self):
        if not self._credential:
            raise InvalidArgumentError("Credential is not set")

    def create_user_agent_header(self):
        return "Python-SDK/" + str(self._version.major) + "." + str(self._version.minor) + "." + str(self._version.revision) + " Python/" + platform.python_version()


