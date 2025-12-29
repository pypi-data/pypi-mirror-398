#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.consumer.MessageReader import MessageReader
from talos.thrift.consumer.ttypes import QueryOffsetRequest
from talos.thrift.consumer.ttypes import CheckPoint
from talos.thrift.consumer.ttypes import UpdateOffsetRequest
from talos.thrift.message.ttypes import GetPartitionOffsetRequest
from talos.consumer.MessageCheckpointer import MessageCheckpointer
from talos.utils import Utils
from talos.thrift.common.ttypes import GalaxyTalosException
import traceback
import logging
import time


class TalosMessageReader(MessageReader, MessageCheckpointer):
    logger = logging.getLogger("TalosMessageReader")

    def __init__(self, consumerConfig=None):
        MessageReader.__init__(self, consumerConfig)

    def init_start_offset(self):
        # get last commit offset or init by outer checkPoint
        readingStartOffset = int
        # when consumer  starting up, checking:
        # 1) whether not exist last commit offset, which means 'readingStartOffset==-1'
        # 2) whether reset offset
        # 3) note that: the priority of 'reset-config' is larger than 'outer-checkPoint'

        # there are following situations
        # 1) reset Offset When Start
        #    1) -1 ———— > set startOffset to - 1 and reading from start
        #    2) -2 ———— > set startOffset to endOffset and reading from end
        # 2) not reset Offset When Start
        #    1) outerCheckPoint is set ———— > reading from outerCheckPoint
        #    2) check point is not exist ———— > same with "1) reset Offset When Start"
        #    3) check point is exist ———— > reading from check point

        if self.consumerConfig.is_reset_offset_when_start():
            readingStartOffset = self.reset_read_start_offset(
                self.consumerConfig.get_reset_offset_value_when_start())
        elif self.outerCheckPoint and self.outerCheckPoint >= 0:
            readingStartOffset = self.outerCheckPoint
            # burn after reading the first time
            self.outerCheckPoint = None
        else:
            queryStartOffset = self.query_start_offset()
            if queryStartOffset == -1:
                readingStartOffset = self.reset_read_start_offset(
                    self.consumerConfig.get_reset_offset_value_when_start())
            else:
                readingStartOffset = queryStartOffset

        self.startOffset.get_and_set(readingStartOffset)
        # guarantee lastCommitOffset and finishedOffset correct
        if self.startOffset.value > 0:
            self.lastCommitOffset = self.finishedOffset = self.startOffset.value - 1
        self.logger.info("Init startOffset: " + str(self.startOffset)
                         + " lastCommitOffset: " + str(self.lastCommitOffset)
                         + " for partition: " + self.topicAndPartition.topicName
                         + str(self.topicAndPartition.partitionId))
        self.messageProcessor.init(self.topicAndPartition, self.startOffset.value)

    def reset_read_start_offset(self, resetOffsetValueWhenStart=None):
        # if resetOffsetValueWhenStart is -1 , just set startOffset to -1 and would read from the start
        # if resetOffsetValueWhenStart is -2 , we should get the endOffset from the server for reading from the end
        if resetOffsetValueWhenStart == -1:
            return -1

        request = GetPartitionOffsetRequest(self.topicAndPartition)
        response = self.messageClient.get_partition_offset(request)
        return response.endOffset + 1

    def commit_check_point(self):
        self.inner_checkpoint()
        self.messageProcessor.shutdown(self)

    def fetch_data(self):
        # control fetch qps
        currentTime = Utils.current_time_mills()
        # sleep time unit is seconds
        if currentTime - self.lastFetchTime < self.fetchInterval:
            time.sleep((self.lastFetchTime + self.fetchInterval - currentTime) / 1000)

        # fetch data and process them
        try:
            if self.logger.isEnabledFor:
                self.logger.debug("Reading message from offset: " + str(self.startOffset.value) +
                                  " of partition: " + str(self.topicAndPartition.partitionId))
            startFetchTime = Utils.current_time_mills()
            messageList = self.simpleConsumer.fetch_message(startOffset=self.startOffset.value,
                                                            maxFetchedNumber=self.consumerConfig.get_max_fetch_msg_num())
            self.lastFetchTime = Utils.current_time_mills()
            self.consumerMetrics.mark_fetch_duration(self.lastFetchTime - startFetchTime)

            # return when no message got
            if not messageList or len(messageList) == 0:
                self.check_and_commit(False)
                return

            #
            # Note: We guarantee the committed offset must be the messages that
            # have been processed by user 's MessageProcessor;
            self.finishedOffset = messageList[len(messageList) - 1].messageOffset
            startProcessTime = Utils.current_time_mills()
            self.messageProcessor.process(messageList, self)
            self.consumerMetrics.mark_process_duration(Utils.current_time_mills() - startProcessTime)
            self.startOffset.get_and_set(self.finishedOffset + 1)
            self.check_and_commit(True)
        except Exception as e:
            self.consumerMetrics.mark_fetch_or_process_failed_times()
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.error("Error when getting messages from topic: "
                              + self.topicAndPartition.topicTalosResourceName.topicTalosResourceName
                              + " partition: " + str(self.topicAndPartition.partitionId)
                              + str(traceback.format_exc()))
            self.process_fetch_exception(e)
            self.lastFetchTime = Utils.current_time_mills()

    def query_start_offset(self):
        queryOffsetRequest = QueryOffsetRequest(self.consumerGroup, self.topicAndPartition)
        queryOffsetResponse = self.queryOffsetClient.query_offset(queryOffsetRequest)

        committedOffset = queryOffsetResponse.msgOffset
        # 'committedOffset == -1' means not exist last committed offset
        # startOffset = committedOffset + 1
        if committedOffset == -1:
            return -1
        else:
            return committedOffset + 1

    def inner_checkpoint(self):
        if self.consumerConfig.is_checkpoint_auto_commit():
            self.commit_offset(self.finishedOffset)

    def checkpoint(self, messageOffset=None):
        if not messageOffset:
            messageOffset = self.finishedOffset

        self.logger.info("start checkpoint: " + str(messageOffset))
        if self.consumerConfig.is_checkpoint_auto_commit():
            self.logger.info("You can not checkpoint through MessageCheckpointer when you set " +
                             "\"galaxy.talos.consumer.checkpoint.auto.commit\" as \"true\"")
            return False

        if messageOffset <= self.lastCommitOffset or messageOffset > self.finishedOffset:
            self.logger.info("checkpoint messageOffset: " + str(messageOffset)
                             + " in wrong " + "range, lastCheckpoint messageOffset: "
                             + str(self.lastCommitOffset) + ", last " +
                             "deliver messageOffset: " + str(self.finishedOffset))
            return False

        try:
            self.commit_offset(messageOffset)
            return True
        except Exception as e:
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.error("Error when getting messages from topic: " +
                              self.topicAndPartition.topicTalosResourceName.topicTalosResourceName()
                              + " partition: " + str(self.topicAndPartition.partitionId)
                              + str(traceback.format_exc()))
            return False

    def commit_offset(self, messageOffset=None):
        checkPoint = CheckPoint(consumerGroup=self.consumerGroup,
                                topicAndPartition=self.topicAndPartition,
                                msgOffset=messageOffset,
                                workerId=self.workerId)
        # check whether to check last commit offset, firstCommit do not check
        if (not self.lastCommitOffset == -1) and self.consumerConfig.is_check_last_commit_offset():
            checkPoint.lastCommitOffset = self.lastCommitOffset

        updateOffsetRequest = UpdateOffsetRequest(checkPoint)
        updateOffsetResponse = self.consumerClient.update_offset(updateOffsetRequest)
        # update startOffset as next message
        if updateOffsetResponse.success:
            self.lastCommitOffset = messageOffset
            self.lastCommitTime = Utils.current_time_mills()
            self.logger.info("Worker: " + self.workerId + " commit offset: " +
                             str(messageOffset) + " for partition: " +
                             str(self.topicAndPartition.partitionId))
        else:
            self.logger.warning("Worker: " + self.workerId + " commit offset: " +
                                str(messageOffset) + " for partition: " +
                                str(self.topicAndPartition.partitionId) + " failed")

    def check_and_commit(self, isContinuous=None):
        if self.should_commit(isContinuous):
            try:
                self.inner_checkpoint()
            except Exception as e:
                if isinstance(e, GalaxyTalosException):
                    self.logger.error(e.errMsg)
                # when commitOffset failed, we just do nothing;
                self.logger.error("commit offset error, we skip to it"
                                  + str(traceback.format_exc()))

    def check_point(self):
        return self.check_point_with_offset(self.finishedOffset)

    def check_point_with_offset(self, commitOffset=None):
        self.logger.info("start checkpoint: " + str(commitOffset))
        if self.consumerConfig.is_checkpoint_auto_commit():
            self.logger.info("You can not checkpoint through MessageCheckpointer when you set " +
                             "\"galaxy.talos.consumer.checkpoint.auto.commit\" as \"true\"")
            return False

        if commitOffset <= self.lastCommitOffset or commitOffset > self.finishedOffset:
            self.logger.info("checkpoint messageOffset: " + str(commitOffset) + " in wrong " +
                             "range, lastCheckpoint messageOffset: " + str(self.lastCommitOffset)
                             + ", last deliver messageOffset: " + str(self.finishedOffset))
            return False

        try:
            self.commit_offset(commitOffset)
            return True
        except Exception as e:
            if isinstance(e, GalaxyTalosException):
                self.logger.error(e.errMsg)
            self.logger.error("Error when getting messages from topic: " +
                              self.topicAndPartition.topicTalosResourceName.topicTalosResourceName
                              + " partition: " + str(self.topicAndPartition.partitionId)
                              + str(traceback.format_exc()))
            return False

