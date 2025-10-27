# Conteúdo movido de generate_test_token.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar token de teste com org_id especifico
"""

import base64
import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def _b64url_encode(data: bytes) -> str:
	return base64.b64encode(data).decode('utf-8').replace('+', '-').replace('/', '_').rstrip('=')

def generate_token(org_id: int) -> str:
	# 1. Criar chave privada RSA
	private_key = rsa.generate_private_key(
		public_exponent=65537,
		key_size=2048,
		backend=default_backend()
	)
	# 2. Serializar chave privada (PKCS#8 DER)
	private_key_bytes = private_key.private_bytes(
		encoding=serialization.Encoding.DER,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.NoEncryption()
	)
	# 3. Criar dados do payload
	payload_data = {"org_id": org_id}
	payload_str = str(payload_data)
	payload_bytes = payload_str.encode('utf-8')
	# 4. Aplicar padding PKCS#7 para AES-CBC (16 bytes blocks)
	def _pad_pkcs7(data: bytes) -> bytes:
		pad_len = 16 - (len(data) % 16)
		return data + bytes([pad_len]) * pad_len
	padded_payload = _pad_pkcs7(payload_bytes)
	# 5. Gerar chave AES aleatória (32 bytes = 256 bits)
	aes_key = os.urandom(32)
	# 6. Gerar IV aleatório (16 bytes)
	iv = os.urandom(16)
	# 7. Criptografar payload com AES-256-CBC
	cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
	encryptor = cipher.encryptor()
	encrypted_content = encryptor.update(padded_payload) + encryptor.finalize()
	# 8. Criptografar chave AES com RSA-OAEP(SHA-1)
	public_key = private_key.public_key()
	encrypted_aes_key = public_key.encrypt(
		aes_key,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA1()),
			algorithm=hashes.SHA1(),
			label=None
		)
	)
	# 9. Combinar: [encrypted_key(256b)] + [iv(16b)] + [encrypted_content]
	combined = encrypted_aes_key + iv + encrypted_content
	# 10. Encode em base64url
	encoded_encrypted_data = _b64url_encode(combined)
	encoded_private_key = _b64url_encode(private_key_bytes)
	# 11. Criar token final: "<encrypted_data>.<private_key>"
	token = f"{encoded_encrypted_data}.{encoded_private_key}"
	return token

if __name__ == "__main__":
	org_id = 17881
	token = generate_token(org_id)
	print(f"Token gerado para org_id {org_id}:")
	print(token)
	print("\nURL de teste:")
	print(f"https://dashboard.e-inscricao.tech/?t={token}")
	from src.utils.crypto import decrypt
	try:
		decrypted_org_id = decrypt(token)
		print(f"\nVerificação: token descriptografado retorna org_id = {decrypted_org_id}")
		if decrypted_org_id == str(org_id):
			print("✅ Token válido!")
		else:
			print("❌ Erro na verificação")
	except Exception as e:
		print(f"❌ Erro na verificação: {e}")
# moved from generate_test_token.py
