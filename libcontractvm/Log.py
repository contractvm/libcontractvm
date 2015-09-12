# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import logging
from colorlog import ColoredFormatter

formatter = ColoredFormatter (
	'%(log_color)s[%(asctime)s] %(module)s: %(message_log_color)s%(message)s',
	datefmt=None,
	reset=True,
	log_colors={
		'DEBUG':    'blue',
		'INFO':     'green',
		'WARNING':  'yellow',
		'ERROR':    'red',
		'CRITICAL': 'red',
	},
	secondary_log_colors={
		'message': {
			'DEBUG':    'purple',
			'INFO':     'yellow',
			'WARNING':  'green',
			'ERROR':    'yellow',
			'CRITICAL': 'red',
		}
	},
	style='%'
)

stream = logging.StreamHandler()
stream.setFormatter(formatter)

logger = logging.getLogger('libcontractvm')
logger.addHandler(stream)
logger.setLevel (10)
logger.propagate = False
