#!/usr/bin/python3
# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Simulation 2: malicious nodes / interaction / avg error rate
# Per ogni iterazione, misurare l'errore medio attuale ed il numero di nodi malevoli
# I risultati sono tutti zero, l'errore inizia ad aumentare per k=9
import os
import sys
import time
import subprocess
from libcontractvm import Wallet, WalletChainSo, ContractManager, ContractException, ConsensusManager
import cvmutils
import threading
from threading import Lock, Thread
from queue import Queue

if __name__ == "__main__":
    f1 = open ('/home/dak/result_2_both.csv', 'w')
    f2 = open ('/home/dak/result_2_oneg.csv', 'w')


    cvmutils.spawn (20, 10, delay = 0)

    for k in range (8,11):
        for policy in [ConsensusManager.POLICY_BOTH, ConsensusManager.POLICY_ONLY_NEGATIVE]:
            cms = []
            for j in range (10):
                consensusManager = ConsensusManager.ConsensusManager ('XLT', policy)
                for x in range (10):
                    if x >= 10-k:
                        consensusManager.addNode ('http://localhost:' + str (2818 + 10 + x))
                    else:
                        consensusManager.addNode ('http://localhost:' + str (2818 + x))
                cms.append ([consensusManager, 0])

            for it in range (1,101):
                erate = []
                for cm in cms:
                    v = cm[0].jsonConsensusCall ('consensus_test', [it])

                    if (v):
                        print (v['result']['value'], it)
                        if v['result']['value'] != it:
                            cm[1] += 1
                    erate.append (cm[1] / it)

                avg_erate = 0.0
                for rate in erate:
                    avg_erate += rate
                avg_erate /= len (erate)

                if policy == ConsensusManager.POLICY_BOTH:
                    f1.write (str(k)+'\t'+str(it)+'\t'+str(avg_erate)+'\n')
                    f1.flush ()
                else:
                    f2.write (str(k)+'\t'+str(it)+'\t'+str(avg_erate)+'\n')
                    f2.flush ()

    f1.close ()
    f2.close ()
