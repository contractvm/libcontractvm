from libcontractvm import Wallet, ConsensusManager, PluginManager

class HelloWorldManager (PluginManager.PluginManager):
	def __init__ (self, consensusManager, wallet = None):
		super (HelloWorldManager, self).__init__(consensusManager, wallet)
			
	def sendName (self, name):
		cid = self._produce_transaction ('hw.hello', [name])
		return cid
	
	def getNames (self):
		return self.consensusManager.jsonConsensusCall ('hw.get_names', [])['result']
