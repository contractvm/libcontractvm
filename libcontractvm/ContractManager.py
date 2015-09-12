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
from libcontractvm import Wallet
from libcontractvm import ContractException
from libcontractvm import ConsensusManager

from . import Log

logger = logging.getLogger('libcontractvm')

class ContractManager:
	BLOCKING_TIMEOUT = 5
	POLLING_TIMEOUT = 15

	STATE_NO_WALLET = -1
	STATE_INIT = 0
	STATE_TELL_WAIT = 5
	STATE_PENDING_FOR_COMPLIANT = 8
	STATE_PENDING = 10
	STATE_FUSED = 15
	STATE_SESSION_END = 20

	def __init__ (self, consensusManager, wallet = None, contractHash = None):
		self.consensusManager = consensusManager

		self.contracthash = contractHash
		self.contractobject = None

		self.sessionhash = None
		self.sessionobject = None
		self.pid = None

		self.wallet = wallet
		self.state = ContractManager.STATE_NO_WALLET

		if self.wallet == None:
			self.wallet = Wallet.Wallet (self.consensusManager.getChain ())

		if self.wallet == None:
			raise ContractException.WalletUndefinedException ()
		else:
			self.state = ContractManager.STATE_INIT

		# Retrive passed contracthash
		if self.contracthash != None:
			# Get the contract from node
			r = self.consensusManager.jsonConsensusCall ('tst.getcontract', [self.contracthash])['result']

			if 'error' in r:
				raise ContractException.ContractNotPresentException ()
			else:
				self.contractobject = r
				self.state = STATE_PENDING


		# Handler
		self.onreceivehandler = None
		self.ondutyhandler = None
		self.onsessionstarthandler = None
		self.oncontractpublishhandler = None
		self.onsessionupdatehandler = None

		# Start the polling thread
		self.polling_thread = Thread(target=self._polling_job, args=())
		self.polling_thread.start()
		self.poll_lock = Lock ()

		# List of txid of received values
		self.received = []

		# List of started threads
		self.threads = []

		#
		self.nonce = 0


	def _polling_job (self):
		while True:
			if self.state == ContractManager.STATE_INIT:
				pass

			elif self.state == ContractManager.STATE_TELL_WAIT:
				# Get the contract
				contr = self.consensusManager.jsonConsensusCall ('tst.getcontract', [self.contracthash])['result']

				if not 'error' in contr:
					self.poll_lock.acquire ()
					self.contractobject = contr
					self.state = ContractManager.STATE_PENDING_FOR_COMPLIANT

					logger.info ('State change for contract %s: STATE_TELL_WAIT -> STATE_PENDING_FOR_COMPLIANT', self.contracthash)

					self.sessionhash = self.contractobject ['session']
					if self.sessionhash != None:
						self.state = ContractManager.STATE_FUSED
						logger.info ('State change for contract %s: STATE_PENDING -> STATE_FUSED', self.contracthash)

						# Get the session object
						self.sessionobject = self.consensusManager.jsonConsensusCall ('tst.getsession', [self.sessionhash])['result']
						self.pid = str (self.sessionobject['players'][self.wallet.getAddress ()])
					self.poll_lock.release()

					if self.state == ContractManager.STATE_PENDING and self.oncontractpublishhandler != None:
						self._start_thread (self.oncontractpublishhandler, (self,))

					elif self.state == ContractManager.STATE_FUSED and self.onsessionstarthandler != None:
						self._start_thread (self.onsessionstarthandler, (self,))


			elif self.state == ContractManager.STATE_PENDING_FOR_COMPLIANT:
				contr = self.consensusManager.jsonConsensusCall ('tst.getcontract', [self.contracthash])['result']

				if not 'error' in contr:
					if contr['session'] != None:
						self.state = ContractManager.STATE_PENDING
						logger.info ('State change for contract %s: STATE_PENDING_FOR_COMPLIANT -> STATE_PENDING', self.contracthash)
						continue

				if not 'error' in contr:
					res = self.consensusManager.jsonCallFromAll ('tst.compliantwithcontract', [self.contracthash])
					compliants = []
					for x in res:
						compliants += x['result']['contracts']

					if len (compliants) > 0:
						try:
							self.fuse (compliants[0])
							self.state = ContractManager.STATE_PENDING
							logger.info ('State change for contract %s: STATE_PENDING_FOR_COMPLIANT -> STATE_PENDING', self.contracthash)
						except ContractException.ContractAlreadyFusedException:
							pass


			elif self.state == ContractManager.STATE_PENDING:
				#logger.debug ('getcontract %s', self.contracthash)

				# Get the contract
				contr = self.consensusManager.jsonConsensusCall ('tst.getcontract', [self.contracthash])['result']

				if not 'error' in contr:
					if contr['session'] != None:
						self.poll_lock.acquire ()

						self.contractobject = contr
						self.sessionhash = self.contractobject ['session']
						self.state = ContractManager.STATE_FUSED
						logger.info ('State change for contract %s: STATE_PENDING -> STATE_FUSED', self.contracthash)

						# Get the session object
						self.sessionobject = self.consensusManager.jsonConsensusCall ('tst.getsession', [self.sessionhash])['result']
						self.pid = str (self.sessionobject['players'][self.wallet.getAddress ()])
						self.poll_lock.release ()

						self._start_thread (self.onsessionstarthandler, (self,))
				else:
					raise ContractException.ContractNotPresentException ()


			elif self.state == ContractManager.STATE_FUSED:
				#logger.debug ('getsession %s', self.sessionhash)

				# Get the session object
				sob = self.consensusManager.jsonConsensusCall ('tst.getsession', [self.sessionhash])['result']

				self.poll_lock.acquire ()
				self.sessionobject = sob
				self.poll_lock.release ()

				if int (self.sessionobject['state']['time_last']) != int (sob['state']['time_last']):
					logger.debug ('Update in session - Culpable %s, Duty %s, End %s, Timelast %s, Actions %d, Possible %s, Pending %s',
							str (sob['state']['culpable']), str (sob['state']['duty']), str (sob['state']['end']),
							str (sob['state']['time_last']), len (sob['state']['history']),
							str (sob['state']['possible']), str (sob['state']['pending']))

					self._start_thread (self.onsessionupdatehandler, (self, self.sessionobject, ))

				if len (self.sessionobject['state']['pending'][self.pid]) > 0 and self.onreceivehandler != None:
					d = self.receive ()
					if d != None:
						self._start_thread (self.onreceivehandler, (self, d, ))

				#print (self.sessionobject['state'])
				if self.sessionobject['state']['end'] == True:
					logger.info ('State change for contract %s: STATE_FUSED -> STATE_SESSION_END', self.contracthash)
					self.poll_lock.acquire ()
					self.state = ContractManager.STATE_SESSION_END
					self.poll_lock.release ()


			elif self.state == ContractManager.STATE_SESSION_END:
				#logger.debug ('Polling %s STATE_SESSION_END', self.contracthash)
				pass

			time.sleep (ContractManager.POLLING_TIMEOUT)


	def _produce_transaction (self, method, arguments):
		logger.info ('Producing transaction: %s %s', method, str (arguments))

		while True:
			best = self.consensusManager.getBestNode()

			# Create the transaction
			res = self.consensusManager.jsonCall (best, method, arguments)
			txhash = self.wallet.createTransaction ([res['outscript']], res['fee'])

			if txhash == None:
				logger.error ('Failed to create transaction')
				time.sleep (5)
				continue

			# Broadcast the transaction
			cid = self.consensusManager.jsonCall (best, 'tst.broadcast_custom', [txhash, res['tempid']])

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


	def _execute_do (self, action, value = None):
		if self.nonce < int (self.sessionobject['state']['nonce_last']):
			self.nonce = int (self.sessionobject['state']['nonce_last']) + 1
		else:
			self.nonce += 1

		return self._produce_transaction ('tst.do', [self.sessionhash, action, value, self.nonce, self.wallet.getAddress ()])


	def _start_thread (self, fun, params):
		if fun != None:
			t = Thread(target=fun, args=params)
			t.start()
			self.threads.append (t)



	# Compliance
	def areCompliant (self, c1, c2):
		return self.consensusManager.jsonConsensusCall ('tst.checkcompliance', [c1, c2])['result']['compliant']

	# Static checks
	def translate (self, contract):
		return self.consensusManager.jsonConsensusCall ('tst.translatecontract', [contract])['result']['contract']

	def validate (self, contract):
		return self.consensusManager.jsonConsensusCall ('tst.validatecontract', [contract])['result']['valid']

	def dual (self, contract):
		return self.consensusManager.jsonConsensusCall ('tst.dualcontract', [contract])['result']['contract']


	def getWallet (self):
		return self.wallet

	def getSessionHash (self):
		return self.sessionhash

	def getHash (self):
		return self.contracthash

	def getChainCode (self):
		return self.consensusManager.getChain ()

	def getTime (self):
		return int (self.consensusManager.jsonConsensusCall ('tst.info')['result']['time'])

	def getSessionStartTime (self):
		if self.session == None:
			raise ContractException.ContractNotFusedException ()
		else:
			self.poll_lock.acquire ()
			stime = self.sessionobject['state']['time_start']
			self.poll_lock.release ()
			return stime

	def isCulpable (self):
		if self.sessionobject == None:
			raise ContractException.ContractNotFusedException ()
		else:
			self.poll_lock.acquire ()
			v = self.sessionobject['state']['culpable'][self.pid]
			self.poll_lock.release ()
			return v


	def isFused (self):
		return self.sessionhash != None

	def isOnDuty (self):
		if self.sessionobject == None:
			raise ContractException.ContractNotFusedException ()
		else:
			self.poll_lock.acquire ()
			v = self.sessionobject['state']['duty'][self.pid]
			self.poll_lock.release ()
			return v

	def isSessionStarted (self):
		return self.isFused ()


	def receive (self):
		if self.state != ContractManager.STATE_FUSED:
			return None

		if len (self.sessionobject['state']['pending'][self.pid]) < 1:
			return None
		else:
			pending = self.sessionobject['state']['pending'][self.pid]
			res = {}

			for p in pending:
				if not (pending[p]['action'] in self.received):
					self.received.append (pending[p]['action'])
					self._execute_do ('?'+p)
					res [p] = pending[p]['value']

			if len (res) != 0:
				return res
			else:
				return None


	def send (self, action, value=None):
		if self.state != ContractManager.STATE_FUSED:
			return False
		return (self._execute_do ('!'+action, value) != None)



	def setHash (self, contractHash):
		self.poll_lock.acquire ()
		self.state = ContractManager.STATE_TELL_WAIT
		self.contracthash = contractHash
		self.poll_lock.release ()


	def tell (self, contract):
		cid = self._produce_transaction ('tst.tell', [contract, self.wallet.getAddress (), 100])
		if cid != None:
			self.poll_lock.acquire ()
			self.state = ContractManager.STATE_TELL_WAIT
			self.contracthash = cid
			self.poll_lock.release ()
			#logger.debug ('Tell of contract %s broadcast done', cid)
			return self.contracthash
		else:
			raise ContractException.ContractTellFailedException ()


	def fuse (self, contractqhash):
		if self.isFused ():
			raise ContractException.ContractAlreadyFusedException ()
		else:
			sid = self._produce_transaction ('tst.fuse', [self.contracthash, contractqhash, self.wallet.getAddress ()])
			if sid != None:
				self.poll_lock.acquire ()
				self.sessionhash = sid
				self.state = ContractManager.STATE_PENDING
				self.poll_lock.release ()
				#logger.debug ('Fuse of contracts %s and %s broadcast done', self.contracthash, contractqhash)
				return True
			else:
				raise ContractException.ContractFuseFailedException ()


	def accept  (self, contractqhash):
		if self.isFused ():
			raise ContractException.ContractAlreadyFusedException ()
		else:
			sid = self._produce_transaction ('tst.accept', [contractqhash, self.wallet.getAddress ()])
			if sid != None:
				self.poll_lock.acquire ()
				self.sessionhash = sid
				self.contracthash = contractqhash
				self.state = ContractManager.STATE_PENDING
				self.poll_lock.release ()
				#logger.debug ('Fuse of contracts %s and %s broadcast done', self.contracthash, contractqhash)
				return True
			else:
				raise ContractException.ContractFuseFailedException ()


	# Blocking
	def waitUntilOnDuty (self, msecs=0):
		if self.state < ContractManager.STATE_FUSED:
			self.waitUntilSessionStart () #raise ContractException.ContractNotFusedException
		elif self.state > ContractManager.STATE_FUSED:
			raise ContractException.SessionEndedException

		while not self.isOnDuty ():
			time.sleep (ContractManager.BLOCKING_TIMEOUT)

	def waitUntilReceive (self, msecs=0):
		if self.state < ContractManager.STATE_FUSED:
			self.waitUntilSessionStart () #raise ContractException.ContractNotFusedException
		elif self.state > ContractManager.STATE_FUSED:
			raise ContractException.SessionEndedException

		while not len (self.sessionobject['state']['pending'][self.pid]) > 0:
			#print (self.sessionobject['state'])
			time.sleep (ContractManager.BLOCKING_TIMEOUT)

	def waitUntilSessionStart (self, msecs=0):
		while self.state < ContractManager.STATE_FUSED:
			time.sleep (ContractManager.BLOCKING_TIMEOUT)

		#TODO This may solve the contractnotfused bug
		time.sleep (ContractManager.BLOCKING_TIMEOUT)


	def waitUntilTelled (self, msecs=0):
		while self.state < ContractManager.STATE_PENDING_FOR_COMPLIANT:
			time.sleep (ContractManager.BLOCKING_TIMEOUT)

		#TODO This may solve the contractnotfused bug
		time.sleep (ContractManager.BLOCKING_TIMEOUT)



	# Event-based
	def setOnReceiveHandler (self, handler):
		self.onreceivehandler = handler

	def setOnDutyHandler (self, handler):
		self.ondutyhandler = handler

	def setOnSessionStartHandler (self, handler):
		self.onsessionstarthandler = handler

	def setOnPublishHandler (self, handler):
		self.oncontractpublishhandler = handler

	def setOnSessionUpdateHandler (self, handler):
		self.onsessionupdatehandler = handler
