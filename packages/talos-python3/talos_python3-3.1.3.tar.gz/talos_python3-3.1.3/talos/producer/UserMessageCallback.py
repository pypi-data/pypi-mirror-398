#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

import abc


class UserMessageCallback:
    #
    # Implement this method to process messages that successfully put to server
    # user can get 'messageList', 'partitionId' and 'isSuccessful' by userMessageResult
    #
    @abc.abstractmethod
    def on_success(self, userMessageResult=None):
        pass

    #
    # Implement this method to process messages failed to put to server
    # user can get 'messageList', 'partitionId' and 'cause' by userMessageResult
    #
    @abc.abstractmethod
    def on_error(self, userMessageResult=None):
        pass

