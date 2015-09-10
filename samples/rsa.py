#!/usr/bin/python3
# RSA cracking example
import config
import os
import sys
import time
import subprocess
from libcontractvm import Wallet, WalletChainSo, WalletNode, ContractManager, ContractException, ConsensusManager
import cvmutils


if __name__ == "__main__" and len (sys.argv) == 2:
    player = sys.argv[1].lower ()

    if player == 'spawn':
        cvmutils.spawn (3)
        while True:
            time.sleep (5)
        sys.exit ()
        
    consensusManager = ConsensusManager.ConsensusManager ('XLT')

    for x in range (3):
        consensusManager.addNode ('http://localhost:' + str (2818 + x))

    if player.find ('slave') != -1:
        wallet = WalletNode.WalletNode (chain='XLT', url=config.WALLET_NODE_URL, wallet_file='data/test_xltnode_a.wallet')
    else:
        wallet = WalletNode.WalletNode (chain='XLT', url=config.WALLET_NODE_URL, wallet_file='data/test_xltnode_b.wallet')
        
    cm = ContractManager.ContractManager (consensusManager, wallet=wallet)
    
    print (player, 'Chain:', cm.getChainCode ())
    print (player, 'Address:', cm.getWallet ().getAddress ())
    print (player, 'Network time:', cm.getTime ())
    print (player, 'Balance:', cm.getWallet ().getBalance (), cm.getChainCode ())
    print (player, 'Time:', cm.getTime ())


    if player == 'honestslave':
        cm.tell (cm.translate ('?publickey{;x}.(!confirm{x<15}.!result{x<90}.?pay{x<120} + !abort{x<15})'))
    elif player == 'inefficientslave':
        cm.tell (cm.translate ('?publickey{;x}.(!confirm{x<20}.!result{x<100}.?pay{x<130} + !abort{x<20})'))
    else:
        cm.tell (cm.translate ('!publickey{;x}.(?confirm{x<20}.?result{x<100}.!pay{x<130} & ?abort{x<20})'))

    cm.waitUntilTelled ()
    print ('Telled:', cm.getHash ())

    cm.waitUntilSessionStart ()

    if player == 'inefficientslave':
        pass
    elif player == 'honestslave':
        pass
    elif player == 'master':
        pass

elif __name__ == "__main__":
    print ('usage: python3',sys.argv[0],'[spawn|inefficientslave|honestslave|master]')
