import impmagic

@impmagic.loader(
	{'module':'zpp_config.core.logs', 'submodule': ['print_nxs']}
)
def help():
	#print_nxs("    ________             \n   / ____/ /___ _      __\n  / /_  / / __ \\ | /| / /\n / __/ / / /_/ / |/ |/ / \n/_/   /_/\\____/|__/|__/  \n                         \n")

	helper= {
		"vault": "Gestion d'un vault",
		"vault_encryption": "Chiffrement de clé",
	}

	for el, le in helper.items():
		print_nxs(f"{el}: ", color='yellow', nojump=True)
		print_nxs(le, color='dark_gray')
	print("")


@impmagic.loader(
	{'module':'zpp_config.core.vault', 'submodule': ['Vault']},
	{'module':'zpp_config.core.logs', 'submodule': ['logs', 'print_tree']},
	{'module':'zpp_args'},
	{'module':'zpp_store'},
	{'module':'sys'},
)
def vault_cli():
	parse = zpp_args.parser(sys.argv[1:])
	parse.command = "zpp_config vault"
	parse.set_description("Gestion d'un vault")
	parse.set_argument("s", "set", description="Initialisation d'un mot de passe", default=None, store="value")
	parse.set_argument("u", "unset", description="Suppression d'un mot de passe", default=None, store="value")
	parse.set_argument("g", "get", description="Récupération d'un mot de passe", default=None, store="value")
	parse.set_argument("l", "list", description="Liste des clés disponibles", default=False)
	parse.set_argument("t", "tree", description="Liste des clés disponibles", default=False)
	parse.set_argument("V", "vault", description="Spécifier le fichier vault", default=False, store="value")
	parse.set_argument("K", "keyfile", description="Spécifier le keyfile contenant le mot de passe du vault", default=None, store="value")
	parse.disable_check()
	parameter, argument = parse.load()

	if parameter!=None:
		if argument.vault:
			if argument.set:
				v = Vault(argument.vault, keyfile=argument.keyfile)
				status_code = v.set_key(argument.set, parameter[0])
				if status_code:
					logs("Clé enregistrée", "success")
				else:
					logs("Erreur lors de l'enregistrement de la clé", "error")

			elif argument.get:
				v = Vault(argument.vault, keyfile=argument.keyfile)
				result = v.get_key(argument.get)
				print(result)

			elif argument.unset:
				v = Vault(argument.vault, keyfile=argument.keyfile)
				status_code = v.unset_key(argument.unset)
				if status_code:
					logs("Clé supprimée", "success")
				else:
					logs("Erreur lors de la suppression de la clé", "error")

			elif argument.list:
				v = Vault(argument.vault, keyfile=argument.keyfile)
				for element in v.get_list():
					print(f"- {element}")


			elif argument.tree:
				v = Vault(argument.vault, keyfile=argument.keyfile)
				result = v.get_key()
				if result:
					print_tree(result)

		else:
			logs("Aucun fichier vault spécifié", "error")



@impmagic.loader(
	{'module':'os'},
	{'module':'zpp_store'},
)
def get_password(argument):
	password = None

	if argument.password:
		password = argument.password

	if argument.keyfile:
		if os.path.exists(argument.keyfile):
			with open(argument.keyfile, "r") as f:
				password = f.read().strip('\n')

	if not password:
		password = zpp_store.secure_input("password vault: ")

	return password


@impmagic.loader(
	{'module':'zpp_config.core.vault_encryption', 'submodule': ['vault_encrypt', 'vault_decrypt']},
	{'module':'zpp_args'},
	{'module':'sys'},
)
def vault_encryption():
	parse = zpp_args.parser(sys.argv[1:])
	parse.command = "zpp_config vault_encryption"
	parse.set_description("Chiffrement de clé")
	parse.set_argument("e", "encrypt", description="Chiffrement d'une clé", default=None, store="value")
	parse.set_argument("d", "decrypt", description="Déchiffrement d'une clé", default=None, store="value")
	parse.set_argument("p", "password", description="Spécifier le mot de passe de chiffrement", default=False, store="value")
	parse.set_argument("K", "keyfile", description="Spécifier le keyfile contenant le mot de passe de chiffrement", default=None, store="value")
	parse.disable_check()
	parameter, argument = parse.load()

	if parameter!=None:
		if argument.encrypt:
			password = get_password(argument)

			result = vault_encrypt(argument.encrypt, password)
			print(result)

		elif argument.decrypt:
			password = get_password(argument)
			
			result = vault_decrypt(argument.decrypt, password)
			print(result)


@impmagic.loader(
	{'module':'sys'},
)
def cli():
	if len(sys.argv)>1:
		match sys.argv[1]:
			case "vault":
				vault()
			case "vault_encryption":
				vault_encryption()
			case _:
				help()
	else:
		help()
