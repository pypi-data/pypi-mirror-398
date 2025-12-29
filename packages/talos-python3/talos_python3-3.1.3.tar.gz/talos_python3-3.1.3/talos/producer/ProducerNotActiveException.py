#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 
from talos.thrift.common.ttypes import GalaxyTalosException


class ProducerNotActiveException(GalaxyTalosException):
    def __init__(self, detailMsg=None):
        GalaxyTalosException().__init__(errMsg=detailMsg)
        self.errMsg = detailMsg





