from __future__ import annotations
import ast
import base64

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def _b64url_decode(data: str) -> bytes:
    """
    Decodifica Base64 URL-safe (substituições -/_ e padding opcional).
    Equivalente ao replace + atob do JS.
    """
    # Converte para base64 "normal" e corrige padding
    data = data.replace("-", "+").replace("_", "/")
    # adiciona '=' para múltiplos de 4
    missing = (-len(data)) % 4
    if missing:
        data += "=" * missing
    return base64.b64decode(data)


def decrypt(token: str) -> str:
    """
    Replica o comportamento do código JS:
    - token = "<encodedEncryptedData>.<encodedPrivateKeyData>"
    - encodedEncryptedData (b64url) = [RSA_AES_KEY(256b)] [IV(16b)] [AES_CIPHERTEXT(resto)]
    - encodedPrivateKeyData (b64url) = chave privada RSA em PKCS#8 DER (sem senha)

    Retorna o plaintext (UTF-8).
    """

    encoded_encrypted_data, encoded_private_key = token.split(".", 1)

    combined = _b64url_decode(encoded_encrypted_data)
    private_key_bytes = _b64url_decode(encoded_private_key)

    # Particiona os componentes (mesmos offsets do JS)
    encrypted_key = combined[:256]       # 256 bytes: chave AES criptografada com RSA
    iv = combined[256:272]               # 16 bytes: IV do AES-CBC
    encrypted_content = combined[272:]   # restante: conteúdo cifrado em AES-CBC

    # Importa chave privada RSA (PKCS#8 DER, sem senha)
    private_key_obj = serialization.load_der_private_key(
        private_key_bytes,
        password=None,
    )
    
    # Type check to ensure we have an RSA private key
    # Should never happen at all, but mypy needs this
    if not isinstance(private_key_obj, rsa.RSAPrivateKey):
        raise ValueError("Expected RSA private key, got different key type")
    
    private_key: rsa.RSAPrivateKey = private_key_obj

    # Descriptografa a chave AES com RSA-OAEP(SHA-1)
    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )

    # Descriptografa o conteúdo com AES-256-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(encrypted_content) + decryptor.finalize()

    # AES-CBC não define padding por si: normalmente é PKCS#7.
    # O WebCrypto 'AES-CBC' não remove padding automaticamente; se seu produtor
    # aplicou PKCS#7, removemos abaixo. Caso contrário, remova esta etapa.
    def _unpad_pkcs7(data: bytes) -> bytes:
        if not data:
            return data
        pad = data[-1]
        if pad < 1 or pad > 16 or data[-pad:] != bytes([pad]) * pad:
            # Se não parecer PKCS#7, devolve como está
            return data
        return data[:-pad]

    plaintext_bytes = _unpad_pkcs7(padded_plain)

    final_value = plaintext_bytes.decode("utf-8")
    
    try:
        return str(ast.literal_eval(final_value)['org_id'])
    except (ValueError, SyntaxError, KeyError):
        return ''