#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from talos.utils.Utils import synchronized
import threading


class BufferedMessageCount:

    def __init__(self, maxBufferedMsgNumber, maxBufferedMsgBytes):
        self._maxBufferedMsgNumber = maxBufferedMsgNumber
        self._maxBufferedMsgBytes = maxBufferedMsgBytes
        self._bufferedMsgNumber = 0
        self._bufferedMsgBytes = 0
        self.increaseLock = threading.Lock()
        self.decreaseLock = threading.Lock()
        self.synchronizedLock = threading.Lock()

    def get_buffered_msg_number(self):
        return self._bufferedMsgNumber

    def get_buffered_msg_bytes(self):
        return self._bufferedMsgBytes

    def increase(self, diffBufferedMsgNumber, diffBufferedMsgBytes):
        self.increaseLock.acquire()
        self._bufferedMsgNumber += diffBufferedMsgNumber
        self._bufferedMsgBytes += diffBufferedMsgBytes
        self.increaseLock.release()

    def decrease(self, diffBufferedMsgNumber, diffBufferedMsgBytes):
        self.decreaseLock.acquire()
        self._bufferedMsgNumber -= diffBufferedMsgNumber
        self._bufferedMsgBytes -= diffBufferedMsgBytes
        self.decreaseLock.release()

    @synchronized
    def is_empty(self):
        return self._bufferedMsgNumber == 0

    @synchronized
    def is_full(self):
        return self._bufferedMsgNumber >= self._maxBufferedMsgNumber or \
               self._bufferedMsgBytes >= self._maxBufferedMsgBytes
