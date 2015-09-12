#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# libcontractchain test framework
# It should be async.

import os
import sys
import time
import subprocess
from libcontractvm import Wallet, WalletChainSo, WalletNode, ContractManager, ContractException, ConsensusManager
import cvmutils


if __name__ == "__main__":
    n = 5
    chain = 'XLT'

    cvmutils.spawn (n)
    consensusManager = ConsensusManager.ConsensusManager (chain)

    for x in range (n):
        consensusManager.addNode ('http://localhost:' + str (2818 + x))

    #cm1 = ContractManager.ContractManager (consensusManager,
    #        wallet=WalletChainSo.WalletChainSo (chain=chain, wallet_file='data/test_'+chain.lower ()+'_a.wallet'))
    cm1 = ContractManager.ContractManager (consensusManager,
            wallet=WalletNode.WalletNode (chain=chain, url="http://test:testpass@localhost:18332", wallet_file='data/test_'+chain.lower ()+'node_a.wallet'))
    cm2 = ContractManager.ContractManager (consensusManager,
            wallet=WalletNode.WalletNode (chain=chain, url="http://test:testpass@localhost:18332", wallet_file='data/test_'+chain.lower ()+'node_b.wallet'))

    print ('1 Chain:', cm1.getChainCode ())
    print ('1 Address:', cm1.getWallet ().getAddress ())
    print ('1 Network time:', cm1.getTime ())
    print ('1 Balance:', cm1.getWallet ().getBalance (), cm1.getChainCode ())

    print ('Time:', cm1.getTime ())

    #for x in range (10):
    cm1.tell (cm1.translate ('!a . ?b'))
    cm1.waitUntilTelled ()
    h1 = cm1.getHash ()
    print ('Told:', cm1.getHash ())

    cm2.tell (cm1.translate ('?a . !b'))
    cm2.waitUntilTelled ()
    print ('Told:', cm2.getHash ())

    cm2.fuse (h1)
    cm1.waitUntilSessionStart ()
    cm2.waitUntilSessionStart ()

    print ('Sending !a')
    cm1.send ('a', 10)
    print ('Waiting for ?a')
    cm2.waitUntilReceive ()
    print ('Receive ?a')
    print (cm2.receive ())
    print ('Waiting until duty')
    cm2.waitUntilOnDuty ()
    print ('Sending b')
    cm2.send ('b', 12)
    print ('Waiting for ?b')
    cm1.waitUntilReceive ()
    print ('Receive ?b')
    print (cm1.receive ())
    print ('End')
