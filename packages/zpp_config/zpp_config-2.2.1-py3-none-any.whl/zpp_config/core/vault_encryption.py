import os
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad

def vault_encrypt(plaintext: str, password: str) -> str:
    """
    Chiffre un texte (AES256) et retourne en hex.
    """
    # 1️. Génération d'un sel aléatoire (16 bytes)
    salt = os.urandom(16)

    # 2️. Génération de la clé AES via PBKDF2-HMAC-SHA256
    # utilise 10000 itérations pour PBKDF2
    key = PBKDF2(password, salt, dkLen=32, count=10000)

    # 3️. IV aléatoire pour AES CBC
    iv = os.urandom(16)

    # 4. Chiffrement AES256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))

    # 5️. Retourne hex : sel + IV + contenu chiffré
    return (salt + iv + ciphertext).hex()


def vault_decrypt(hex_data: str, password: str) -> str:
    """
    Déchiffre un flux chiffré (AES256).
    hex_data : sel + IV + ciphertext en hex
    """
    data = bytes.fromhex(hex_data)

    # 1️. On extrait le sel, l'IV et le ciphertext
    salt = data[:16]
    iv = data[16:32]
    ciphertext = data[32:]

    # 2️. Recréation de la clé via PBKDF2-HMAC-SHA256
    key = PBKDF2(password, salt, dkLen=32, count=10000)

    # 3️. Déchiffrement AES256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext_padded = cipher.decrypt(ciphertext)

    # 4️. Dépadding PKCS7
    plaintext = unpad(plaintext_padded, AES.block_size)

    return plaintext.decode()
