# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import sys
import signal
import logging
import json
import requests
import time
import threading
import copy
from threading import Thread, Timer, Lock
from queue import Queue
from random import shuffle

from . import Log

logger = logging.getLogger('libcontractvm')


POLICY_ONLY_NEGATIVE = 0
POLICY_BOTH = 1
POLICY_NONE = 2

BOOTSTRAP_TIMER = 20


class ConsensusManager:
	def __init__ (self, chain = 'XTN', policy = POLICY_BOTH):
		self.chain = chain
		self.nodes = {}
		self.policy = policy
		self.bootmer = Timer (BOOTSTRAP_TIMER, self.bootstrapSched)
		self.bootmer.start ()
		self.nodeslock = Lock ()

	# Return a list
	def getNodes (self):
		return self.nodes

	# Return the used chain
	def getChain (self):
		return self.chain


	# Bootstrap from a node
	def bootstrap (self, node):
		self.addNode (node, bootstrap=False)

		logger.debug ('Bootstrap from ' + node + '...')
		c = self.jsonCall (node, 'net.peers')
		if c != None:
			#print (c)
			for nn in c:
				if nn['info'] != None:
					self.addNode ('http://'+nn['host']+':'+str(nn['info']))


	def bootstrapSched (self):
		self.nodeslock.acquire ()
		nodes = copy.deepcopy (self.nodes)
		self.nodeslock.release ()

		for node in nodes:
			self.bootstrap (node)

		self.bootmer = Timer (BOOTSTRAP_TIMER, self.bootstrapSched)
		self.bootmer.start ()

	# Add a new node
	def addNode (self, node, bootstrap=True):
		self.nodeslock.acquire ()
		#print (self.nodes)
		if node in self.nodes:
			#	logger.warning ('Duplicated node')
			self.nodeslock.release ()
			return False

		c = self.jsonCall (node, 'info')

		if c == None:
			#logger.error ('Unreachable node ' + node)
			self.nodeslock.release ()
			return False

		if c['chain']['code'] != self.chain:
			logger.error ('Different chain between node and client ' + node)
			self.nodeslock.release ()
			return False

		self.nodes[node] = { 'reputation': 1.0, 'calls': 0 }
		logger.info ('New node found: ' + node)
		self.nodeslock.release ()
		self.bootstrap (node)

		return True

	def getBestNode (self):
		#print (self.nodes.items())
		dictlist = []
		for key, value in self.nodes.items():
			temp = [key,value]
			dictlist.append(temp)

		shuffle (dictlist)
		ordered_nodes = sorted (dictlist, key=lambda node: node[1]['reputation'])
		return ordered_nodes [0][0]



	# Perform a call with consensus algorithm
	def jsonConsensusCall (self, command, args = []):
		res = self.jsonCallFromAll (command, args)

		#print (res)
		# Group by result
		resgroups = {}

		for x in res:
			resst = json.dumps (x['result'], sort_keys=True, separators=(',',':'))
			if resst in resgroups:
				resgroups[resst]['score'] += self.nodes[x['node']]['reputation']
				resgroups[resst]['nodes'].append(x['node'])
			else:
				resgroups[resst] = {'result': x['result'], 'score': self.nodes[x['node']]['reputation'], 'nodes': [x['node']]}

		# Select best score
		max = None
		for x in resgroups:
			if max == None:
				max = x
			elif resgroups[max]['score'] < resgroups[x]['score']:
				max = x

		for x in resgroups:
			# Increase reputation for good results (Positive Feedback)
			if self.policy == POLICY_BOTH and resgroups[x]['score'] >= resgroups[max]['score']:
				for node in resgroups[x]['nodes']:
					self.nodes[node]['reputation'] *= 1.2

					if self.nodes[node]['reputation'] > 1.0:
						self.nodes[node]['reputation'] = 1.0

			# Decrease reputation for wrong results (Negative Feedback)
			if self.policy != POLICY_NONE and resgroups[x]['score'] < resgroups[max]['score']:
				for node in resgroups[x]['nodes']:
					self.nodes[node]['reputation'] /= 1.2

					if self.nodes[node]['reputation'] < 0.1:
						logger.debug ("Removing node %s because of low reputation", node)
						del self.nodes[node]

		logger.debug ("Found consensus majority with score %f of %d nodes", resgroups[max]['score'], len (resgroups[max]['nodes']))
		if len (resgroups) == None:
			return None

		return resgroups[max]


	def jsonCallFromAll (self, command, args = []):
		# Perform the call in parallel
		q = Queue ()
		threads = []

		for node in self.nodes:
			self.nodes[node]['calls'] += 1
			t = Thread(target=self.jsonCall, args=(node, command, args, q))
			t.start()
			threads.append(t)

		for t in threads:
			t.join(4.0)

		res = []
		while not q.empty ():
			res.append (q.get ())

		return res

	# Perform a call with a node
	def jsonCall (self, node, command, args = [], queue = None):
		try:
			payload = {
				"method": command,
				"params": args,
				"jsonrpc": "2.0",
				"id": 0,
			}
			d = requests.post(node, data=json.dumps(payload), headers={'content-type': 'application/json'}).json()

			#print (command, args, d)
			if queue != None:
				queue.put ({'node': node, 'result': d['result']})
			else:
				return d['result']
		except:
			#logger.error ('Failed to contact the node '+node)
			if queue == None:
				return None
