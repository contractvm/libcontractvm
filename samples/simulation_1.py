#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Simulation 1: avg error / number of malicious node con probabilita' di consenso fissata
# provare con le tre politiche
import os
import sys
import time
import subprocess
from libcontractvm import Wallet, WalletExplorer, ContractManager, ContractException, ConsensusManager
import cvmutils
import threading
from threading import Lock, Thread
from queue import Queue

# n = nodi
# t = numero di call
def test (n, t, policy):
    consensusManager = ConsensusManager.ConsensusManager ('XLT', policy)

    for x in range (n):
        consensusManager.addNode ('http://localhost:' + str (2818 + x))

    errors = 0
    valids = 0
    for x in range (t):
        v = consensusManager.jsonConsensusCall ('consensus_test', [x])

        if (v):
            if v['result']['value'] != x:
                errors += 1
            else:
                valids += 1

    return {'errors': errors, 'valids': valids, 'tests': t}
    #cm1 = ContractManager.ContractManager (consensusManager,
    #        wallet=WalletChainSo.WalletChainSo (chain=chain.upper (), wallet_file='data/test_xlt_a.wallet'))


def teststep (q, t, policy):
    r = test (10, t, policy)
    err_rate = r['errors'] / r['tests']
    q.put (err_rate)


if __name__ == "__main__":
    f = open ('/home/dak/result.csv', 'w')
    res_tot = {}

    for policy in [ConsensusManager.POLICY_NONE, ConsensusManager.POLICY_BOTH, ConsensusManager.POLICY_ONLY_NEGATIVE]:
        for k in range (5,9):
            results = {}

            cvmutils.spawn (10, k, delay = 0)

            erate = []

            print ('Malicious:',k)
            time.sleep (1)

            q = Queue ()
            threads = []

            for x in range (10):
                t = Thread(target=teststep, args=(q, 100, policy))
                t.start()
                threads.append(t)

            for t in threads:
                t.join(4.0)

            while not q.empty ():
                erate.append (q.get ())

            avg_erate = 0.0
            for y in erate:
                avg_erate += y
            avg_erate /= len (erate)
            print ('Average error rate:',avg_erate)

            #f.write (str(k)+'\t'+str(g)+'\t'+str(avg_erate)+'\n')
            f.write (str(policy)+'\t'+str(k)+'\t'+str(avg_erate)+'\n')
            f.flush ()

            res_tot[k] = avg_erate
            print (res_tot)
            time.sleep (10)

    f.close ()
