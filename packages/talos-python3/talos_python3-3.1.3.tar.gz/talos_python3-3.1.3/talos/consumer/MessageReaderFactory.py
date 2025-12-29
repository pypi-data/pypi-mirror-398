#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#
from talos.consumer.TalosMessageReader import TalosMessageReader


class MessageReaderFactory:
    def create_message_reader(self, talosConsumerConfig=None):
        return TalosMessageReader(talosConsumerConfig)

