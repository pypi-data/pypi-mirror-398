#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 
from abc import abstractmethod


class Partitioner:

    @abstractmethod
    def partition(self, partitionKey=None, partitionNum=None):
        pass
