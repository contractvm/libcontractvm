#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from libcontractvm import Wallet, WalletNode, HelloWorldManager, ConsensusManager
import config

consMan = ConsensusManager.ConsensusManager ()
consMan.addNode ("http://127.0.0.1:8181")
#consMan.addNode ("http://127.0.0.1:2819")
#consMan.addNode ("http://127.0.0.1:2820")

wallet=WalletNode.WalletNode (chain='XLT', url=config.WALLET_NODE_URL, wallet_file='data/test_xltnode_a.wallet')
			
helloworldMan = HelloWorldManager.HelloWorldManager (consMan, wallet=wallet)

yname = input ('Insert a name to greet: ')
helloworldMan.sendName (yname)
names = helloworldMan.getNames () 

if yname in names:
	print ("Your name has already greeted in", names[yname], "other messages")
else:
	print ("Oh cool, you're the first that said hello to", yname)
