#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.client.TalosClientConfigkeys import TalosClientConfigKeys
from talos.producer.TalosProducerConfigKey import TalosProducerConfigKeys
from talos.consumer.TalosConsumerConfigKeys import TalosConsumerConfigKeys
from talos.utils import Utils


class TalosClientConfig:
    # client configs
    _maxRetry = int
    _clientTimeout = int
    _clientConnTimeout = int
    _adminOpreationTimeout = int
    _serviceEndpint = str
    _secureServiceEndpint = int
    _maxTotalConnections = int
    _maxTotalConnectionsPerRoute = int
    _isRetry = bool
    _isAutoLocation = bool
    _isOpenDnsResolver = bool
    _scheduleInfoMaxRetry = int
    _updateScheduleInfoInterval = int
    _falconUrl = str
    _reportMetricIntervalMillis = int
    _clientMonitorSwitch = bool
    _consumerMetricFalconEndpoint = str
    _producerMetricFalconEndpoint = str
    _metricFalconStep = int
    _alertType = str
    _clusterName = str
    _scheduleInfoMaxRetry = int

    # producer configs
    _service_endpoint = str
    _maxBufferedMsgNumber = int
    _maxBufferedMsgBytes = int
    _maxBufferedMsgTime = int
    _maxPutMsgNumber = int
    _maxPutMsgBytes = int
    _maxSingleMessageBytes = int
    _producerCheckPartitionInterval = int
    # put failed related private
    _maxRetryTimes = int
    _putMessageBaseBackoffTime = int
    _putMessageMaxBackoffTime = int
    _putMessageMaxFailedTimes = int

    # consumer configs
    _threadPoolSize = int
    _checkPartitionInterval = int
    _workerInfoCheckInterval = int
    _reNewCheckInterval = int
    _reNewMaxRetry = int
    _selfRegisterMaxRetry = int
    _commitOffsetTreshold = int
    _commitOffsetInterval = int
    _fetchMessageInterval = int
    _checkLastCommitOffset = bool
    _waitPartitionWorkingTime = int
    _waitPartitionReduceTime = int
    _resetLatestOffsetWhenOutOfRange = bool
    _checkpointAutoCommit = bool
    _resetOffsetWhenStart = bool
    _resetOffsetValueWhenStart = int
    _maxFetchMessageNum = int
    _maxFetchMessageBytes = int

    def __init__(self, pro=None):
        self._properties = pro
        self._clientIp = Utils.get_host_ip()
        self._maxRetry = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_MAX_RETRY,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_MAX_RETRY_DEFAULT)
        self._clientTimeout = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_TIMEOUT_MILLI_SECS,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_TIMEOUT_MILLI_SECS_DEFAULT)
        self._clientConnTimeout = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_CONN_TIMECOUT_MILLI_SECS,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_CONN_TIMECOUT_MILLI_SECS_DEFAULT)
        self._adminOpreationTimeout = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_ADMIN_TIMEOUT_MILLI_SECS,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_ADMIN_TIMEOUT_MILLI_SECS_DEFAULT)
        self._serviceEndpint = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_SERVICE_ENDPOINT,
            TalosClientConfigKeys.GALAXY_TALOS_DEFAULT_SERVICE_ENDPOINT)
        if not self._serviceEndpint:
            raise RuntimeError("The property of 'galaxy.talos.service.endpoint' must be set")
        self._clusterName = self.get_service_endpoint().replace("http://", "")\
            .replace("https://", "")\
            .replace(".api.xiaomi.net", "")\
            .replace(".api.xiaomi.com", "")
        self._secureServiceEndpint = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_SECURE_SERVICE_ENDPOINT,
            TalosClientConfigKeys.GALAXY_TALOS_DEFAULT_SECURE_SERVICE_ENDPOINT)
        self._maxTotalConnections = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_HTTP_MAX_TOTAL_CONNECTION,
            TalosClientConfigKeys.GALAXY_TALOS_HTTP_MAX_TOTAL_CONNECTION_DEFAULT)
        self._maxTotalConnectionsPerRoute = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_HTTP_MAX_TOTAL_CONNECTION_PER_ROUTE,
            TalosClientConfigKeys.GALAXY_TALOS_HTTP_MAX_TOTAL_CONNECTION_PER_ROUTE_DEFAULT)
        self._isRetry = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_IS_RETRY,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_IS_RETRY_DEFAULT)
        self._isAutoLocation = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_IS_AUTO_LOCATION,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_IS_AUTO_LOCATION_DEFAULT)
        self._isOpenDnsResolver = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_IS_OPEN_DNS_RESOLVER,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_IS_OPEN_DNS_RESOLVER_DEFAULT)
        self._scheduleInfoMaxRetry = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_SCHEDULE_INFO_MAX_RETRY,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_SCHEDULE_INFO_MAX_RETRY_DEFAULT)
        self._updateScheduleInfoInterval = pro.get(
            TalosClientConfigKeys.GALSXY_TALOS_CLIENT_SCHEDULE_INFO_INTERVAL,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_SCHEDULE_INFO_INTERVAL_DEFAULT)
        self._fetchMessageInterval = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_FETCH_INTERVAL,
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_FETCH_INTERVAL_DEFAULT)
        self._falconUrl = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_METRIC_FALCON_URL,
            TalosClientConfigKeys.GALAXY_TALOS_METRIC_FALCON_URL_DEFAULT)
        self._reportMetricIntervalMillis = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_REPORT_METRIC_INTERVAL_MILLIS,
            TalosClientConfigKeys.GALAXY_TALOS_REPORT_METRIC_INTERVAL_MILLIS_DEFAULT)
        self._clientMonitorSwitch = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_FALCON_MONITOR_SWITCH,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_FALCON_MONITOR_SWITCH_DEFAULT)
        self._consumerMetricFalconEndpoint = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_METRIC_FALCON_ENDPOINT,
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_METRIC_FALCON_ENDPOINT_DEFAULT)
        self._producerMetricFalconEndpoint = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_PRODUCER_METRIC_FALCON_ENDPOINT,
            TalosClientConfigKeys.GALAXY_TALOS_PRODUCER_METRIC_FALCON_ENDPOINT_DEFAULT)
        self._metricFalconStep = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_FALCON_STEP,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_FALCON_STEP_DEFAULT)
        self._scheduleInfoMaxRetry = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_SCHEDULE_INFO_MAX_RETRY,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_SCHEDULE_INFO_MAX_RETRY_DEFAULT)
        self._alertType = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_ALERT_TYPE,
            TalosClientConfigKeys.GALAXY_TALOS_CLIENT_ALERT_TYPE_DEFAULT)

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
        self._threadPoolSize = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_THREAD_POOL_SIZE,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_THREAD_POOL_SIZE_DEFAULT)
        self._checkPartitionInterval = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_PARTITION_INTERVAL,
            TalosProducerConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_PARTITION_INTERVAL_DEFAULT)
        self._workerInfoCheckInterval = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_WORKER_INFO_INTERVAL,
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_WORKER_INFO_INTERVAL_DEFAULT)
        self._reNewCheckInterval = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_RENEW_INTERVAL,
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_RENEW_INTERVAL_DEFAULT)
        self._reNewMaxRetry = pro.get(
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_RENEW_MAX_RETRY,
            TalosClientConfigKeys.GALAXY_TALOS_CONSUMER_RENEW_MAX_RETRY_DEFAULT)
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

        # consumer configs
        self._selfRegisterMaxRetry = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_REGISTER_MAX_RETRY,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_REGISTER_MAX_RETRY_DEFAULT)
        self._commitOffsetTreshold = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_COMMIT_OFFSET_THRESHOLD,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_COMMIT_OFFSET_THRESHOLD_DEFAULT)
        self._commitOffsetInterval = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_COMMIT_OFFSET_INTERVAL,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_COMMIT_OFFSET_INTERVAL_DEFAULT)
        self._checkLastCommitOffset = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_LAST_COMMIT_OFFSET_SWITCH,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_CHECK_LAST_COMMIT_OFFSET_SWITCH_DEFAULT)
        self._waitPartitionWorkingTime = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_WAIT_PARTITION_WORKING_TIME,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_WAIT_PARTITION_WORKING_TIME_DEFAULT)
        self._waitPartitionReduceTime = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_WAIT_PARTITION_REDUCE_TIME,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_WAIT_PARTITION_REDUCE_TIME_DEFAULT)
        self._resetLatestOffsetWhenOutOfRange = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_OUT_OF_RANGE_RESET_LATEST_OFFSET,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_OUT_OF_RANGE_RESET_LATEST_OFFSET_DEFAULT)
        self._checkpointAutoCommit = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_CHECKPOINT_AUTO_COMMIT,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_CHECKPOINT_AUTO_COMMIT_DEFAULT)
        self._resetOffsetWhenStart = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_START_WHETHER_RESET_OFFSET,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_START_WHETHER_RESET_OFFSET_DEFAULT)
        self._resetOffsetValueWhenStart = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_START_RESET_OFFSET_VALUE,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_START_RESET_OFFSET_AS_START)
        self._maxFetchMessageNum = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_RECORDS,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_RECORDS_DEFAULT)
        self._maxFetchMessageBytes = pro.get(
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_BYTES,
            TalosConsumerConfigKeys.GALAXY_TALOS_CONSUMER_MAX_FETCH_BYTES_DEFAULT)

        # producer configs
        self._maxRetryTimes = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_RETRY_TIMES,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_RETRY_TIMES_DEFAULT)
        self._producerCheckPartitionInterval = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_CHECK_PARTITION_INTERVAL_DEFAULT)
        self._putMessageBaseBackoffTime = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_PUT_MESSAGE_BASE_BACKOFF_TIME,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_PUT_MESSAGE_BASE_BACKOFF_TIME_DEFAULT)
        self._putMessageMaxBackoffTime = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_PUT_MESSAGE_MAX_BACKOFF_TIME,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_PUT_MESSAGE_MAX_BACKOFF_TIME_DEFAULT)
        self._putMessageMaxFailedTimes = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_PUT_MESSAGE_MAX_FAILED_TIMES,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_PUT_MESSAGE_MAX_FAILED_TIMES_DEFAULT)
        self._maxSingleMessageBytes = pro.get(
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_SINGLE_MESSAGE_BYTES,
            TalosProducerConfigKeys.GALAXY_TALOS_PRODUCER_MAX_SINGLE_MESSAGE_BYTES_DEFAULT)

    def get_max_retry(self):
        return self._maxRetry

    def get_client_timeout(self):
        return self._clientTimeout

    def get_client_conn_timeout(self):
        return self._clientConnTimeout

    def get_admin_operation_timeout(self):
        return self._adminOpreationTimeout

    def get_service_endpoint(self):
        return self._serviceEndpint

    def get_secure_service_endpoint(self):
        return self._secureServiceEndpint

    def get_max_total_connections(self):
        return self._maxTotalConnections

    def get_max_total_connections_per_route(self):
        return self._maxTotalConnectionsPerRoute

    def get_is_retry(self):
        return self._isRetry

    def get_is_auto_location(self):
        return self._isAutoLocation

    def get_is_open_dns_resolver(self):
        return self._isOpenDnsResolver

    def get_schedule_info_max_retry(self):
        return self._scheduleInfoMaxRetry

    def get_update_schedule_info_interval(self):
        return self._updateScheduleInfoInterval

    # producer configs
    def get_producer_check_partition_interval(self):
        return self._producerCheckPartitionInterval

    def get_max_retry_times(self):
        return self._maxRetryTimes

    def get_put_message_base_backoff_time(self):
        return self._putMessageBaseBackoffTime

    def get_put_message_max_backoff_time(self):
        return self._putMessageMaxBackoffTime

    def get_put_message_max_failed_times(self):
        return self._putMessageMaxFailedTimes

    def get_max_buffered_msg_number(self):
        return self._maxBufferedMsgNumber

    def get_max_buffered_msg_bytes(self):
        return self._maxBufferedMsgBytes

    def get_max_buffered_msg_time(self):
        return self._maxBufferedMsgTime

    def get_max_put_msg_number(self):
        return self._maxPutMsgNumber

    def get_max_put_msg_bytes(self):
        return self._maxPutMsgBytes

    def get_max_single_msg_bytes(self):
        return self._maxSingleMessageBytes

    def get_thread_pool_size(self):
        return self._threadPoolSize

    def get_check_partition_interval(self):
        return self._checkPartitionInterval

    def get_check_worker_info_interval(self):
        return self._workerInfoCheckInterval

    def get_renew_check_interval(self):
        return self._reNewCheckInterval

    def get_renew_max_retry(self):
        return self._reNewMaxRetry

    def get_update_partition_id_interval(self):
        return self._updatePartitionIdInterval

    def get_wait_partition_working_time(self):
        return self._waitPartitionWorkingTime

    def get_wait_partition_reduce_time(self):
        return self._waitPartitionReduceTime

    def get_update_partition_msg_number(self):
        return self._updatePartitionMsgNum

    def get_compression_type(self):
        return self._compressionType

    def get_self_register_max_retry(self):
        return self._selfRegisterMaxRetry

    def get_commit_offset_threshold(self):
        return self._commitOffsetTreshold

    def get_commit_offset_interval(self):
        return self._commitOffsetInterval

    def get_fetch_message_interval(self):
        return self._fetchMessageInterval

    def is_check_last_commit_offset(self):
        return self._checkLastCommitOffset

    def is_reset_latest_offset_out_of_range(self):
        return self._resetLatestOffsetWhenOutOfRange

    def is_checkpoint_auto_commit(self):
        return self._checkpointAutoCommit

    def is_reset_offset_when_start(self):
        return self._resetOffsetWhenStart

    def get_reset_offset_value_when_start(self):
        return self._resetOffsetValueWhenStart

    def get_max_fetch_msg_num(self):
        return self._maxFetchMessageNum

    def get_max_fetch_msg_bytes(self):
        return self._maxFetchMessageBytes

    def get_client_ip(self):
        return self._clientIp

    def get_falcon_url(self):
        return self._falconUrl

    def is_open_client_monitor(self):
        return self._clientMonitorSwitch

    def get_report_metric_interval_millis(self):
        return self._reportMetricIntervalMillis

    def get_consumer_metric_falcon_endpoint(self):
        return self._consumerMetricFalconEndpoint

    def get_producer_metric_falcon_endpoint(self):
        return self._producerMetricFalconEndpoint

    def get_metric_falcon_step(self):
        return self._metricFalconStep

    def get_alert_type(self):
        return self._alertType

    def get_cluster_name(self):
        return self._clusterName

    def get_schedule_info_max_retry(self):
        return self._scheduleInfoMaxRetry

