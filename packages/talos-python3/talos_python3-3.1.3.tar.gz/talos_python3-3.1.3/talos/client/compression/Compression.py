# -*- coding:utf-8 -*-
#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 


from talos.thrift.message.ttypes import MessageCompressionType
from talos.thrift.message.ttypes import MessageBlock
from talos.thrift.message.ttypes import MessageAndOffset
from talos.thrift.common.ttypes import GalaxyTalosException
from talos.client.serialization.MessageSerializationFactory import MessageSerializationFactory
from talos.utils.Utils import current_time_mills
from talos.client.serialization.MessageSerialization import MessageSerialization
from talos.client.Constants import Constants
from talos.client.compression.Gzip import Gzip
from talos.client.compression.Snappy import Snappy
from io import BytesIO
import logging
import traceback


class Compression(object):

    logger = logging.getLogger("Compression")
    gzip = Gzip()
    snappy = Snappy()

    def compress(self, msgList=None, compressionType=None):
        return self.do_compress(msgList, compressionType, MessageSerializationFactory().get_default_message_version())

    def do_compress(self, msgList=None, compressionType=None, messageVersion=None):
        messageBlock = MessageBlock(startMessageOffset=0, messageNumber=0,
                                    messageBlockSize=0, appendTimestamp=0,
                                    createTimestamp=0, transactionId=0)
        messageCompressionType = MessageCompressionType._NAMES_TO_VALUES[compressionType]
        messageBlock.compressionType = messageCompressionType
        messageBlock.messageNumber = len(msgList)

        createTime = current_time_mills()
        if len(msgList) > 0:
            createTime = msgList[0].createTimestamp

        try:
            # assume the message bytes size is 256KB
            messageBlockData = bytearray()
            messageSerializedBuffer = bytearray()
            dataOutputIo = BytesIO(messageSerializedBuffer)
            index = 0
            for message in msgList:
                MessageSerialization().serialize_message(message, dataOutputIo, messageVersion)
                createTime += (message.createTimestamp - createTime) / (index + 1)
            messageBlock.createTimestamp = int(createTime)

            if messageCompressionType == MessageCompressionType.NONE:
                messageBlockData = dataOutputIo.getvalue()
            elif messageCompressionType == MessageCompressionType.GZIP:
                messageBlockData = self.gzip.compress(dataOutputIo.getvalue())
            elif messageCompressionType == MessageCompressionType.SNAPPY:
                messageBlockData = self.snappy.encode(dataOutputIo.getvalue())
            else:
                raise RuntimeError("Unsupported Compression Type: " + str(compressionType))

            # close dataOutputIo
            dataOutputIo.close()

            if len(messageBlockData) > Constants.TALOS_MESSAGE_BLOCK_BYTES_MAXIMAL:
                raise GalaxyTalosException(errMsg="MessageBlock must be less than or equal to " +
                                                  Constants.TALOS_MESSAGE_BLOCK_BYTES_MAXIMAL +
                                                  " bytes, got bytes: " + str(len(messageBlockData)))
            messageBlock.messageBlock = messageBlockData
            messageBlock.messageBlockSize = len(messageBlockData)
        except (RuntimeError, Exception) as e:
            self.logger.info("compress MessageList failed!" + str(traceback.format_exc()))
            raise e

        return messageBlock

    def decompress(self, msgBlockList=None, unHandledMessageNumber=None):
        if len(msgBlockList) > 0:
            messageAndOffsetList = []
            unHandledNumber = unHandledMessageNumber
            for messageBlock in reversed(msgBlockList):
                msgAndOffsetList = self.do_decompress(messageBlock, unHandledNumber)
                unHandledNumber += len(msgAndOffsetList)
                messageAndOffsetList[0:0] = msgAndOffsetList
            return messageAndOffsetList
        else:
            return []

    def do_decompress(self, messageBlock=None, unHandledNumber=None):
        messageBlockData = BytesIO()
        if messageBlock.compressionType == MessageCompressionType.NONE:
            messageBlockData = BytesIO(messageBlock.messageBlock)
        elif messageBlock.compressionType == MessageCompressionType.GZIP:
            messageBlockData = BytesIO(self.gzip.decompress(messageBlock.messageBlock))
        elif messageBlock.compressionType == MessageCompressionType.SNAPPY:
            messageBlockData = BytesIO(self.snappy.decode(messageBlock.messageBlock))

        messageNumber = messageBlock.messageNumber

        messageAndOffsetList = []
        try:
            i = 0
            while i < messageNumber:
                messageAndOffset = MessageAndOffset()
                messageAndOffset.messageOffset = messageBlock.startMessageOffset + i
                message = MessageSerialization().deserialize_message(messageBlockData)
                if messageBlock.appendTimestamp:
                    message.appendTimestamp = messageBlock.appendTimestamp
                messageAndOffset.message = message
                messageAndOffset.unHandledMessageNumber = unHandledNumber + messageNumber - 1 - i

                # add message to messageList
                messageAndOffsetList.append(messageAndOffset)
                i += 1
        except Exception as e:
            self.logger.error("Decompress messageBlock failed" + str(traceback.format_exc()))
        return messageAndOffsetList


