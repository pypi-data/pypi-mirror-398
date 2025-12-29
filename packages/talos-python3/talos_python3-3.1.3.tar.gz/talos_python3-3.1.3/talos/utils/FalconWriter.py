#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
#


import requests
import traceback
import logging
import json

logger = logging.getLogger("FalconWriter")


class FalconWriter(object):
	falconUrl = str
	headers = {'Content-type': 'application/json'}

	def __init__(self, falconUrl=None):
		self.falconUrl = falconUrl

	def push_falcon_data(self, falconData=None):
		try:
			resp = requests.post(self.falconUrl, data=json.dumps(falconData), headers=self.headers)
			if not resp.status_code == 200:
				logger.error("Post data failed, StatusCode: " + str(resp.status_code))
		except Exception as throwable:
			logger.error("catch Exception: " + str(traceback.format_exc()))




