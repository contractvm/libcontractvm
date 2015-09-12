# Copyright (c) 2015 Davide Gessa
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

class ContractException (Exception):
	def __init__ (self, code, message):
		self.code = code
		self.message = message
	

class ContractNotPresentException (Exception):
	pass


class SessionEndedException (Exception):
	pass

class ContractNotFusedException (Exception):
	pass


class ContractFuseFailedException (Exception):
	pass


class ContractAlreadyFusedException (Exception):
	pass


class ContractTellFailedException (Exception):
	pass


class WalletUndefinedException (Exception):
	pass


class RPCConnectException (Exception):
	pass
