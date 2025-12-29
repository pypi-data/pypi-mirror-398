#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.utils.Utils import synchronized
from talos.utils import Utils
from talos.thrift.common.ttypes import GalaxyTalosException
import logging
import threading
import traceback


class PartitionMessageQueue:
    logging.basicConfig()
    logger = logging.getLogger("PartitionMessageQueue")
    userMessageList = []
    curMessageBytes = int
    partitionId = int
    maxBufferedTime = int
    maxPutMsgNumber = int
    maxPutMsgBytes = int

    def __init__(self, producerConfig=None, partitionId=None, producerPtr=None):
        self.userMessageList = []
        self.curMessageBytes = 0
        self.partitionId = partitionId
        self.producer = producerPtr
        self.maxBufferedTime = producerConfig.get_max_buffered_msg_time()
        self.maxPutMsgNumber = producerConfig.get_max_put_msg_number()
        self.maxPutMsgBytes = producerConfig.get_max_put_msg_bytes()
        self.globalLock = threading.Condition()
        self.synchronizedLock = threading.Lock()
        self.should_putLock = threading.Lock()
        self.get_wait_timeLock = threading.Lock()
        self.get_all_message_listLock = threading.Lock()

    def add_message(self, messageList=None):
        if self.globalLock.acquire():
            incrementBytes = 0
            for userMessage in messageList:
                self.userMessageList.insert(0, userMessage)
                incrementBytes += userMessage.get_message_size()

            self.curMessageBytes += incrementBytes
            # update total buffered count when add messageList
            self.producer.increase_buffered_count(len(messageList), incrementBytes)

            # notify partitionSender to getUserMessageList
            self.globalLock.notifyAll()
            self.globalLock.release()

    #
    # return messageList, if not shouldPut, block in this method
    #
    def get_message_list(self):
        if self.globalLock.acquire():
            while not self.should_put():
                try:
                    waitTime = self.get_wait_time()
                    self.globalLock.wait(waitTime)
                except Exception as e:
                    if isinstance(e, GalaxyTalosException):
                        self.logger.error(e.errMsg)
                    self.logger.error("getUserMessageList for partition: " +
                                      str(self.partitionId) + " is interrupt when waiting: "
                                      + traceback.format_exc())

        if self.logger.isEnabledFor(level=logging.DEBUG):
            self.logger.debug("getUserMessageList wake up for partition: "
                              + str(self.partitionId))

        returnList = []
        returnMsgBytes = 0
        returnMsgNumber = 0

        while (not len(self.userMessageList) == 0) and \
                returnMsgNumber < self.maxPutMsgNumber and \
                returnMsgBytes < self.maxPutMsgBytes:
            userMessage = self.userMessageList[len(self.userMessageList) - 1]
            del self.userMessageList[len(self.userMessageList) - 1]
            returnList.append(userMessage.get_message())
            self.curMessageBytes -= userMessage.get_message_size()
            returnMsgBytes += userMessage.get_message_size()
            returnMsgNumber += 1

        # update total buffered count when poll messageList
        self.producer.decrease_buffered_count(returnMsgNumber, returnMsgBytes)
        if self.logger.isEnabledFor(level=logging.DEBUG):
            self.logger.debug("Ready to put message batch: " + str(len(returnList)) +
                              " queue size: " + str(len(self.userMessageList))
                              + " and curBytes: " + str(self.curMessageBytes) +
                              " for partition: " + str(self.partitionId))
        self.globalLock.release()
        return returnList

    def should_put(self):
        self.should_putLock.acquire()
        try:
            # when TalosProducer is not active;
            if not self.producer.is_active():
                return True

            # when we have enough bytes data or enough number data;
            if self.curMessageBytes >= self.maxPutMsgBytes or \
                    len(self.userMessageList) >= self.maxPutMsgNumber:
                return True

            # when there have at least one message and it has exist enough long time;
            if len(self.userMessageList) > 0:
                curBufferedTime = Utils.current_time_mills() - self.userMessageList[len(self.userMessageList) - 1].get_timestamp()
                if curBufferedTime >= self.maxBufferedTime:
                    return True

            return False
        except Exception as e:
            self.logger.error("should_put func error: " + traceback.format_exc())
        finally:
            self.should_putLock.release()

    #
    # Note: wait(0) represents wait infinite until be notified
    # so we wait minimal 1 milli secs when time <= 0
    #
    def get_wait_time(self):
        self.get_wait_timeLock.acquire()
        try:
            if len(self.userMessageList) <= 0:
                return 3600
            time = (self.userMessageList[len(self.userMessageList) - 1].get_timestamp()
                    + self.maxBufferedTime - Utils.current_time_mills()) / 1000
            if time > 0:
                return time
            else:
                return 1
        except Exception as e:
            self.logger.error("get_wait_time func error: " + traceback.format_exc())
        finally:
            self.get_wait_timeLock.release()

    #
    # clean up MessageQueue, return all message list
    #
    def get_all_message_list(self):
        self.get_all_message_listLock.acquire()
        try:
            returnList = []
            returnMsgBytes = 0
            returnMsgNumber = 0

            while not len(self.userMessageList) == 0:
                userMessage = self.userMessageList[len(self.userMessageList) - 1]
                del self.userMessageList[len(self.userMessageList) - 1]
                returnList.append(userMessage.get_message())
                self.curMessageBytes -= userMessage.get_message_size()
                returnMsgBytes += userMessage.get_message_size()
                returnMsgNumber += 1

            # update total buffered count when poll messageList
            self.producer.decrease_buffered_count(returnMsgNumber, returnMsgBytes)
            return returnList
        except Exception as e:
            self.logger.error("get_all_message_list func error: " + traceback.format_exc())
        finally:
            self.get_all_message_listLock.release()

    @synchronized
    def get_cur_message_bytes(self):
        return self.curMessageBytes








