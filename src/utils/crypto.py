# Conteúdo movido de src/crypto_utils.py
from __future__ import annotations
import ast
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def _b64url_decode(data: str) -> bytes:
	data = data.replace("-", "+").replace("_", "/")
	missing = (-len(data)) % 4
	if missing:
		data += "=" * missing
	return base64.b64decode(data)

def decrypt(token: str) -> str:
	if '.' not in token:
		return token
	encoded_encrypted_data, encoded_private_key = token.split(".", 1)
	combined = _b64url_decode(encoded_encrypted_data)
	private_key_bytes = _b64url_decode(encoded_private_key)
	encrypted_key = combined[:256]
	iv = combined[256:272]
	encrypted_content = combined[272:]
	private_key_obj = serialization.load_der_private_key(private_key_bytes, password=None)
	if not isinstance(private_key_obj, rsa.RSAPrivateKey):
		raise ValueError("Expected RSA private key, got different key type")
	private_key: rsa.RSAPrivateKey = private_key_obj
	aes_key = private_key.decrypt(
		encrypted_key,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA1()),
			algorithm=hashes.SHA1(),
			label=None,
		),
	)
	cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
	decryptor = cipher.decryptor()
	padded_plain = decryptor.update(encrypted_content) + decryptor.finalize()
	def _unpad_pkcs7(data: bytes) -> bytes:
		if not data:
			return data
		pad = data[-1]
		if pad < 1 or pad > 16 or data[-pad:] != bytes([pad]) * pad:
			return data
		return data[:-pad]
	plaintext_bytes = _unpad_pkcs7(padded_plain)
	final_value = plaintext_bytes.decode("utf-8")
	try:
		return str(ast.literal_eval(final_value)['org_id'])
	except (ValueError, SyntaxError, KeyError):
		return ''

from hashids import Hashids
hashids = Hashids(salt="minha-chave-secreta-dashboard-2024", min_length=8)
def encode_id(real_id: int) -> str:
	return hashids.encode(real_id)
def decode_id(encoded_id: str) -> int:
	decoded = hashids.decode(encoded_id)
	return decoded[0] if decoded else 0
# moved from src/crypto_utils.py
