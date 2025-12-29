#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.utils import Utils
from talos.client.TalosClientConfig import TalosClientConfig
from talos.producer.TalosProducerConfigKey import TalosProducerConfigKeys


class TalosProducerConfig(TalosClientConfig):
    _service_endpoint = str
    _maxBufferedMsgNumber = int
    _maxBufferedMsgBytes = int
    _maxBufferedMsgTime = int
    _maxPutMsgNumber = int
    _maxPutMsgBytes = int

    def __init__(self, pro=None):
        self._properties = pro
        self._maxBufferedMsgNumber = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MESSAGE_NUMBER,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MESSAGE_NUMBER_DEFAULT)
        self._maxBufferedMsgBytes = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MESSAGE_BYTES,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MESSAGE_BYTES_DEFAULT)
        self._maxBufferedMsgTime = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MILLI_SECS,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_BUFFERED_MILLI_SECS_DEFAULT)
        self._maxPutMsgNumber = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER_DEFAULT)
        self._maxPutMsgBytes = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES_DEFAULT)
        self._threadPoolsize = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_THREAD_POOL_SIZE,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_THREAD_POOL_SIZE_DEFAULT)
        self._checkPartitionInterval = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL_DEFAULT)
        self._updatePartitionIdInterval = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITIONID_INTERVAL,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITIONID_INTERVAL_DEFAULT)
        self._waitPartitionWorkingTime = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_WAIT_PARTITION_WORKING_TIME,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_WAIT_PARTITION_WORKING_TIME_DEFAULT)
        self._updatePartitionMsgNum = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITION_MSGNUMBER,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITION_MSGNUMBER_DEFAULT)
        self._compressionType = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_COMPRESSION_TYPE,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_COMPRESSION_TYPE_DEFAULT)

        if not (self._compressionType == "NONE" or self._compressionType == "GZIP"
                or self._compressionType == "SNAPPY"):
            raise RuntimeError("Unsupported Compression Type: " + self._compressionType)

    def parameter_checking(self):
        Utils.check_parameter_range(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER,
            self._maxPutMsgNumber,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER_MINIMUM,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_NUMBER_MAXIMUM)
        Utils.check_parameter_range(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES,
            self._maxPutMsgBytes,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES_MINIMUM,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_PUT_MESSAGE_BYTES_MAXIMUM)
        Utils.check_parameter_range(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL,
            self._checkPartitionInterval,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL_MINIMUM,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL_MAXIMUM)
        Utils.check_parameter_range(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITIONID_INTERVAL,
            self._updatePartitionIdInterval,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITIONID_INTERVAL_MINIMUM,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_UPDATE_PARTITIONID_INTERVAL_MAXIMUM)
        Utils.check_parameter_range(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_SINGLE_MESSAGE_BYTES,
            self._maxSingleMessageBytes,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_SINGLE_MESSAGE_BYTES_MINIMUM,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_SINGLE_MESSAGE_BYTES_MAXIMUM)

    def get_max_buffered_msg_number(self):
        return self._maxBufferedMsgNumber

    def get_max_buffered_msg_bytes(self):
        return self._maxBufferedMsgBytes

    def get_max_buffered_msg_time(self):
        return self._maxBufferedMsgTime

    def get_max_put_msg_number(self):
        return self._maxPutMsgNumber

    def get_max_put_msg_bytes(self):
        return self._maxBufferedMsgBytes

    def get_thread_pool_size(self):
        return self._threadPoolsize

    def get_check_partition_interval(self):
        return self._checkPartitionInterval

    def get_update_partition_id_interval(self):
        return self._updatePartitionIdInterval

    def get_wait_partition_working_time(self):
        return self._waitPartitionWorkingTime

    def get_update_partition_msg_number(self):
        return self._updatePartitionMsgNum

    def get_compression_type(self):
        return self._compressionType

    def get_service_endpoint(self):
        return super(TalosProducerConfig, self).get_service_endpoint()

