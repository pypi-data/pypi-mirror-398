#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 


class MessageVersion(object):

    _version = int

    def __init__(self, version=None):
        self._version = version

    def get_version_number(self):
        return self._version

    def get_version(self):
        if self._version == 1:
            return "V1"
        elif self._version == 2:
            return "V2"
        elif self._version == 3:
            return "V3"
        return "UNKNOW"





