#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.thrift.topic.ttypes import GetDescribeInfoRequest
from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.admin.TalosAdmin import TalosAdmin
from talos.client.TalosClientConfig import TalosClientConfig
from talos.client.TalosClientFactory import TalosClientFactory
from talos.utils import Utils
from talos.utils.Utils import ReadWriteLock
from talos.utils.FalconWriter import FalconWriter
from talos.consumer.MessageProcessorFactory import MessageProcessorFactory
from talos.consumer.MessageReaderFactory import MessageReaderFactory
from talos.thrift.consumer.ttypes import ConsumeUnit
from talos.thrift.consumer.ttypes import QueryWorkerRequest
from talos.thrift.consumer.ttypes import RenewResponse
from talos.thrift.consumer.ttypes import RenewRequest
from talos.thrift.consumer.ttypes import LockWorkerRequest
from talos.client.TalosErrors import InvalidArgumentError
from talos.client.ScheduleInfoCache import ScheduleInfoCache
from talos.consumer.PartitionFetcher import PartitionFetcher
from talos.thrift.common.ttypes import GalaxyTalosException
from threading import Timer
import logging
import random
import copy
import threading
import traceback


logger = logging.getLogger("TalosConsumer")


class WorkerPair(object):
    workerId = str
    hasPartitionNum = int

    def __init__(self, workerId=None, hasPartitionNum=None):
        self.workerId = workerId
        self.hasPartitionNum = hasPartitionNum

    def __lt__(self, other):
        return self.hasPartitionNum > other.hasPartitionNum

    def to_string(self):
        return "{'" + self.workerId + '\'' + ", " + str(self.hasPartitionNum) + '}'


class TalosConsumer(object):
    workerId = str
    random = random
    consumerGroup = str
    messageProcessorFactory = MessageProcessorFactory
    messageReaderFactory = MessageReaderFactory
    partitionFetcherMap = dict
    talosConsumerConfig = TalosClientConfig
    talosClientFactory = TalosClientFactory
    talosAdmin = TalosAdmin
    readWriteLock = ReadWriteLock()
    isActive = bool
    reBalanceExecutor = threading.Thread

    # 3 single scheduledExecutor respectively used for
    # a) checking partition number periodically
    # b) checking alive worker info periodically
    # c) renew worker heartbeat and serving partition locks periodically
    partitionScheduledExecutor = Timer
    workerScheduleExecutor = Timer
    renewScheduleExecutor = Timer

    # init by getting from rpc call as follows
    topicName = str
    partitionNumber = int
    topicTalosResourceName = TopicTalosResourceName
    workerInfoMap = dict
    partitionCheckPoint = dict

    falconWriter = FalconWriter
    consumerMonitorThread = Timer

    def __init__(self, consumerGroup=None, consumerConfig=None,
                 credential=None, topicName=None, messageProcessorFactory=None,
                 clientPrefix=None, talosResourceName=None, workerId=None,
                 consumerClient=None, talosAdmin=None, fetcherMap=None,
                 partitionCheckPoint=None):
        if workerId:
            self.workerId = workerId
        else:
            self.workerId = Utils.generate_client_id(consumerConfig.get_client_ip(), clientPrefix)
        self.consumerGroup = consumerGroup
        self.talosConsumerConfig = consumerConfig
        self.topicName = topicName
        self.messageProcessorFactory = messageProcessorFactory
        self.messageReaderFactory = MessageReaderFactory()
        self.talosClientFactory = TalosClientFactory(consumerConfig, credential)
        if talosAdmin:
            self.talosAdmin = talosAdmin
        else:
            self.talosAdmin = TalosAdmin(self.talosClientFactory)
        if consumerClient:
            self.consumerClient = consumerClient
        else:
            self.consumerClient = self.talosClientFactory.new_consumer_client()
            self.lockClient = self.talosClientFactory.new_consumer_client()
            self.renewClient = self.talosClientFactory.new_consumer_client()
            self.queryClient = self.talosClientFactory.new_consumer_client()
        if talosResourceName:
            self.topicTalosResourceName = talosResourceName
        else:
            self.topicTalosResourceName = self.talosAdmin.get_describe_info(
                GetDescribeInfoRequest(self.topicName))
        if fetcherMap:
            self.partitionFetcherMap = fetcherMap
        else:
            self.partitionFetcherMap = dict()
        if partitionCheckPoint:
            self.partitionCheckPoint = partitionCheckPoint
        else:
            self.partitionCheckPoint = dict()
        # get scheduleInfo
        self.scheduleInfoCache = ScheduleInfoCache().get_schedule_info_cache(
            topicTalosResourceName=self.topicTalosResourceName.topicTalosResourceName,
            talosClientConfig=consumerConfig, messageClient=self.talosClientFactory.new_message_client(),
            talosClientFactory=self.talosClientFactory)
        self.falconWriter = FalconWriter(falconUrl=consumerConfig.get_falcon_url())
        self.isActive = True

        logger.info("The worker: " + self.workerId + " is initializing...")
        # check and get topic info such as partitionNumber
        self.check_and_get_topic_info(self.topicTalosResourceName)
        # register self workerId
        self.register_self()
        # get worker info
        self.get_worker_info()
        # do balance and init simple consumer
        self.make_balance()
        # start CheckPartitionTask/CheckWorkerInfoTask/RenewTask
        self.init_check_partition_task()
        self.init_check_worker_info_task()
        self.init_renew_task()
        self.init_consumer_monitor_task()

    #
    # Check Partition Task
    # if partition number change, invoke ReBalanceTask
    #
    def check_partition_task(self):
        try:
            request = GetDescribeInfoRequest(self.topicName)
            response = self.talosAdmin.get_describe_info(request)
        except Exception as throwable:
            logger.error("Exception in CheckPartitionTask: " + str(traceback.format_exc()))
            # if throwable instance of HBaseOperationFailed, just return
            # if throwable instance of TopicNotExist, cancel all reading task
            if Utils.is_topic_not_exist(throwable):
                self.cancel_all_consuming_task()
            self.partitionScheduledExecutor = Timer(interval=self.talosConsumerConfig
                                                    .get_check_partition_interval(),
                                                    function=self.check_partition_task)
            self.partitionScheduledExecutor.setName(
                "checkPartitionTask-" + self.topicName)
            self.partitionScheduledExecutor.start()
            return

        if not self.topicTalosResourceName == response.topicTalosResourceName:
            errMsg = "The topic: " + self.topicTalosResourceName.topicTalosResourceName \
                     + " not exist. It might have been deleted. " + \
                     "The getMessage threads will be cancel."
            logger.error(errMsg)
            self.cancel_all_consuming_task()
            self.partitionScheduledExecutor = Timer(interval=self.talosConsumerConfig
                                                    .get_check_partition_interval(),
                                                    function=self.check_partition_task)
            self.partitionScheduledExecutor.setName(
                "checkPartitionTask-" + self.topicName)
            self.partitionScheduledExecutor.start()
            return

        topicPartitionNum = response.partitionNumber
        if self.partitionNumber < topicPartitionNum:
            logger.info("partitionNumber changed from " + str(self.partitionNumber) + " to " +
                        str(topicPartitionNum) + ", execute a re-balance task.")
            # update partition number and call the re - balance
            self.set_partition_number(topicPartitionNum)
            # call the re - balance task
            self.reBalanceExecutor = threading.Thread(target=self.re_balance_task)
            self.reBalanceExecutor.setName("talos-consumer-reBalanceTask-" + self.topicName)
            self.reBalanceExecutor.start()

        self.partitionScheduledExecutor = Timer(interval=self.talosConsumerConfig
                                                .get_check_partition_interval(),
                                                function=self.check_partition_task)
        self.partitionScheduledExecutor.setName("talos-consumer-checkPartitionTask-"
                                                + self.topicName)
        self.partitionScheduledExecutor.start()

    #
    # Check Worker Info Task
    #
    # check alive worker number and get the worker serving map
    # 1) get the latest worker info and synchronized update the local workInfoMap
    # 2) invoke the ReBalanceTask every time
    #
    # Note:
    # a) current alive workers refer to scan 'consumerGroup+Topic+Worker'
    # b) all serving partitions got by the a)'s alive workers
    #
    # G+T+W    G+T+P
    # yes       no  -- normal, exist idle workers
    # no        yes -- abnormal, but ttl will fix it
    #
    def check_worker_info_task(self):
        try:
            self.get_worker_info()
        except Exception as throwble:
            logger.error("Get worker info error: " + str(traceback.format_exc()))
        # invoke the re-balance task every time
        self.reBalanceExecutor = threading.Thread(target=self.re_balance_task)
        self.reBalanceExecutor.setName("reBalanceTask-" + self.topicName)
        self.reBalanceExecutor.start()

        self.workerScheduleExecutor = Timer(interval=self.talosConsumerConfig
                                            .get_check_worker_info_interval(),
                                            function=self.check_worker_info_task)
        self.workerScheduleExecutor.setName("talos-consumer-checkWorkerInfoTask-"
                                            + self.topicName)
        self.workerScheduleExecutor.start()

    #
    # Re - Balance Task
    #
    # This task just re - calculate the 'has' / 'max' / 'min' and try to steal / release
    # 'CheckPartitionTask' takes charge of updating partitionNumber
    # 'CheckWorkerInfoTask' takes charge of updating workerInfoMap
    #
    def re_balance_task(self):
        try:
            self.make_balance()
        except Exception as e:
            logger.error("Exception in make_balance " + str(traceback.format_exc()))

    #
    # ReNew Task(contains two sections per renew)
    #
    # Note: we make renew process outside rather than inner PartitionFetcher class
    # because:
    # 1) make the partitionFetcher heartbeat and worker heartbeat together
    # 2) renew all the serving partitions lock within one rpc process,
    # which prevent massive rpc request to server
    #
    # when get what to renew, we take 'partitionFetcherMap' as guideline
    #
    def renew_task(self):
        toRenewPartitionList = self.get_renew_partition_list()
        consumeUnit = ConsumeUnit(self.consumerGroup, self.topicTalosResourceName,
                                  toRenewPartitionList, self.workerId)
        renewRequest = RenewRequest(consumeUnit)
        renewResponse = RenewResponse

        # plus 1 to include the first renew operation
        maxRetry = self.talosConsumerConfig.get_renew_max_retry() + 1
        while maxRetry > 0:
            try:
                renewResponse = self.renewClient.renew(renewRequest)
            except Exception as e:
                if isinstance(e, GalaxyTalosException):
                    logger.error(e.errMsg)
                logger.error("Worker: " + self.workerId + " renew error: "
                             + str(traceback.format_exc()))
                continue
            maxRetry -= 1

            # 1) make heartbeat success and renew partitions success
            if renewResponse.heartbeatSuccess and len(renewResponse.failedPartitionList) == 0:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("The worker: " + self.workerId +
                                 " success heartbeat and renew partitions: " + str(toRenewPartitionList))
                break

        # 2) make heart beat failed, cancel all partitions
        # no need to renew anything, so block the renew thread and cancel all task
        if renewResponse and not renewResponse.heartbeatSuccess:
            logger.error("The worker: " + self.workerId + " failed to make heartbeat, cancel all consumer task")
            self.cancel_all_consuming_task()

        # 3) make heartbeat success but renew some partitions failed
        # stop read, commit offset, unlock for renew failed partitions
        # the release process is graceful, so may be a long time,
        # do not block the renew thread and switch thread to re-balance thread
        if renewResponse and len(renewResponse.failedPartitionList) > 0:
            failedRenewList = renewResponse.failedPartitionList
            logger.error("The worker: " + self.workerId + " failed to renew partitions: "
                         + str(failedRenewList))
            self.release_partition_lock(failedRenewList)

        self.renewScheduleExecutor = Timer(interval=self.talosConsumerConfig
                                           .get_renew_check_interval(),
                                           function=self.renew_task)
        self.renewScheduleExecutor.setName("talos-consumer-renewTask-" + self.topicName)
        self.renewScheduleExecutor.start()

    def consumer_monitor_task(self):
        try:
            self.push_metric_data()
        except Exception as throwable:
            logger.error("push metric data to falcon failed." + str(traceback.format_exc()))

        self.consumerMonitorThread = Timer(interval=self.talosConsumerConfig
                                           .get_report_metric_interval_millis() / 1000,
                                           function=self.consumer_monitor_task)
        self.consumerMonitorThread.setName("talos-consumer-checkPartitionTask-"
                                           + self.topicName)
        self.consumerMonitorThread.start()

    def check_and_get_topic_info(self, topicTalosResourceName=None):
        topicName = Utils.get_topic_name_by_resource_name(
            str(topicTalosResourceName.topicTalosResourceName.topicTalosResourceName))
        response = self.talosAdmin.get_describe_info(GetDescribeInfoRequest(topicName))
        resourceName = topicTalosResourceName.topicTalosResourceName.topicTalosResourceName

        if not resourceName == response.topicTalosResourceName.topicTalosResourceName:
            logger.info("The consumer initialize failed by topic not found")
            raise InvalidArgumentError("The topic: " + resourceName +
                                       " not found")

        self.set_partition_number(response.partitionNumber)
        self.topicTalosResourceName = topicTalosResourceName.topicTalosResourceName
        logger.info("The worker: " + self.workerId + " check and get topic info done")

    def set_partition_number(self, partitionNumber=None):
        self.readWriteLock.write_acquire()
        self.partitionNumber = partitionNumber
        self.readWriteLock.write_release()

    def register_self(self):
        consumeUnit = ConsumeUnit(self.consumerGroup, self.topicTalosResourceName, [],
                                  self.workerId)
        lockWorkerRequest = LockWorkerRequest(consumeUnit)

        tryCount = self.talosConsumerConfig.get_self_register_max_retry() + 1
        while tryCount >= 0:
            try:
                lockWorkerResponse = self.lockClient.lock_worker(lockWorkerRequest)
            except Exception as e:
                if isinstance(e, GalaxyTalosException):
                    logger.error(e.errMsg)
                logger.error("The worker: " + self.workerId + "register self got error: "
                             + str(traceback.format_exc()))
                continue
            if lockWorkerResponse.registerSuccess:
                logger.info("The worker: " + self.workerId + " register self success")
                return
            logger.warn("The worker: " + self.workerId + " register self failed, make " +
                        str(tryCount) + " retry")
            tryCount -= 1

        logger.error("The worker: " + self.workerId + " register self failed")
        raise RuntimeError(self.workerId + " register self failed")

    def get_worker_info(self):
        queryWorkerRequest = QueryWorkerRequest(self.consumerGroup,
                                                self.topicTalosResourceName)
        queryWorkerResponse = self.queryClient.query_worker(queryWorkerRequest)

        # if queryWorkerInfoMap size equals 0,
        # it represents hbase failed error, do not update local map
        # because registration, the queryWorkerInfoMap size >= 1 at least
        # if queryWorkerInfoMap not contains self, it indicates renew failed,
        # do not update local map to prevent a bad re - balance
        if len(queryWorkerResponse.workerMap) == 0 or self.workerId not in \
                queryWorkerResponse.workerMap:
            return

        self.readWriteLock.write_acquire()
        self.workerInfoMap = queryWorkerResponse.workerMap
        self.readWriteLock.write_release()

    def calculate_target_list(self, copyPartitionNum=None, workerNumber=None,
                              targetList=None):
        if workerNumber == 1:
            # one worker serving all partitions
            targetList.append(copyPartitionNum)
        elif copyPartitionNum < workerNumber:
            # per worker per partition, the extra worker must be idle
            index = 0
            while index < copyPartitionNum:
                targetList.append(1)
                index += 1
        else:
            # calculate the target sequence
            sum = 0
            min = int(copyPartitionNum / workerNumber)
            remainder = int(copyPartitionNum % workerNumber)
            # add max by remainder
            index = 0
            while index < remainder:
                targetList.append(min + 1)
                sum += min + 1
                index += 1

            # add min by (workerNumber - remainder)
            index = 0
            while index < (workerNumber - remainder):
                targetList.append(min)
                sum += min
                index += 1
            try:
                assert sum == copyPartitionNum
            except AssertionError as error:
                raise error

        # sort target by descending
        targetList.sort(reverse=True)
        logger.info("worker: " + self.workerId + " calculate target partitions done: " +
                    str(targetList))

    def calculate_worker_pairs(self, copyWorkerMap=None, storedWorkerPairs=None):
        for key, value in copyWorkerMap.items():
            storedWorkerPairs.append(WorkerPair(key, len(value)))
        storedWorkerPairs.sort()
        logger.info("worker: " + self.workerId + " calculate sorted worker pairs: "
                    + str(storedWorkerPairs))

    def make_balance(self):
        #
        # When start make balance, we deep copy 'partitionNumber' and 'workerInfoMap'
        # to prevent both value appear inconsistent during the process makeBalance
        #
        copyPartitionNum = self.partitionNumber
        copyWorkerInfoMap = self.deep_copy_worker_info()

        #
        # if workerInfoMap not contains workerId, there must be error in renew task.
        # the renew task will cancel the consuming task and stop to read data,
        # so just return and do not care balance.
        #
        if not (self.workerId in copyWorkerInfoMap):
            logger.error("WorkerInfoMap not contains worker: " + self.workerId +
                         ". There may be some error for renew task.")
            return

        # calculate target and sorted worker pairs
        targetList = []
        sortedWorkerPairs = []
        self.calculate_target_list(copyPartitionNum, len(copyWorkerInfoMap), targetList)
        self.calculate_worker_pairs(copyWorkerInfoMap, sortedWorkerPairs)

        # judge stealing or release
        toStealList = []
        toReleaseList = []

        i = 0
        while i < len(sortedWorkerPairs):
            if sortedWorkerPairs[i].workerId == self.workerId:
                hasList = self.get_has_list()
                has = len(hasList)

                # workerNum > partitionNum, idle workers have no match target, do nothing
                if i >= len(targetList):
                    break
                target = targetList[i]
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Worker: " + self.workerId + " has: " + str(has) +
                                 " target: " + str(target))

                # a balanced state, do nothing
                if has == target:
                    return
                elif has > target:
                    # release partitions
                    toReleaseNum = has - target
                    while toReleaseNum > 0 and len(hasList) > 0:
                        toReleaseList.append(hasList.pop(0))
                        toReleaseNum -= 1
                else:
                    # stealing partitions
                    idlePartitions = self.get_idle_partitions()
                    if len(idlePartitions) > 0:
                        toStealNum = target - has
                        while toStealNum > 0 and len(idlePartitions) > 0:
                            randomIndex = random.randint(0, len(idlePartitions) - 1)
                            toStealList.append(idlePartitions.pop(randomIndex))
                            toStealNum -= 1
            i += 1

        # steal or release partition lock or reached a balance state
        try:
            assert not (len(toStealList) > 0 and len(toReleaseList) > 0)
        except AssertionError as error:
            raise error

        if len(toStealList) > 0:
            self.steal_partition_lock(toStealList)
        elif len(toReleaseList) > 0:
            self.release_partition_lock(toReleaseList)
        else:
            # do nothing when reach balance state
            logger.info("The worker: " + self.workerId + " have reached a balance state.")

    def steal_partition_lock(self, toStealList=None):
        logger.info("Worker: " + self.workerId + " try to steal " + str(len(toStealList)) +
                    " partition: " + str(toStealList))
        # try to lock and invoke serving partition PartitionFetcher to 'LOCKED' state
        self.readWriteLock.write_acquire()
        for partitionId in toStealList:
            if partitionId not in self.partitionFetcherMap:
                # Note 'partitionCheckPoint.get(partitionId)' may be null, it's ok
                partitionFetcher = PartitionFetcher(consumerGroup=self.consumerGroup,
                                                    topicName=self.topicName,
                                                    topicTalosResourceName=self.topicTalosResourceName,
                                                    partitionId=partitionId,
                                                    talosConsumerConfig=self.talosConsumerConfig,
                                                    workerId=self.workerId,
                                                    consumerClient=self.talosClientFactory.new_consumer_client(),
                                                    messageClient=self.talosClientFactory.new_message_client(),
                                                    getPartitionOffsetClient=self.talosClientFactory.new_message_client(),
                                                    queryPartitionCleint=self.talosClientFactory.new_consumer_client(),
                                                    commitOffsetClient=self.talosClientFactory.new_consumer_client(),
                                                    messageProcessor=self.messageProcessorFactory.create_processor(),
                                                    messageReader=self.messageReaderFactory.create_message_reader(self.talosConsumerConfig),
                                                    outerCheckPoint=self.partitionCheckPoint.get(partitionId))
                self.partitionFetcherMap[partitionId] = partitionFetcher
            self.partitionFetcherMap.get(partitionId).lock()
        self.readWriteLock.write_release()

    def release_partition_lock(self, toReleaseList=None):
        logger.info("Worker: " + self.workerId + " try to release " + str(len(toReleaseList))
                    + " partition: " + str(toReleaseList))
        # stop read, commit offset, unlock the partition async
        for partitionId in toReleaseList:
            try:
                assert partitionId in self.partitionFetcherMap
            except AssertionError as error:
                logger.warning("Worker: %s try to release partition: %d failed: %s", self.workerId, partitionId, error)
                continue
            self.partitionFetcherMap.get(partitionId).unlock()
            del self.partitionFetcherMap[partitionId]

    def get_has_list(self):
        hasList = []
        self.readWriteLock.write_acquire()
        for key, value in self.partitionFetcherMap.items():
            if value.is_serving():
                hasList.append(key)
        self.readWriteLock.write_release()
        return hasList

    def get_idle_partitions(self):
        self.readWriteLock.read_acquire()
        try:
            assert self.partitionNumber > 0

            idlePartitions = []
            i = 0
            while i < self.partitionNumber:
                idlePartitions.append(i)
                i += 1
            for valueList in self.workerInfoMap.values():
                for partitionId in valueList:
                    idlePartitions.remove(partitionId)
        except AssertionError as error:
            raise error
        finally:
            self.readWriteLock.read_release()
        return idlePartitions

    def shut_down_fetcher(self):
        for i in self.partitionFetcherMap:
            self.partitionFetcherMap.get(i).shutdown()

    def deep_copy_worker_info(self):
        self.readWriteLock.read_acquire()
        copyMap = copy.deepcopy(self.workerInfoMap)
        self.readWriteLock.read_release()
        return copyMap

    def get_worker_id(self):
        return self.workerId

    def get_topic_talos_resource_name(self):
        return self.topicTalosResourceName

    def cancel_all_consuming_task(self):
        self.release_partition_lock(self.get_has_list())

    def get_renew_partition_list(self):
        toRenewList = []
        self.readWriteLock.read_acquire()
        for key, value in self.partitionFetcherMap.items():
            if value.is_holding_lock():
                toRenewList.append(key)
        self.readWriteLock.read_release()
        return toRenewList

    def init_check_partition_task(self):
        # check and update partition number every 1 minutes delay by default
        self.partitionScheduledExecutor = Timer(interval=self.talosConsumerConfig
                                                .get_check_partition_interval(),
                                                function=self.check_partition_task)
        self.partitionScheduledExecutor.setName("talos-consumer-checkPartitionTask-"
                                                + self.topicName)
        self.partitionScheduledExecutor.start()

    def init_check_worker_info_task(self):
        self.workerScheduleExecutor = Timer(interval=self.talosConsumerConfig
                                            .get_check_worker_info_interval(),
                                            function=self.check_worker_info_task)
        self.workerScheduleExecutor.setName("talos-consumer-checkWorkerInfoTask-"
                                            + self.topicName)
        self.workerScheduleExecutor.start()

    def init_renew_task(self):
        self.renewScheduleExecutor = Timer(interval=self.talosConsumerConfig
                                           .get_renew_check_interval(),
                                           function=self.renew_task)
        self.renewScheduleExecutor.setName("talos-consumer-renewTask-"
                                           + self.topicName)
        self.renewScheduleExecutor.start()

    def init_consumer_monitor_task(self):
        if self.talosConsumerConfig.is_open_client_monitor():
            self.consumerMonitorThread = Timer(interval=self.talosConsumerConfig
                                               .get_report_metric_interval_millis() / 1000,
                                               function=self.consumer_monitor_task)
            self.consumerMonitorThread.setName("talos-consumer-monitor-" + self.topicName)
            self.consumerMonitorThread.start()

    def push_metric_data(self):
        jsonArray = []
        for key, value in self.partitionFetcherMap.items():
            jsonArray += value.get_falcon_data()
        self.falconWriter.push_falcon_data(jsonArray)

    #
    # First stop CheckPartition and CheckWorkerInfo Task and then shutdown all fetcher,
    # that avoid thread exit failed caused by rebalance partition when shutDownAllFetcher
    #
    def shutdown(self):
        if not self.isActive:
            logger.info("Worker: " + str(self.workerId) + " is already shutdown, "
                        + "don't do it again.")
            return
        logger.info("Worker: " + self.workerId + " is shutting down...")
        self.partitionScheduledExecutor.cancel()
        self.workerScheduleExecutor.cancel()
        self.shut_down_fetcher()
        self.renewScheduleExecutor.cancel()
        if self.talosConsumerConfig.is_open_client_monitor():
            self.consumerMonitorThread.cancel()
        self.scheduleInfoCache.shut_down(self.topicTalosResourceName)
        self.isActive = False
        logger.info("Worker: " + self.workerId + " shutdown.")
