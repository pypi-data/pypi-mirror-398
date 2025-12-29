#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#

from io import BytesIO
import gzip
import logging
import traceback


class Gzip:
    logger = logging.getLogger("Gzip")

    def __init__(self):
        pass

    def compress(self, c_data):
        buf = BytesIO()
        try:
            with gzip.GzipFile(mode='wb', fileobj=buf) as f:
                f.write(c_data)
            return buf.getvalue()
        except Exception as e:
            self.logger.error("compress wrong" + str(traceback.format_exc()))
        finally:
            f.close()

    def decompress(self, c_data):
        try:
            buf = BytesIO(c_data)
            with gzip.GzipFile(mode='rb', fileobj=buf) as f:
                return f.read()
        except Exception as e:
            self.logger.error("uncompress wrong" + str(traceback.format_exc()))
        finally:
            f.close()

