#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.serialization.MessageSerializer import MessageSerializer
from talos.client.serialization.MessageSerializerV1 import MessageSerializerV1
from talos.client.serialization.MessageSerializerV2 import MessageSerializerV2
from talos.client.serialization.MessageSerializerV3 import MessageSerializerV3
from io import BytesIO
import logging


class MessageSerialization(object):

    logger = logging.getLogger("MessageSerialization")

    def serialize_message(self, message=None, dataOutputIo=None, messageVersion=None):
        if messageVersion == 'V1':
            MessageSerializerV1().serialize(message, dataOutputIo)
        elif messageVersion == 'V2':
            MessageSerializerV2().serialize(message, dataOutputIo)
        elif messageVersion == 'V3':
            MessageSerializerV3().serialize(message, dataOutputIo)
        return

    def deserialize_message(self, dataInputIo=None):
        messageSerializer = MessageSerializer
        header = bytearray(messageSerializer.VERSION_NUMBER_LENGTH)
        try:
            if dataInputIo.readinto(header) != messageSerializer.VERSION_NUMBER_LENGTH:
                self.logger.error("read header error!")
                return
        except Exception as e:
            self.logger.error("read header error!" + e.message)
            raise
        messageVersion = MessageSerializer.decode_message_version(header=header)
        if messageVersion.get_version() == "V1":
            return MessageSerializerV1().deserialize(header, dataInputIo)
        elif messageVersion.get_version() == "V2":
            return MessageSerializerV2().deserialize(header, dataInputIo)
        elif messageVersion.get_version() == "V3":
            return MessageSerializerV3().deserialize(header, dataInputIo)

    def get_message_size(self, message=None, messageVersion=None):
        if messageVersion == 'V1':
            return MessageSerializerV1().get_message_size(message)
        elif messageVersion == 'V2':
            return MessageSerializerV2.get_message_size(message)
        elif messageVersion == 'V3':
            return MessageSerializerV3().get_message_size(message)



