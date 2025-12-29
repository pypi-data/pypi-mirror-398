#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 
from talos.client.serialization.MessageSerializer import MessageSerializer
from talos.thrift.message.ttypes import Message
from talos.thrift.message.ttypes import MessageType
from talos.client.serialization import MessageVersion
from struct import unpack, pack_into
from talos.utils.Utils import SerializeFormat
from talos.utils import Utils
import logging


class MessageSerializerV2(MessageSerializer):

    logger = logging.getLogger("MessageSerializerV2")

    __CREATE_TIMESTAMP_BYTES_V2 = 8
    __MESSAGE_TYPE_BYTES_V2 = 2
    __SEQUENCE_NUMBER_LENGTH_BYTES_V2 = 2
    __VERSION_NUMBER_LENGTH_V2 = 4
    __MESSAGE_DATA_LENGTH_BYTES_V2 = 4
    __MESSAGE_HEADER_BYTES_V2 = __VERSION_NUMBER_LENGTH_V2 + __MESSAGE_TYPE_BYTES_V2 + \
                                __CREATE_TIMESTAMP_BYTES_V2 + \
                                __SEQUENCE_NUMBER_LENGTH_BYTES_V2 + \
                                __MESSAGE_DATA_LENGTH_BYTES_V2

    # TalosProducer serialize
    def serialize(self, msg=None, buf=None):
        # write version number
        self.write_message_version(MessageVersion.MessageVersion(2), buf)

        # write create timestamp
        timestampBuffer = bytearray(self.__CREATE_TIMESTAMP_BYTES_V2)
        if msg.createTimestamp:
            pack_into(SerializeFormat.format_i64, timestampBuffer, 0, msg.createTimestamp)
        else:
            pack_into(SerializeFormat.format_i64, timestampBuffer, 0,
                      Utils.current_time_mills())
        buf.write(timestampBuffer)

        # write message type
        if not msg.messageType:
            raise RuntimeError("message must set messageType")
        else:
            messageTypeBuffer = bytearray(self.__MESSAGE_TYPE_BYTES_V2)
            pack_into(SerializeFormat.format_i16, messageTypeBuffer, 0, msg.messageType)
            buf.write(messageTypeBuffer)

        # write sequence number
        sequenceNumberBuffer = bytearray(self.__SEQUENCE_NUMBER_LENGTH_BYTES_V2)
        if msg.sequenceNumber:
            pack_into(SerializeFormat.format_i16, sequenceNumberBuffer, 0,
                      len(msg.sequenceNumber))
            buf.write(sequenceNumberBuffer)
            buf.write(msg.sequenceNumber)
        else:
            pack_into(SerializeFormat.format_i16,
                                             sequenceNumberBuffer, 0, 0)
            buf.write(sequenceNumberBuffer)

        # write message size
        sizeBuffer = bytearray(self.__MESSAGE_DATA_LENGTH_BYTES_V2)
        pack_into(SerializeFormat.format_i32, sizeBuffer, 0, len(msg.message))
        buf.write(sizeBuffer)

        # write message
        buf.write(msg.message)
        return

    # TalosConsumer deserialize
    def deserialize(self, header=None, buf=None):
        msg = Message
        # read create timestamp
        timestampBuffer = bytearray(self.__CREATE_TIMESTAMP_BYTES_V2)
        try:
            if buf.readinto(timestampBuffer) != self.__CREATE_TIMESTAMP_BYTES_V2:
                self.logger.error("deserialize create timestamp error!")
                return
        except Exception as e:
            self.logger.error("deserialize create timestamp error!" + e.message)
            raise e
        else:
            createTimestamp = int(unpack(SerializeFormat.format_i64, timestampBuffer)[0])
            msg.createTimestamp = createTimestamp

        # read message type
        messageTypeBuffer = bytearray(self.__MESSAGE_TYPE_BYTES_V2)
        try:
            if buf.readinto(messageTypeBuffer) != self.__MESSAGE_TYPE_BYTES_V2:
                self.logger.error("deserialize message type error!")
                return
        except Exception as e:
            self.logger.error("deserialize message type error!" + e.message)
            raise e
        else:
            messageType = int(unpack(SerializeFormat.format_i16, messageTypeBuffer)[0])
            if messageType == MessageType.UTF8:
                msg.messageType = MessageType.UTF8
            elif messageType == MessageType.BINARY:
                msg.messageType = MessageType.BINARY
            elif messageType == MessageType.AVRO:
                msg.messageType = MessageType.AVRO
            elif messageType == MessageType.PROTOBUF:
                msg.messageType = MessageType.PROTOBUF
            else:
                msg.messageType = MessageType.THRIFT

        # read sequence number
        sequenceNumLenBuffer = bytearray(self.__SEQUENCE_NUMBER_LENGTH_BYTES_V2)
        try:
            if buf.readinto(sequenceNumLenBuffer) != self.__SEQUENCE_NUMBER_LENGTH_BYTES_V2:
                self.logger.error("deserialize sequence number length error!")
                return
        except Exception as e:
            self.logger.error("deserialize sequence number length error!" + e.message)
            raise e
        else:
            sequenceNumLen = int(unpack(SerializeFormat.format_i16, sequenceNumLenBuffer)[0])

        if not sequenceNumLen == 0:
            sequenceNumberBuffer = bytearray(sequenceNumLen)
            try:
                if buf.readinto(sequenceNumberBuffer) != sequenceNumLen:
                    self.logger.error("deserialize sequence number error!")
                    return
            except Exception as e:
                self.logger.error("deserialize sequence number error!" + e.message)
                raise e
            else:
                sequenceNumber = str(sequenceNumberBuffer)
                msg.sequenceNumber = sequenceNumber

        # read message size
        messageSizeBuffer = bytearray(self.__MESSAGE_DATA_LENGTH_BYTES_V2)
        try:
            if buf.readinto(messageSizeBuffer) != self.__MESSAGE_DATA_LENGTH_BYTES_V2:
                self.logger.error("deserialize message size error!")
                return
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
        size = self.__MESSAGE_HEADER_BYTES_V2
        if msg.sequenceNumber:
            size += len(msg.sequenceNumber)
        size += len(msg.message)
        return size


