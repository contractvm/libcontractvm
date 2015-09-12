#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from libcontractvm import Wallet, WalletNode, FIFOManager, ConsensusManager
import config

consMan = ConsensusManager.ConsensusManager ()
consMan.addNode ("http://127.0.0.1:2818")
consMan.addNode ("http://127.0.0.1:2819")
consMan.addNode ("http://127.0.0.1:2820")

wallet=WalletNode.WalletNode (chain='XLT', url=config.WALLET_NODE_URL, wallet_file='data/test_xltnode_a.wallet')
			
fifoMan = FIFOManager.FIFOManager (consMan, wallet=wallet)

def consume (queue, body):
	print ('[x] Received:', body)


fifoMan.consume ('helloqueue', consume)
fifoMan.startConsumer ()

