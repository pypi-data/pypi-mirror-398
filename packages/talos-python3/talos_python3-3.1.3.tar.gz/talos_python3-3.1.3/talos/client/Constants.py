#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 


class Constants:
    # Constants for rest sever path
    TALOS_API_ROOT_PATH = "/v1/api"
    TALOS_TOPIC_SERVICE_PATH = TALOS_API_ROOT_PATH + "/topic"
    TALOS_MESSAGE_SERVICE_PATH = TALOS_API_ROOT_PATH + "/message"
    TALOS_QUOTA_SERVICE_PATH = TALOS_API_ROOT_PATH + "/quota"
    TALOS_CONSUMER_SERVICE_PATH = TALOS_API_ROOT_PATH + "/consumer"
    TALOS_METRIC_SERVICE_PATH = TALOS_API_ROOT_PATH + "/metric"

    TALOS_IDENTIFIER_DELIMITER = "#"
    TALOS_CONNECTION_DELIMITER = "-"
    TALOS_NAME_REGEX = "^(?!_)(?!-)(?!.*?_$)[a-zA-Z0-9_-]+$"
    TALOS_TEMPORARY_FILE_SUFFIX = ".tmp"

    # Constants for producer
    TALOS_SINGLE_MESSAGE_BYTES_MINIMAL = 1
    TALOS_SINGLE_MESSAGE_BYTES_MAXIMAL = 100 * 1024 * 1024
    TALOS_MESSAGE_BLOCK_BYTES_MAXIMAL = 200 * 1024 * 1024

    TALOS_PARTITION_KEY_LENGTH_MINIMAL = 1
    TALOS_PARTITION_KEY_LENGTH_MAXIMAL = 256

    # Constants for cloud - manager auth
    TALOS_CLOUD_TOPIC_NAME_DELIMITER = "/"
    TALOS_CLOUD_ORG_PREFIX = "CL"
    TALOS_CLOUD_TEAM_PREFIX = "CI"
    TALOS_CLOUD_AK_PREFIX = "AK"
    TALOS_GALAXY_AK_PREFIX = "EAK"

    # Constants for consumer metrics
    FETCH_MESSAGE_TIMES = "fetchMessage.60sRate"
    FETCH_MESSAGE_FAILED_TIMES = "fetchMessageFailed.60sRate"
    FETCH_MESSAGE_TIME = "fetchMessageTime.gauge"
    MAX_FETCH_MESSAGE_TIME = "fetchMessageTime.max"
    MIN_FETCH_MESSAGE_TIME = "fetchMessageTime.min"
    PROCESS_MESSAGE_TIME = "processMessageTime.gauge"
    MAX_PROCESS_MESSAGE_TIME = "processMessageTime.max"
    MIN_PROCESS_MESSAGE_TIME = "processMessageTime.min"

    # Constants for producer metrics
    PUT_MESSAGE_TIMES = "putMessage.60sRate"
    PUT_MESSAGE_FAILED_TIMES = "putMessageFailed.60sRate"
    PUT_MESSAGE_TIME = "putMessageTime.gauge"
    MAX_PUT_MESSAGE_TIME = "putMessageTime.max"
    MIN_PUT_MESSAGE_TIME = "putMessageTime.min"
