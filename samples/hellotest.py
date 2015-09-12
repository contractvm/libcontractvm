#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from libcontractvm import ConsensusManager
import sys
import config
import time

consMan = ConsensusManager.ConsensusManager ()
consMan.bootstrap ("http://127.0.0.1:2818")

consMan = ConsensusManager.ConsensusManager ()
consMan.bootstrap ("http://127.0.0.1:2819")

consMan = ConsensusManager.ConsensusManager ()
consMan.bootstrap ("http://127.0.0.1:2820")

while True:
	time.sleep (5)

