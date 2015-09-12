# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
import cvmutils

if __name__ == "__main__":
    cvmutils.spawn (3)
    while True:
        time.sleep (5)
    sys.exit ()
        
