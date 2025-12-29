#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

# read properties for client / consumer / producer

from talos.client.TalosErrors import InvalidArgumentError
from talos.client.Constants import Constants
from talos.thrift.message.ttypes import MessageOffset
from talos.thrift.common.ttypes import GalaxyTalosException
from talos.thrift.common.ttypes import ErrorCode
import functools
import time
import re
import uuid
import threading
import socket
import math


def synchronized(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.synchronizedLock:
            return func(self, *args, **kwargs)
    return wrapper


class ReadWriteLock:
    """ A lock object that allows many simultaneous "read locks", but
    only one "write lock." """
    def __init__(self):
        self.rlock = threading.Lock()
        self.wlock = threading.Lock()
        self.reader = 0

    def write_acquire(self):
        self.wlock.acquire()

    def write_release(self):
        self.wlock.release()

    def read_acquire(self):
        self.rlock.acquire()
        self.reader += 1
        if self.reader == 1:
            self.wlock.acquire()
        self.rlock.release()

    def read_release(self):
        self.rlock.acquire()
        self.reader -= 1
        if self.reader == 0:
            self.wlock.release()
        self.rlock.release()


def current_time_mills():
    return int(time.time() * 1000)


def update_message(message=None, messageType=None):
    if not message.createTimestamp:
        message.createTimestamp = current_time_mills()

    if not message.messageType:
        message.messageType = messageType


def check_message_list_validity(msgList=None, producerConfig=None):
    totalSize = 0
    for message in msgList:
        check_message_validity(message, producerConfig)
        totalSize += len(message.message)

    # is too large, and not just throw exception;
    if totalSize > producerConfig.get_max_single_msg_bytes() * 2:
        raise InvalidArgumentError("Total Messages byte must less than " +
                                   str(producerConfig.get_max_single_msg_bytes() * 2))


def check_message_validity(message=None, producerConfig=None):
    check_message_len_validity(message, producerConfig)
    check_message_sequence_number_validity(message)
    check_message_type_validity(message)


def check_message_len_validity(message=None, producerConfig=None):
    if not message.message:
        raise InvalidArgumentError("Field \"message\" must be set")

    data = message.message
    max_bytes = producerConfig.get_max_single_msg_bytes() \
        if producerConfig != None else Constants.TALOS_SINGLE_MESSAGE_BYTES_MAXIMAL
    if len(data) > max_bytes or len(data) < Constants.TALOS_SINGLE_MESSAGE_BYTES_MINIMAL:
        raise InvalidArgumentError("Data must be less than or equal to " +
                                   str(max_bytes) + " bytes, got bytes: " + str(len(data)))


def check_message_sequence_number_validity(message=None):
    if not message.sequenceNumber:
        return

    sequenceNumber = message.sequenceNumber
    if len(sequenceNumber) > Constants.TALOS_PARTITION_KEY_LENGTH_MAXIMAL\
            or len(sequenceNumber) < Constants.TALOS_PARTITION_KEY_LENGTH_MINIMAL:
        raise InvalidArgumentError("Invalid sequenceNumber which length must be at least "
                                   + str(Constants.TALOS_PARTITION_KEY_LENGTH_MINIMAL) +
                                   " and at most " + str(Constants.TALOS_PARTITION_KEY_LENGTH_MAXIMAL)
                                   + ", got " + str(len(sequenceNumber)))


def check_message_type_validity(message=None):
    if not message.messageType:
        raise InvalidArgumentError("Filed \"messageType\" must be set")


def check_parameter_range(parameter=None, value=None, minValue=None, maxValue=None):
    if value < minValue or value > maxValue:
        raise InvalidArgumentError(parameter + " should be in range [" + str(minValue) +
                                   ", " + str(maxValue) + "], got: " + str(value))


def generate_request_sequence_id(clientId=None, requestId=None):
    check_name_validity(clientId)
    return clientId + Constants.TALOS_IDENTIFIER_DELIMITER + str(requestId.get_and_set(requestId.value + 1))


# The format of cloud topicName is: orgId/topicName
def check_cloud_topic_name_validity(topicName=None):
    if not topicName or len(topicName) == 0:
        raise InvalidArgumentError("Got null topicName")
    items = topicName.split(Constants.TALOS_CLOUD_TOPIC_NAME_DELIMITER)
    # either 'xxx/xxx/'(split 2), '/xxx'(split 2) or 'xx//xx'(split 3) are invalid
    if len(items) != 2 or topicName.endswith(Constants.TALOS_CLOUD_TOPIC_NAME_DELIMITER) or not topicName.startswith(Constants.TALOS_CLOUD_ORG_PREFIX):
        raise InvalidArgumentError("The format of topicName used by cloud-manager must be: orgId/topicName")
    # check real topic name validity
    check_name_validity(items[1])


def check_name_validity(name=None):
    if (not name) or len(name) <= 0:
        return
    if (not re.match(Constants.TALOS_NAME_REGEX, name)) or len(name) > 80:
        raise InvalidArgumentError("invalid str: " + name + ". please name the str only " +
                                   "with the regex set: [a-zA-Z0-9_-]. Its length must be" +
                                   " [1, 80] and cannot start with '_' or '-'.")


def generate_client_id(clientIp=None, prefix=None):
    check_name_validity(prefix)
    return clientIp.replace(".", "-") + "-" + prefix + generate_client_id_()


def generate_client_id_():
    return str(current_time_mills()) + str(uuid.uuid4())[0:8]


def check_topic_name(topicName=None):
    if Constants.TALOS_CLOUD_TOPIC_NAME_DELIMITER in topicName:
        raise InvalidArgumentError("The topic name format in TopicAndPartition should" +
                                   " not be: orgId/topicName")


def check_start_offset_validity(startOffset=None):
    if startOffset >= 0 or startOffset == MessageOffset.START_OFFSET or \
            startOffset == MessageOffset.LATEST_OFFSET:
        return
    raise InvalidArgumentError("invalid startOffset: " + str(startOffset) +
                               ". It must be greater than or equal to 0, " +
                               "or equal to MessageOffset.START_OFFSET/MessageOffset.LATEST_OFFSET")


def get_error_code(throwable=None):
    if isinstance(throwable, GalaxyTalosException):
        return throwable.errorCode
    else:
        pass


def is_topic_not_exist(throwable=None):
    return get_error_code(throwable) == ErrorCode.TOPIC_NOT_EXIST


def is_partition_not_serving(throwable=None):
    return get_error_code(throwable) == ErrorCode.PARTITION_NOT_SERVING


def is_partition_not_exist(throwable=None):
    return get_error_code(throwable) == ErrorCode.PARTITION_NOT_EXIST


def is_offset_out_of_range(throwable=None):
    return get_error_code(throwable) == ErrorCode.MESSAGE_OFFSET_OUT_OF_RANGE


def get_topic_name_by_resource_name(topicTalosResourceName=None):
    itemList = topicTalosResourceName.split(Constants.TALOS_IDENTIFIER_DELIMITER)
    try:
        assert len(itemList) >= 3
    except AssertionError as e:
        raise e
    return itemList[len(itemList) - 2]


def get_put_msg_failed_delay(retry=None, producerConfig=None):
    delayTimes = int(math.pow(2, retry))
    return min(delayTimes * producerConfig.get_put_message_base_backoff_time(),
               producerConfig.get_put_message_max_backoff_time())


def sleep_pause_time(pauseTime=None):
    if pauseTime > 0:
        try:
            time.sleep(pauseTime)
        except Exception as ie:
            raise RuntimeError("thread sleep failed" + ie.message)


class HashCode:

    def convert_n_bytes(self, n, b):
        bits = b * 8
        return (n + 2 ** (bits - 1)) % 2 ** bits - 2 ** (bits - 1)

    def convert_4_bytes(self, n):
        return self.convert_n_bytes(n, 4)

    @classmethod
    def HashCode(cls, s):
        h = 0
        n = len(s)
        for i, c in enumerate(s):
            h = h + ord(c) * 31 ** (n - 1 - i)
        return cls().convert_4_bytes(h)


class SerializeFormat(object):

    format_i16 = '>h'
    format_i32 = '>i'
    format_i64 = '>Q'


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

