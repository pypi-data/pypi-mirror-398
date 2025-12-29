#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.thrift.message.ttypes import Message
from talos.utils import Utils


class UserMessage:
    message = Message
    timestamp = int
    messageSize = int

    def __init__(self, message=None):
        self.message = message
        self.timestamp = Utils.current_time_mills()
        self.messageSize = len(message.message)
        if message.sequenceNumber:
            self.messageSize += len(message.sequenceNumber)

    def get_message(self):
        return self.message

    def get_timestamp(self):
        return self.timestamp

    def get_message_size(self):
        return self.messageSize
