#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from threading import Thread
from libcontractvm import Wallet, WalletChainSo, FIFOManager, ConsensusManager
import config
import random
import time

consMan = ConsensusManager.ConsensusManager ()
consMan.addNode ("http://127.0.0.1:2818")
consMan.addNode ("http://127.0.0.1:2819")
consMan.addNode ("http://127.0.0.1:2820")

wallet=WalletChainSo.WalletChainSo (chain='XLT', wallet_file='data/test_xltnode_b.wallet')
			


def consumer ():
	fifoMan = FIFOManager.FIFOManager (consMan, wallet=wallet)
	def consume (queue, body):
		print ('[x] Received:', body)


	fifoMan.consume ('helloqueue', consume)
	fifoMan.startConsumer ()
	

def producer ():
	while True:
		fifoMan = FIFOManager.FIFOManager (consMan, wallet=wallet)
		body = str (int (random.random () * 10000000000000000000))
		fifoMan.publish ('helloqueue', body)
		print ('[x] Sent:', body)
		time.sleep (1)

		
t = Thread(target=consumer, args=())
t.start()

for x in range (5):
	t = Thread(target=producer, args=())
	t.start()
