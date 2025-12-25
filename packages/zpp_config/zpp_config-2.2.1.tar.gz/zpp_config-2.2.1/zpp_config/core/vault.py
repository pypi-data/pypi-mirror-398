import os
import __main__
import zpp_store

class Vault:
	def __init__(self, vault_file, password=None, keyfile=None):
		if keyfile:
			if os.path.exists(keyfile):
				with open(keyfile, "r") as f:
					password = f.read().strip('\n')

		if not password:
			password = zpp_store.secure_input("password vault: ")

		self.vault = zpp_store.Store(filename=vault_file, format= zpp_store.Formatstore.to_binary, protected=True, password=password)


	def set_key(self, component, value=None):
		try:
			if not value:
				value = zpp_store.secure_input("key: ")

			self.vault.push(component, value)
			return True
		except:
			return False


	def get_key(self, component=None):
		try:
			return self.vault.pull(component)
		except:
			return ""


	def unset_key(self, component=None):
		try:
			self.vault.erase(component)
			return True
		except:
			return False


	def get_list(self):
		return self.vault.list()
