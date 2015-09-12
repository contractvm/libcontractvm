# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import os
import subprocess
import time

def spawnCVMD (n, port, apiport, chain, datapath, params = [], delay = 5):
    #"xterm", "-rv", "-e",
    #"urxvt", "-e", 
    pid = subprocess.Popen(["xterm", "-rv", "-e", "contractvmd", "--discard-old-blocks", "--api-port="+str(apiport),
                    "--port="+str(port), "--chain="+chain, "--data="+datapath] + params,
                    stderr=subprocess.STDOUT).pid #, stdout=subprocess.PIPE
    time.sleep (delay)
    print ('Started client',n,'with pid', pid)
    return pid


# n = nodi
# k = nodi farlocchisti
def spawn (n, k = 0, delay = 5):
    os.system ('killall contractvmd')
    os.system ('rm -r /tmp/cvmd*')
    time.sleep (2)

    prev = None
    for x in range (n):
        args = []
        if prev != None:
            args.append ('--seed=localhost:'+str(prev))
        if x >= n-k:
            args.append ('--malicious')

        spawnCVMD (x, 1818 + x, 2818 + x, 'XLT', '/tmp/cvmd'+str(x), args, delay)
        prev = 1818+x

    time.sleep (15)
