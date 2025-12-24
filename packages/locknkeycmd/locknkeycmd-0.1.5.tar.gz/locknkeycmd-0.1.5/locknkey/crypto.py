import nacl.pwhash
import nacl.secret
import nacl.utils
import nacl.encoding
import nacl.public
from nacl.public import PrivateKey, Box
import base64
from typing import Optional

class CryptoEngine:
    """
    Handles all cryptographic operations for Keyblock.
    """

    @staticmethod
    def derive_master_key(password: str, salt: bytes) -> bytes:
        """
        Derives KEK from password using Argon2id.
        Must match JS: iterations=3, memory=65536KB (64MB), parallelism=1, hashLen=32
        """
        # JS: parallelism=1 is usually handled by threading in C-impl, but libsodium default is usually 1 thread.
        # opslimit correlates to iterations/passes.
        # memlimit is in bytes.

        OPSLIMIT = 3
        MEMLIMIT = 67108864 # 64 MB

        return nacl.pwhash.argon2id.kdf(
            32,
            password.encode('utf-8'),
            salt,
            opslimit=OPSLIMIT, 
            memlimit=MEMLIMIT
        )

    @staticmethod
    def decrypt_private_key(encrypted_b64: str, nonce_b64: str, master_key: bytes) -> Optional[PrivateKey]:
        try:
            ciphertext = base64.b64decode(encrypted_b64)
            nonce = base64.b64decode(nonce_b64)
            
            # XSalsa20-Poly1305 decryption
            box = nacl.secret.SecretBox(master_key)
            decrypted = box.decrypt(ciphertext, nonce=nonce)
            
            return PrivateKey(decrypted)
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None

    @staticmethod
    def decrypt_project_key(encrypted_key_b64: str, nonce_b64: str, sender_pub_b64: str, user_private_key: PrivateKey) -> bytes:
        """
        Decrypts a project key using the user's private key and the sender's public key.
        """
        ciphertext = base64.b64decode(encrypted_key_b64)
        nonce = base64.b64decode(nonce_b64)
        sender_pub = nacl.public.PublicKey(base64.b64decode(sender_pub_b64))
        
        # Create Box
        box = Box(user_private_key, sender_pub)
        return box.decrypt(ciphertext, nonce=nonce)
    
    @staticmethod
    def decrypt_secret(ciphertext_b64: str, nonce_b64: str, project_key: bytes) -> bytes:
        """
        Decrypts a symmetric secret.
        """
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        
        box = nacl.secret.SecretBox(project_key)
        return box.decrypt(ciphertext, nonce=nonce)

    @staticmethod
    def decode_b64(val: str) -> bytes:
        return base64.b64decode(val)
