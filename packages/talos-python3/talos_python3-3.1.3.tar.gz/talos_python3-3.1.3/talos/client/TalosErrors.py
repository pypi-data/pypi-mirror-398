#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 

from talos.thrift.common.ttypes import ErrorCode
from talos.thrift.common.ttypes import HttpStatusCode


class TalosTransportError(Exception):
	HttpStatusCode = HttpStatusCode
	ErrorCode = int
	ErrorMessage = str
	ServerTime = int

	def __init__(self, httpStatusCode=None, errorMessage=None, timestamp=None):
		errorCode = None
		if httpStatusCode == HttpStatusCode.INVALID_AUTH:
			errorCode = ErrorCode.INVALID_AUTH_INFO
		elif httpStatusCode == HttpStatusCode.CLOCK_TOO_SKEWED:
			errorCode = ErrorCode.CLOCK_TOO_SKEWED
		elif httpStatusCode == HttpStatusCode.REQUEST_TOO_LARGE:
			errorCode = ErrorCode.REQUEST_TOO_LARGE
		elif httpStatusCode == HttpStatusCode.INTERNAL_ERROR:
			errorCode = ErrorCode.INTERNAL_SERVER_ERROR
		elif httpStatusCode == HttpStatusCode.BAD_REQUEST:
			errorCode = ErrorCode.BAD_REQUEST
		self.HttpStatusCode = httpStatusCode
		self.ErrorCode = errorCode
		self.ErrorMessage = errorMessage
		self.ServerTime = timestamp

	def get_error_code(self):
		return self.ErrorCode

	def string(self):
		if not self:
			return None
		errorString = "Transport error, ErrorCode: " + str(self.ErrorCode) + \
					  ", HttpStatusCode: " + str(self.HttpStatusCode) + \
					  ", ErrorMessage: " + self.ErrorMessage
		return errorString

	def error(self):
		return self.string()


class InvalidArgumentError(Exception):
	errorMsg = str

	def __init__(self, errorMsg=None):
		self.errorMsg = errorMsg

	def to_string(self):
		return self.errorMsg

