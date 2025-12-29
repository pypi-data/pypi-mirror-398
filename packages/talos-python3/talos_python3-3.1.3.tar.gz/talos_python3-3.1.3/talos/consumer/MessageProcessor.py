#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#


class MessageProcessor:
    #
    # TalosConsumer invoke init to indicate it will deliver message to the
    # MessageProcessor instance;
    # @ param topicAndPartition which topicAndPartition to consume message
    # @ param startMessageOffset the messageOffset that read from talos;
    #
    def init(self, topicAndPartition=None, startMessageOffset=None):
        pass

    #
    # User implement this method and process the messages read from Talos
    # @ param messages the messages that read from talos;
    # @ param messageCheckpointer you can use messageCheckpointer to checkpoint
    #                             the received messageOffset when you not use Talos
    #                             default checkpoint messageOffset.
    #
    def process(self, messages=None, messageCheckPointer=None):
        pass

    #
    # TalosConsumer invoke shutdown to indicate it will no longer deliver message
    # to the MessageProcess instance.
    # @ param messageCheckpointer you can use messageCheckpointer to checkpoint
    #                             the received messageOffset when you not use Talos
    #                             default checkpoint messageOffset.
    #
    def shutdown(self, messageCheckPointer=None):
        pass

