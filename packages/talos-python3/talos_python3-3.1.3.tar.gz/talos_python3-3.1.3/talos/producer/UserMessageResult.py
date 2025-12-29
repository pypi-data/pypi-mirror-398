#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 

class UserMessageResult:
    messageList = []
    topicName = str
    partitionId = int
    successful = bool
    cause = Exception

    def __init__(self, messageList=None, topicName=None, partitionId=None):
        self.messageList = messageList
        self.topicName = topicName
        self.partitionId = partitionId
        self.successful = False
        self.cause = None

    def get_topic_name(self):
        return self.topicName

    def get_partition_id(self):
        return self.partitionId

    def is_successful(self):
        return self.successful

    def get_message_list(self):
        return self.messageList

    def get_cause(self):
        return self.cause

    def set_successful(self, successful=None):
        self.successful = successful

    def set_cause(self, cause=None):
        self.cause = cause
