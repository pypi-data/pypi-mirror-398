#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.thrift.topic.ttypes import TopicTalosResourceName
from talos.thrift.topic.ttypes import TopicAndPartition
from talos.consumer.SimpleConsumer import SimpleConsumer
from talos.consumer.MessageReader import MessageReader
from talos.thrift.consumer.ttypes import ConsumeUnit
from talos.thrift.consumer.ttypes import UnlockPartitionRequest
from talos.thrift.consumer.ttypes import LockPartitionRequest
from talos.thrift.consumer.ttypes import LockPartitionResponse
from talos.client.TalosClientFactory import ConsumerClient
from talos.thrift.common.ttypes import GalaxyTalosException
from talos.utils import Utils
from talos.utils.Utils import synchronized
import logging
import threading
import traceback


#
# State of PartitionFetcher
#
# The state evolution as follows:
# INIT -> LOCKED;
# LOCKED -> UNLOCKING;
# LOCKED -> UNLOCKED;
# UNLOCKING -> UNLOCKED;
# UNLOCKED -> LOCKED;
#
class TASK_STATE:
    INIT = 0
    LOCKED = 1
    UNLOCKING = 2
    UNLOCKED = 3
    SHUTDOWNED = 4


def cur_state_to_string(curState=None):
    if curState == TASK_STATE.INIT:
        return "INIT"
    elif curState == TASK_STATE.LOCKED:
        return "LOCKED"
    elif curState == TASK_STATE.UNLOCKING:
        return "UNLOCKING"
    elif curState == TASK_STATE.UNLOCKED:
        return "UNLOCKED"
    elif curState == TASK_STATE.SHUTDOWNED:
        return "SHUTDOWNED"
    else:
        return "UNKNOWNSTATE"

#
# PartitionFetcher
#
# Per partition per PartitionFetcher
#
# PartitionFetcher as the message process task for one partition, which has four state:
# INIT, LOCKED, UNLOCKING, UNLOCKED
# Every PartitionFetcher has one runnable FetcherStateMachine to fetch messages continuously.
#
# when standing be LOCKED, it continuously reading messages by SimpleConsumer.fetchMessage;
# when standing be UNLOCKING, it stop to read, commit offset and release the partition lock;
# when standing be UNLOCKED, it do not serve any partition and wait to be invoking;
#
class PartitionFetcher(object):
    logging.basicConfig()
    logger = logging.getLogger("PartitionFetcher")
    consumerGroup = str
    topicTalosResourceName = TopicTalosResourceName
    partitionId = int
    workerId = str
    consumerClient = ConsumerClient
    commitOffsetClient = ConsumerClient
    curState = int
    topicAndPartition = TopicAndPartition
    topicName = str
    simpleConsumer = SimpleConsumer
    messageReader = MessageReader

    def __init__(self, consumerGroup=None, topicName=None, topicTalosResourceName=None,
                 partitionId=None, talosConsumerConfig=None, workerId=None,
                 consumerClient=None, messageClient=None, getPartitionOffsetClient=None,
                 queryPartitionCleint=None, commitOffsetClient=None, messageProcessor=None,
                 messageReader=None, simpleConsumer=None, outerCheckPoint=None):
        self.synchronizedLock = threading.Lock()
        self.update_stateLock = threading.Lock()
        self.consumerGroup = consumerGroup
        self.topicTalosResourceName = topicTalosResourceName
        self.partitionId = partitionId
        self.workerId = workerId
        self.consumerClient = consumerClient
        self.curState = TASK_STATE.INIT
        self.topicName = Utils.get_topic_name_by_resource_name(
            topicTalosResourceName.topicTalosResourceName)

        self.topicAndPartition = TopicAndPartition(topicName, topicTalosResourceName,
                                                   partitionId)
        if simpleConsumer:
            self.simpleConsumer = simpleConsumer
        else:
            self.simpleConsumer = SimpleConsumer(talosConsumerConfig,
                                                 topicAndPartition=self.topicAndPartition,
                                                 messageClient=messageClient)
        self.getPartitionOffsetClient = getPartitionOffsetClient
        self.queryPartitionClient = queryPartitionCleint
        self.commitOffsetClient = commitOffsetClient

        self.fetcherStateMachine = threading.Thread

        # set message reader
        if messageReader:
            self.messageReader = messageReader
            self.messageReader.set_worker_id(self.workerId)
            self.messageReader.set_consumer_group(self.consumerGroup)
            self.messageReader.set_topic_and_partition(self.topicAndPartition)
            self.messageReader.set_simple_consumer(self.simpleConsumer)
            self.messageReader.set_message_processor(messageProcessor)
            self.messageReader.set_message_client(self.getPartitionOffsetClient)
            self.messageReader.set_consumer_client(self.commitOffsetClient)
            self.messageReader.set_query_offset_client(self.queryPartitionClient)
            self.messageReader.set_outer_checkpoint(outerCheckPoint)
            self.messageReader.init_consumer_metrics()

        self.logger.info("The PartitionFetcher for topic: " +
                         str(topicTalosResourceName.topicTalosResourceName)
                         + " partition: " + str(partitionId) + " init.")

    def fetcher_state_machine(self):
        self.logger.info("initialize FetcherStateMachine for partition: "
                         + str(self.partitionId))

        # try to lock partition from HBase, if failed, set to UNLOCKED and return;
        try:
            if not self.steal_partition():
                self.update_state(TASK_STATE.UNLOCKED)
                return
        except Exception as e:
            self.logger.error("Exception in steal_partition: " + str(traceback.format_exc()))
            return

        # query start offset to read, if failed, clean and return;
        try:
            self.messageReader.init_start_offset()
        except Exception as e:
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.error("Worker: " + self.workerId + " query partition offset " +
                              "error: we will skip this partition" + str(traceback.format_exc()))
            self.clean()
            return

        # reading data
        self.logger.info("The workerId: " + self.workerId + " is serving partition: "
                         + str(self.partitionId) + " from offset: " +
                         str(self.messageReader.get_start_offset()))
        while self.get_cur_state() == TASK_STATE.LOCKED:
            self.messageReader.fetch_data()

        # wait task quit gracefully: stop reading, commit offset, clean and shutdown
        self.messageReader.clean_reader()
        self.clean()
        self.logger.info("The MessageProcessTask for topic: "
                         + self.topicTalosResourceName.topicTalosResourceName
                         + " partition: " + str(self.partitionId) + " is finished")

    # used to know whether is serving and reading data
    def is_serving(self):
        return self.curState == TASK_STATE.LOCKED

    # used to know whether need to renew
    def is_holding_lock(self):
        return self.curState == TASK_STATE.LOCKED or self.curState == TASK_STATE.UNLOCKING

    #
    # we want to guarantee the operation order for partitionFetcher,
    # such as process the following operation call:
    # 1) lock -> lock: the second 'lock' will be useless
    # 2) unlock -> unlock: the second 'unlock' will be useless
    # 3) lock -> unlock: every step within 'lock' can gracefully exit by unlock
    # 4) unlock -> lock: the 'lock' operation is useless before 'unlock' process done
    #
    def lock(self):
        if self.update_state(TASK_STATE.LOCKED):
            self.fetcherStateMachine = threading.Thread(target=self.fetcher_state_machine,
                                                        name=str("partitionFetcher for: "
                                                                 + self.topicName + " "
                                                                 + str(self.partitionId)))
            self.fetcherStateMachine.start()
            self.logger.info("Worker: " + self.workerId + " invoke partition: " +
                             str(self.partitionId) + " to 'LOCKED', try to serve it.")

    def unlock(self):
        if self.update_state(TASK_STATE.UNLOCKING):
            self.logger.info("Worker: " + self.workerId + " has set partition: " +
                             str(self.partitionId) +
                             " to 'UNLOCKING', it is revoking gracefully.")

    @synchronized
    def get_cur_state(self):
        return self.curState

    def update_state(self, targetState=None):
        self.update_stateLock.acquire()
        try:
            self.logger.info("PartitionFetcher for Partition: " + str(self.partitionId)
                             + " update " + "status from: " + cur_state_to_string(self.curState)
                             + " to: " + cur_state_to_string(targetState))
            if targetState == TASK_STATE.INIT:
                self.logger.error("targetState can nerver be INIT, "
                                  + "updateState error for: " + str(self.partitionId))
                return False
            elif targetState == TASK_STATE.LOCKED:
                if self.curState == TASK_STATE.INIT or self.curState == TASK_STATE.UNLOCKED:
                    self.curState = TASK_STATE.LOCKED
                    return True
                self.logger.error("targetState is LOCKED, but curState is: "
                                  + cur_state_to_string(self.curState) + " for partition: "
                                  + str(self.partitionId))
                return False
            elif targetState == TASK_STATE.UNLOCKING:
                if self.curState == TASK_STATE.LOCKED:
                    self.curState = TASK_STATE.UNLOCKING
                    return True
                self.logger.error("targetState is UNLOCKING, but curState is: "
                                  + cur_state_to_string(self.curState) + " for partition: "
                                  + str(self.partitionId))
                return False
            elif targetState == TASK_STATE.UNLOCKED:
                if self.curState == TASK_STATE.UNLOCKING or self.curState == TASK_STATE.LOCKED:
                    self.curState = TASK_STATE.UNLOCKED
                    return True
                self.logger.error("targetState is UNLOCKED, but curState is: "
                                  + cur_state_to_string(self.curState) + " for partition: "
                                  + str(self.partitionId))
                return False
            elif targetState == TASK_STATE.SHUTDOWNED:
                self.curState = TASK_STATE.SHUTDOWNED
                return False
            else:
                return False
        except Exception as e:
            self.logger.error("update_state func error: " + traceback.format_exc())
        finally:
            self.update_stateLock.release()

    #
    # conditions for releasePartition:
    # 1) LOCKED, stealPartition success but get startOffset failed
    # 2) UNLOCKING, stop to serve this partition
    #
    def release_partition(self):
        # release lock, if unlock failed, we just wait ttl work.
        toReleaseList = [self.partitionId]
        consumeUnit = ConsumeUnit(self.consumerGroup, self.topicTalosResourceName,
                                  toReleaseList, self.workerId)
        unlockRequest = UnlockPartitionRequest(consumeUnit)
        try:
            self.consumerClient.unlock_partition(unlockRequest)
        except Exception as e:
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.warn("Worker: " + self.workerId + " release partition error: "
                             + str(traceback.format_exc()))
            return
        self.logger.info("Worker: " + self.workerId + " success to release partition: "
                         + str(self.partitionId))

    def steal_partition(self):
        state = self.get_cur_state()
        if not state == TASK_STATE.LOCKED:
            self.logger.error("Worker: " + self.workerId + " try to stealPartitionLock: "
                              + str(self.partitionId) + " but got state: " + str(state))
            return False

        # steal lock, if lock failed, we skip it and wait next re-balance
        toStealList = [self.partitionId]
        consumeUnit = ConsumeUnit(self.consumerGroup, self.topicTalosResourceName,
                                  toStealList, self.workerId)
        lockRequest = LockPartitionRequest(consumeUnit)
        lockResponse = LockPartitionResponse()

        try:
            lockResponse = self.consumerClient.lock_partition(lockRequest)
        except Exception as e:
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.error("Worker: " + self.workerId + " steal partition id : "
                              + str(self.partitionId) + " error! " + str(traceback.format_exc()))
            return False

        # get the successfully locked partition
        successPartitionList = lockResponse.successPartitions
        if len(successPartitionList) > 0:
            try:
                assert successPartitionList[0] == self.partitionId
            except AssertionError as error:
                raise error

            self.logger.info("Worker: " + self.workerId + " success to lock partitions: "
                             + str(self.partitionId))
            return True

        self.logger.error("Worker: " + self.workerId + " failed to lock partitions: "
                          + str(self.partitionId))
        return False

    # unlock partitionLock, then revoke this task and set it to 'UNLOCKED'
    def clean(self):
        self.release_partition()
        self.update_state(TASK_STATE.UNLOCKED)

    def get_falcon_data(self):
        return self.messageReader.get_consumer_metrics().to_json_data()

    def shutdown(self):
        # set UNLOCKING to stop read and wait fetcher gracefully quit
        self.update_state(TASK_STATE.UNLOCKING)
        self.fetcherStateMachine.join()
        self.update_state(TASK_STATE.SHUTDOWNED)


