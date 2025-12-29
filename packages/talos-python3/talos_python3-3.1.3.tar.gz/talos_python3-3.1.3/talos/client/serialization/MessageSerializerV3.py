#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 
from talos.client.serialization.MessageSerializer import MessageSerializer
from talos.thrift.message.ttypes import Message
from talos.client.serialization.MessageVersion import MessageVersion
from struct import unpack, pack_into
from talos.utils.Utils import SerializeFormat
from talos.thrift.TSerialization import serialize
from talos.thrift.TSerialization import deserialize
from talos.thrift.protocol.TCompactProtocol import TCompactProtocolFactory
import logging
import traceback


class MessageSerializerV3(MessageSerializer):

    logger = logging.getLogger("MessageSerializerV3")

    __MESSAGE_HEADER_BYTES_V3 = 8
    __VERSION_NUMBER_LENGTH_V3 = 4
    __MESSAGE_DATA_LENGTH_BYTES_V3 = 4

    # TalosProducer serialize
    def serialize(self, msg=None, buf=None):
        # write version number
        self.write_message_version(MessageVersion(3), buf)

        # write message size
        messageData = serialize(msg, TCompactProtocolFactory())
        sizeBuffer = bytearray(self.__MESSAGE_DATA_LENGTH_BYTES_V3)
        pack_into(SerializeFormat.format_i32, sizeBuffer, 0, len(messageData))
        buf.write(sizeBuffer)

        # write message
        buf.write(messageData)
        return

    # TalosConsumer deserialize
    def deserialize(self, header=None, buf=None):
        msg = Message()
        # read message size
        messageSizeBuffer = bytearray(self.__MESSAGE_DATA_LENGTH_BYTES_V3)
        try:
            if buf.readinto(messageSizeBuffer) != self.__MESSAGE_DATA_LENGTH_BYTES_V3:
                self.logger.error("deserialize message size error!")
                return
        except Exception as e:
            self.logger.error("deserialize message size error!"
                              + str(traceback.format_exc()))
            raise e

        messageSize = int(unpack(SerializeFormat.format_i32, messageSizeBuffer)[0])

        # read message
        messageDataBuffer = bytearray(messageSize)
        try:
            if buf.readinto(messageDataBuffer) != messageSize:
                self.logger.error("deserialize message error!")
                return
        except Exception as e:
            self.logger.error("deserialize message error!" + str(traceback.format_exc()))
            raise e
        else:
            msg = deserialize(msg, messageDataBuffer, TCompactProtocolFactory())
            return msg

    def get_message_size(self, msg=None):
        size = self.__MESSAGE_HEADER_BYTES_V3
        messageData = serialize(msg)
        return size + len(messageData)
