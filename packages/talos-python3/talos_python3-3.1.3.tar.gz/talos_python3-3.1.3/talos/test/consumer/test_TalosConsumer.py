#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 
import unittest

from talos.thrift.consumer.ttypes import LockWorkerResponse
from talos.thrift.consumer.ttypes import RenewResponse
from talos.thrift.consumer.ttypes import QueryWorkerResponse
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.topic.ttypes import TopicInfo
from talos.thrift.topic.ttypes import TopicAttribute
from talos.thrift.topic.ttypes import Topic
from talos.thrift.topic.ttypes import TopicState
from talos.thrift.topic.ttypes import GetDescribeInfoResponse
from talos.thrift.common.ttypes import GalaxyTalosException
from talos.thrift.common.ttypes import ErrorCode
from talos.consumer.TalosConsumer import TalosConsumer
from talos.consumer.PartitionFetcher import PartitionFetcher
from talos.client.TalosClientFactory import ConsumerClient
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from talos.admin.TalosAdmin import TalosAdmin
from talos.client.TalosErrors import InvalidArgumentError
from talos.utils import Utils
from mock import Mock
import time


class test_TalosConsumer(unittest.TestCase):
    topicName = "MyTopic"
    ownerId = "12345"
    partitionNum = 5
    partitionNum2 = 6
    resourceName = TopicTalosResourceName(topicTalosResourceName="12345#MyTopic#34595fkdiso456i390")
    resourceName2 = TopicTalosResourceName(topicTalosResourceName="12345#MyTopic#34595fkdiso456i23")
    consumerGroup = "MyConsumerGroup"
    clientIdPrefix = "TestClient1"
    clientIdPrefix2 = "TestClient2"
    clientIdPrefix3 = "TestClient3"
    workerId = Utils.generate_client_id(clientIdPrefix, "")
    workerId2 = Utils.generate_client_id(clientIdPrefix2, "")
    workerId3 = Utils.generate_client_id(clientIdPrefix3, "")

    talosResourceName = resourceName
    talosResourceName2 = resourceName2
    topicInfo = TopicInfo(topicName, talosResourceName, ownerId)
    topicInfo2 = TopicInfo(topicName, talosResourceName2, ownerId)
    topicAttribute = TopicAttribute(partitionNumber=partitionNum)
    topicAttribute2 = TopicAttribute(partitionNumber=partitionNum2)
    topic = Topic(topicInfo, topicAttribute, TopicState())
    # resourceName changed
    topic2 = Topic(topicInfo2, topicAttribute, TopicState())
    # partitionNumber changed
    topic3 = Topic(topicInfo, topicAttribute2, TopicState())

    fetcherMap = dict()
    partitionFetcher0 = Mock(PartitionFetcher)
    partitionFetcher1 = Mock(PartitionFetcher)
    partitionFetcher2 = Mock(PartitionFetcher)
    partitionFetcher3 = Mock(PartitionFetcher)
    partitionFetcher4 = Mock(PartitionFetcher)
    partitionFetcher5 = Mock(PartitionFetcher)

    talosAdminMock = Mock(TalosAdmin)
    consumerClientMock = Mock(ConsumerClient)

    def setUp(self):
        properties = dict()
        # check partition number interval 200ms
        properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_PARTITION_INTERVAL] = 0.2
        # check worker info interval 300ms
        properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_WORKER_INFO_INTERVAL] = 0.3
        # renew interval 300ms
        properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_RENEW_INTERVAL] = 0.3
        properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_RENEW_MAX_RETRY] = 0
        properties[TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_REGISTER_MAX_RETRY] = 0
        properties[TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT] = "testURI"

        # do not check parameter validity for unit test
        self.consumerConfig = TalosClientConfig(properties)

        self.fetcherMap[0] = self.partitionFetcher0
        self.fetcherMap[1] = self.partitionFetcher1
        self.fetcherMap[2] = self.partitionFetcher2
        self.fetcherMap[3] = self.partitionFetcher3
        self.fetcherMap[4] = self.partitionFetcher4
        # self.fetcherMap[5] = self.partitionFetcher5

        # construct a getDescribeInfoResponse
        getDescribeInfoResponse = GetDescribeInfoResponse(self.talosResourceName, self.partitionNum)
        self.talosAdminMock.get_describe_info = Mock(return_value=getDescribeInfoResponse)

    def tearDown(self):
        pass

    # 1) checkAndGetTopicInfoFailed
    def test_CheckAndGetTopicInfoFailed(self):
        # get describe info
        getDescribeInfoResponse = GetDescribeInfoResponse(self.talosResourceName2, self.partitionNum)
        self.talosAdminMock.get_describe_info = Mock(return_value=getDescribeInfoResponse)

        with self.assertRaises(InvalidArgumentError) as context:
            TalosConsumer(consumerGroup=self.consumerGroup, consumerConfig=self.consumerConfig,
                          talosResourceName=TopicTalosResourceName(self.talosResourceName),
                          workerId=self.workerId, consumerClient=self.consumerClientMock,
                          talosAdmin=self.talosAdminMock, fetcherMap=self.fetcherMap)

    # 2) registerSelf failed, init failed
    def test_RegisterSelfFailed(self):
        # register self
        lockWorkerResponse = LockWorkerResponse(False)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)

        with self.assertRaises(RuntimeError) as context:
            TalosConsumer(consumerGroup=self.consumerGroup, consumerConfig=self.consumerConfig,
                          talosResourceName=TopicTalosResourceName(self.talosResourceName),
                          workerId=self.workerId, consumerClient=self.consumerClientMock,
                          talosAdmin=self.talosAdminMock, fetcherMap=self.fetcherMap)

    # 3) lock -> balance
    def test_LockBalance(self):
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(True, []))
        # worker info check
        workerInfo = dict()
        partitionList = [3, 0, 2]
        workerInfo[self.workerId] = []
        workerInfo[self.workerId2] = partitionList
        workerInfo2 = dict()
        partitionList2 = [1, 4]
        workerInfo2[self.workerId] = partitionList2
        workerInfo2[self.workerId2] = partitionList
        # first not balance, then balance for serving partition number
        self.consumerClientMock.query_worker = Mock(side_effect=[QueryWorkerResponse(workerInfo),
                                                                 QueryWorkerResponse(workerInfo2)])
        # for renew/steal partition/re-balance
        self.partitionFetcher0.is_serving = Mock(side_effect=[False, False])
        self.partitionFetcher1.is_serving = Mock(side_effect=[False, True])
        self.partitionFetcher2.is_serving = Mock(side_effect=[False, False])
        self.partitionFetcher3.is_serving = Mock(side_effect=[False, False])
        self.partitionFetcher4.is_serving = Mock(side_effect=[False, True])

        self.partitionFetcher0.is_holding_lock = Mock(side_effect=[False, False])
        self.partitionFetcher1.is_holding_lock = Mock(side_effect=[False, True])
        self.partitionFetcher2.is_holding_lock = Mock(side_effect=[False, False])
        self.partitionFetcher3.is_holding_lock = Mock(side_effect=[False, False])
        self.partitionFetcher4.is_holding_lock = Mock(side_effect=[False, True])

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)
        # sleep for 2 times balance
        time.sleep(0.8)
        consumer.shutdown()

    # 4) worker online: lock -> unlock -> balance
    def test_WorkerOnlineLockUnlock(self):
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(True, []))
        # worker info check
        # first: 1 worker, 5, this worker lock 5 partitions
        workerInfo = dict()
        workerInfo[self.workerId] = []
        # second: 3 worker, 2 2 1, has sort: 5 0 0, this worker unlock 3 partition
        workerInfo2 = dict()
        workerInfo2[self.workerId] = [0, 1, 2, 3, 4]
        workerInfo2[self.workerId2] = []
        workerInfo2[self.workerId3] = []
        self.consumerClientMock.query_worker = Mock(side_effect=[QueryWorkerResponse(workerInfo),
                                                                 QueryWorkerResponse(workerInfo2)])
        # for renew/steal partition/re-balance
        # construct 3 times balance
        self.partitionFetcher0.is_serving = Mock(side_effect=[False, True, False])
        self.partitionFetcher1.is_serving = Mock(side_effect=[False, True, False])
        self.partitionFetcher2.is_serving = Mock(side_effect=[False, True, False])
        self.partitionFetcher3.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher4.is_serving = Mock(side_effect=[False, True, True])

        self.partitionFetcher0.is_holding_lock = Mock(side_effect=[False, True, False])
        self.partitionFetcher1.is_holding_lock = Mock(side_effect=[False, True, False])
        self.partitionFetcher2.is_holding_lock = Mock(side_effect=[False, True, False])
        self.partitionFetcher3.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher4.is_holding_lock = Mock(side_effect=[False, True, True])

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 3 times balance
        time.sleep(1)
        consumer.shutdown()

    # 5) worker offline: lock -> lock -> balance
    def test_WorkerOfflineLockLock(self):
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(True, []))
        # worker info check
        # first: 2 worker, [3, 2], this worker lock 2 paritions
        workerInfo = dict()
        partitionList = [4, 0, 2]
        workerInfo[self.workerId] = []
        workerInfo[self.workerId2] = partitionList
        # second: 1 worker, the other worker die, this worker lock 3 paritions
        workerInfo2 = dict()
        partitionList2 = [3, 1]
        workerInfo2[self.workerId] = partitionList2
        self.consumerClientMock.query_worker = Mock(side_effect=[QueryWorkerResponse(workerInfo),
                                                                 QueryWorkerResponse(workerInfo2)])
        # for renew / steal partition / re-balance
        # construct 2 times balance
        self.partitionFetcher1.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher3.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher0.is_serving = Mock(side_effect=[False, False, True])
        self.partitionFetcher2.is_serving = Mock(side_effect=[False, False, True])
        self.partitionFetcher4.is_serving = Mock(side_effect=[False, False, True])

        self.partitionFetcher1.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher3.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher0.is_holding_lock = Mock(side_effect=[False, False, True])
        self.partitionFetcher2.is_holding_lock = Mock(side_effect=[False, False, True])
        self.partitionFetcher4.is_holding_lock = Mock(side_effect=[False, False, True])

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 3 times balance
        time.sleep(1)
        consumer.shutdown()

    # 6) partition increase: lock -> lock -> balance
    def test_PartitionChangedLockLock(self):
        self.fetcherMap[5] = self.partitionFetcher5
        # partition check, change from 5 to 6
        getDescribeInfoResponse = GetDescribeInfoResponse(self.talosResourceName, self.partitionNum)
        getDescribeInfoResponse3 = GetDescribeInfoResponse(self.talosResourceName, self.partitionNum2)
        self.talosAdminMock.get_describe_info = Mock(side_effect=[getDescribeInfoResponse, getDescribeInfoResponse3])
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(True, []))
        # worker info check
        # first: 1 worker 5 partitions
        workerInfo = dict()
        workerInfo[self.workerId] = []
        # second: 1 worker 6 partitions
        workerInfo2 = dict()
        partitionList = [0, 1, 2, 3, 4]
        workerInfo2[self.workerId] = partitionList
        self.consumerClientMock.query_worker = Mock(side_effect=[QueryWorkerResponse(workerInfo),
                                                                 QueryWorkerResponse(workerInfo2),
                                                                 QueryWorkerResponse(workerInfo2)])
        # for renew / steal partition / re-balance
        # construct 2 times balance
        self.partitionFetcher0.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher1.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher2.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher3.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher4.is_serving = Mock(side_effect=[False, True, True])
        self.partitionFetcher5.is_serving = Mock(side_effect=[False, False, True])

        self.partitionFetcher0.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher1.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher2.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher3.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher4.is_holding_lock = Mock(side_effect=[False, True, True])
        self.partitionFetcher5.is_holding_lock = Mock(side_effect=[False, False, True])

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 3 times balance
        time.sleep(1)
        consumer.shutdown()

    # 7) renew failed: lock -> unlock -> balance
    def test_RenewFailedLockUnlock(self):
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        failedList = [0]
        self.consumerClientMock.renew = Mock(side_effect=[RenewResponse(True, []), RenewResponse(True, failedList)])
        # worker info check
        # first: 1 worker 5 partitions
        workerInfo = dict()
        partitionList = [0, 1, 2, 3, 4]
        workerInfo[self.workerId] = partitionList
        self.consumerClientMock.query_worker = Mock(return_value=QueryWorkerResponse(workerInfo))
        # for renew / steal partition / re-balance
        self.partitionFetcher0.is_serving = Mock(return_value=True)
        self.partitionFetcher1.is_serving = Mock(return_value=True)
        self.partitionFetcher2.is_serving = Mock(return_value=True)
        self.partitionFetcher3.is_serving = Mock(return_value=True)
        self.partitionFetcher4.is_serving = Mock(return_value=True)

        self.partitionFetcher0.is_holding_lock = Mock(side_effect=[True, False])
        self.partitionFetcher1.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher2.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher3.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher4.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher4.is_holding_lock = Mock(return_value=False)

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 3 times renew
        time.sleep(0.8)
        consumer.shutdown()

    # 8) renew heartbeat failed: cancel all task
    def test_RenewHeartbeatFailed(self):
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(False, []))
        # worker info check
        # first: 1 worker 5 partitions, then renew failed
        workerInfo = dict()
        workerInfo[self.workerId] = [0, 1, 2, 3, 4]
        self.consumerClientMock.query_worker = Mock(return_value=QueryWorkerResponse(workerInfo))
        # for renew / steal partition / re-balance
        self.partitionFetcher0.is_serving = Mock(return_value=True)
        self.partitionFetcher1.is_serving = Mock(return_value=True)
        self.partitionFetcher2.is_serving = Mock(return_value=True)
        self.partitionFetcher3.is_serving = Mock(return_value=True)
        self.partitionFetcher4.is_serving = Mock(return_value=True)

        self.partitionFetcher0.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher1.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher2.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher3.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher4.is_holding_lock = Mock(return_value=True)

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 3 times renew
        time.sleep(0.8)
        consumer.shutdown()

    # 9) describeTopic not exist error
    def test_DescribeTopicNotExist(self):
        getDescribeInfoResponse = GetDescribeInfoResponse(self.talosResourceName, self.partitionNum)
        self.talosAdminMock.get_describe_info = Mock(side_effect=[getDescribeInfoResponse,
                                                                  GalaxyTalosException(errorCode=ErrorCode.TOPIC_NOT_EXIST)])
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(True, []))
        workerInfo = dict()
        workerInfo[self.workerId] = []
        self.consumerClientMock.query_worker = Mock(return_value=QueryWorkerResponse(workerInfo))

        self.partitionFetcher0.is_serving = Mock(return_value=False)
        self.partitionFetcher1.is_serving = Mock(return_value=False)
        self.partitionFetcher2.is_serving = Mock(return_value=False)
        self.partitionFetcher3.is_serving = Mock(return_value=False)
        self.partitionFetcher4.is_serving = Mock(return_value=False)

        self.partitionFetcher0.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher1.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher2.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher3.is_holding_lock = Mock(return_value=True)
        self.partitionFetcher4.is_holding_lock = Mock(return_value=True)

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 1 times renew
        time.sleep(0.31)
        consumer.shutdown()

    # 10) describeTopic resourceName changed, old topic deleted
    def test_DescribeTopicResourceNameChanged(self):
        getDescribeInfoResponse = GetDescribeInfoResponse(self.talosResourceName, self.partitionNum)
        getDescribeInfoResponse2 = GetDescribeInfoResponse(self.talosResourceName2, self.partitionNum)
        self.talosAdminMock.get_describe_info = Mock(side_effect=[getDescribeInfoResponse, getDescribeInfoResponse2])
        # register self
        lockWorkerResponse = LockWorkerResponse(True)
        self.consumerClientMock.lock_worker = Mock(return_value=lockWorkerResponse)
        # renew check
        self.consumerClientMock.renew = Mock(return_value=RenewResponse(True, []))
        workerInfo = dict()
        workerInfo[self.workerId] = []
        self.consumerClientMock.query_worker = Mock(return_value=QueryWorkerResponse(workerInfo))

        self.partitionFetcher0.is_serving = Mock(return_value=False)
        self.partitionFetcher1.is_serving = Mock(return_value=False)
        self.partitionFetcher2.is_serving = Mock(return_value=False)
        self.partitionFetcher3.is_serving = Mock(return_value=False)
        self.partitionFetcher4.is_serving = Mock(return_value=False)

        consumer = TalosConsumer(consumerGroup=self.consumerGroup,
                                 consumerConfig=self.consumerConfig,
                                 talosResourceName=TopicTalosResourceName(self.talosResourceName),
                                 workerId=self.workerId,
                                 consumerClient=self.consumerClientMock,
                                 talosAdmin=self.talosAdminMock,
                                 fetcherMap=self.fetcherMap)

        # sleep for 1 times renew
        time.sleep(0.4)
        consumer.shutdown()



