# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from libcontractvm import Wallet, ConsensusManager, PluginManager

class BlockStoreManager (PluginManager.PluginManager):
	def __init__ (self, consensusManager, wallet = None):
		super (BlockStoreManager, self).__init__(consensusManager, wallet)

	def set (self, key, value):
		cid = self._produce_transaction ('bs.set', [key, value])
		return cid
	
	def get (self, key):
		return self.consensusManager.jsonConsensusCall ('bs.get', [key])['result']
