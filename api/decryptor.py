import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class ManagerDecrypt:
    def __init__(self):
        self.keys = [
            "mS9wR2qY7pK7vX5n",
            "fV3gK5vU7uG6hU5e",
            "oU0dI2lL2tK2dR9f",
        ]

        # Configuração baseada no script original
        self.config = {
            "sigBytes": 32,
            "words": [
                1884436332, 1295477057, 929846578, 1867920227,
                1144552015, 878792752, 1917597540, 1211458376
            ],
        }

    @staticmethod
    def reverse(value: str) -> str:
        """
        Reverte uma string.
        """
        return value[::-1]

    def decrypt_jwt(self, token: str) -> str:
        """
        Decifra um token JWT usando a lógica migrada do TypeScript.
        """
        try:
            # Extrai os últimos 64 caracteres como IV
            iv = token[-64:]
            iv_reversed = self.reverse(iv)

            # Ajusta o IV para os primeiros 16 bytes (128 bits)
            iv_bytes = iv_reversed.encode('utf-8')[:16]

            # Extrai o payload criptografado do token
            encrypted_payload = token[36:-64]
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_payload + '==')

            # Simula a chave (usando os "words" do config como base para gerar uma chave)
            key_bytes = b''.join(w.to_bytes(4, 'big') for w in self.config["words"])

            # Decifra usando AES com CBC
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            return f"Failed to decrypt: {e}"
