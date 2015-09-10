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
