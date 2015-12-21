# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from pycoin.networks import *
from pycoin.key import Key
from pycoin.key.BIP32Node import BIP32Node
from pycoin import encoding
from pycoin.ecdsa import is_public_pair_valid, generator_secp256k1, public_pair_for_x, secp256k1
from pycoin.serialize import b2h, h2b
from pycoin.tx import *
from pycoin.tx.tx_utils import sign_tx, create_tx
from pycoin.tx.Spendable import Spendable
from pycoin.tx.TxOut import TxOut
from pycoin.tx.script import tools
from pycoin.encoding import bitcoin_address_to_hash160_sec, is_sec_compressed, public_pair_to_sec, secret_exponent_to_wif, public_pair_to_bitcoin_address, wif_to_tuple_of_secret_exponent_compressed, sec_to_public_pair, public_pair_to_hash160_sec, wif_to_secret_exponent
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup
import logging
import json
import requests
import binascii
import random
import time
from libcontractvm import Wallet
from . import Log
logger = logging.getLogger('libcontractvm')

class WalletExplorer (Wallet.Wallet):
	def __init__ (self, chain = 'XTN', address = None, wif = None, wallet_file = None):
		self.lockedspendables = []
		super (WalletExplorer, self).__init__ (chain, address, wif, wallet_file)


	def _chaincodeToChainSoName (self, code):
		if self.chain == 'XTN':
			code = 'BTCTEST'
		elif self.chain == 'XDT':
			code = 'DOGETEST'
		elif self.chain == 'XLT':
			code = 'LTCTEST'
		else:
			code = self.chain

		return code


	def _spendables (self, value):
		code = self._chaincodeToChainSoName (self.chain)

		u = 'https://chain.so/api/v2/get_tx_unspent/'+code+'/'+self.address
		#print (u)

		while True:
			try:
				d = requests.get (u, headers={'content-type': 'application/json'}).json()
			except:
				time.sleep (5)
				continue
			

			sps = []
			tot = 0
			random.shuffle (d['data']['txs'])
			for s in d['data']['txs']:
				#if int (s['confirmations']) > 0:
				txid = s['txid'] #''
				#for x in range (len (s['txid']), -2, -2):
				#	txid += s['txid'][x:x+2]
	
				if (txid+':'+str (s['output_no'])) in self.lockedspendables:
					#print ('Locked spendable')
					continue

				tot += int (float (s['value']) * 100000000)
				sps.append (Spendable.from_dict ({'coin_value': int (float (s['value']) * 100000000),
					'script_hex': s['script_hex'], 'tx_hash_hex': txid, 'tx_out_index': int (s['output_no'])}))

				self.lockedspendables.append (txid+':'+str (s['output_no']))

				if tot >= value:
					#print (sps)
					return sps

			return sps


	def getBalance (self):
		code = self._chaincodeToChainSoName (self.chain)

		u = 'https://chain.so/api/v2/get_address_balance/'+code+'/'+self.address

		while True:
			try:
				d = requests.get (u, headers={'content-type': 'application/json'}).json()
			except:
				time.sleep (5)
				continue

			return float (d['data']['confirmed_balance']) + float (d['data']['unconfirmed_balance'])


