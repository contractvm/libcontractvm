from libcontractvm import Wallet, WalletNode, FIFOManager, ConsensusManager
import config

consMan = ConsensusManager.ConsensusManager ()
consMan.addNode ("http://127.0.0.1:2818")
consMan.addNode ("http://127.0.0.1:2819")
consMan.addNode ("http://127.0.0.1:2820")

wallet=WalletNode.WalletNode (chain='XLT', url=config.WALLET_NODE_URL, wallet_file='data/test_xltnode_a.wallet')
			
fifoMan = FIFOManager.FIFOManager (consMan, wallet=wallet)

body = input ('Insert a body for the message: ')
fifoMan.publish ('helloqueue', body)
print ('Done.')
