#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

import abc
from talos.client.serialization.MessageVersion import MessageVersion
from talos.utils.Utils import SerializeFormat
from struct import pack, unpack


class MessageSerializer(object):

    VERSION_NUMBER_LENGTH = 4
    _CHARSET = "utf-8"

    @classmethod
    def decode_message_version(cls, header=None):
        if chr(header[0]) != 'V':
            return MessageVersion(1)
        else:
            versionNumberTuple = unpack(SerializeFormat.format_i16, header[1:3])
            versionNumber = versionNumberTuple[0]
            return MessageVersion(versionNumber)

    @classmethod
    def write_message_version(cls, version=None, buffer=None):
        versionNumber = version.get_version_number()
        buffer.write(b'V')
        buffer.write(pack(SerializeFormat.format_i16, versionNumber))
        buffer.write(pack('b', 0))

    # TalosProducer serialize
    @abc.abstractmethod
    def serialize(self, msg=None, buf=None):
        pass

    # TalosConsumer deserialize
    @abc.abstractmethod
    def deserialize(self, header=None, buf=None):
        pass

    @abc.abstractmethod
    def get_message_size(self, msg=None):
        pass







