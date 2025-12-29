#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.serialization.MessageSerializer import MessageSerializer
from talos.thrift.message.ttypes import Message
from struct import unpack, pack_into
from talos.utils.Utils import SerializeFormat
import logging


class MessageSerializerV1(MessageSerializer):

    logger = logging.getLogger("MessageSerializerV1")

    __MESSAGE_HEADER_BYTES_V1 = 8
    __SEQUENCE_NUMBER_LENGTH_BYTES_V1 = 4
    __MESSAGE_DATA_LENGTH_BYTES_V1 = 4

    # TalosProducer serialize
    def serialize(self, msg=None, buf=None):
        # write sequence number
        sequenceNumberBuffer = bytearray(self.__SEQUENCE_NUMBER_LENGTH_BYTES_V1)
        if msg.sequenceNumber:
            pack_into(SerializeFormat.format_i32, sequenceNumberBuffer, 0, len(msg.sequenceNumber))
            buf.write(sequenceNumberBuffer)
            buf.write(msg.sequenceNumber)
        else:
            pack_into(SerializeFormat.format_i32, sequenceNumberBuffer, 0, 0)
            buf.write(sequenceNumberBuffer)

        # write message size
        sizeBuffer = bytearray(self.__MESSAGE_DATA_LENGTH_BYTES_V1)
        pack_into(SerializeFormat.format_i32, sizeBuffer, 0, len(msg.message))
        buf.write(sizeBuffer)

        # write message
        buf.write(msg.message)
        return

    # TalosConsumer deserialize
    def deserialize(self, header=None, buf=None):
        msg = Message()
        # generate sequence number len
        sequenceNumLen = int(unpack(SerializeFormat.format_i32, header)[0])

        # read sequence number
        if sequenceNumLen != 0:
            try:
                sequenceNumberBuffer = bytearray(sequenceNumLen)
                if buf.readinto(sequenceNumberBuffer) != sequenceNumLen:
                    self.logger.error("deserialize sequence number error!")
                    return
            except Exception as e:
                self.logger.error("deserialize sequence number error!" + e.message)
                raise e
            else:
                msg.sequenceNumber = str(sequenceNumberBuffer)

        # read message size
        messageSizeBuffer = bytearray(self.__MESSAGE_DATA_LENGTH_BYTES_V1)
        try:
            if buf.readinto(messageSizeBuffer) != self.__MESSAGE_DATA_LENGTH_BYTES_V1:
                self.logger.error("deserialize message error!")
        except Exception as e:
            self.logger.error("deserialize message size error!" + e.message)
            raise e
        else:
            messageSize = int(unpack(SerializeFormat.format_i32, messageSizeBuffer)[0])

        # read message
        messageDataBuffer = bytearray(messageSize)
        try:
            if buf.readinto(messageDataBuffer) != messageSize:
                self.logger.error("deserialize message error!")
                return
        except Exception as e:
            self.logger.error("deserialize message error!" + e.message)
            raise e
        else:
            msg.message = messageDataBuffer

        return msg

    def get_message_size(self, msg=None):
        size = self.__MESSAGE_HEADER_BYTES_V1
        if msg.sequenceNumber:
            size += len(msg.sequenceNumber)
        size += len(msg.message)
        return size


