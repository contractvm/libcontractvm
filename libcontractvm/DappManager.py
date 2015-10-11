# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import requests
import binascii
import json
import sys
import logging
import time
from threading import Thread
from threading import Lock
from colorlog import ColoredFormatter
from libcontractvm import Wallet
from libcontractvm import ConsensusManager
from . import Log

logger = logging.getLogger('libcontractvm')

class DappManager:
	def __init__ (self, consensusmgr, wallet):
		self.consensusManager = consensusmgr
		self.wallet = wallet
		
	def _produce_transaction (self, method, arguments, bmethod = 'broadcast'):
		logger.info ('Producing transaction: %s %s', method, str (arguments))

		while True:
			best = self.consensusManager.getBestNode()

			# Create the transaction
			res = self.consensusManager.jsonCall (best, method, arguments)
			#print (res, best)
			txhash = self.wallet.createTransaction ([res['outscript']], res['fee'])

			if txhash == None:
				logger.error ('Failed to create transaction')
				time.sleep (5)
				continue

			# Broadcast the transaction
			cid = self.consensusManager.jsonCall (best, bmethod, [txhash, res['tempid']])

			if cid == None:
				logger.error ('Broadcast failed')
				time.sleep (5)
				continue

			cid = cid['txid']

			if cid != None:
				logger.info ('Broadcasting transaction: %s', cid)
				return cid
			else:
				logger.error ('Failed to produce transaction, retrying in 5 seconds')
				time.sleep (5)

