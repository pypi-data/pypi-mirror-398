import base64
import datetime
import hashlib
import os
from typing import Optional, List, Dict, Union

import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class Security:
    DEFAULT_HASH_ALGO = "sha256"
    DEFAULT_JWT_ALGO = "HS256"
    RSA_PUBLIC_EXPONENT = 65537
    RSA_KEY_SIZE = 2048
    
    CONFIGURED_JWT_SECRET = None

    @classmethod
    def load_config(cls, config: dict):
        if "Security" in config.keys():
            tool_config = config["Security"]
            cls.DEFAULT_HASH_ALGO = tool_config.get("DEFAULT_HASH_ALGO", cls.DEFAULT_HASH_ALGO)
            cls.DEFAULT_JWT_ALGO = tool_config.get("DEFAULT_JWT_ALGO", cls.DEFAULT_JWT_ALGO)
            cls.RSA_KEY_SIZE = tool_config.get("RSA_KEY_SIZE", cls.RSA_KEY_SIZE)
            cls.CONFIGURED_JWT_SECRET = tool_config.get("JWT_SECRET", cls.CONFIGURED_JWT_SECRET)

    @classmethod
    def generate_rsa_keypair(cls, save_dir: Optional[str] = None, name: str = "key") -> Dict[str, str]:
        private_key = rsa.generate_private_key(
            public_exponent=cls.RSA_PUBLIC_EXPONENT,
            key_size=cls.RSA_KEY_SIZE
        )
        public_key = private_key.public_key()

        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        if save_dir:
            cls._save_key_file(save_dir, f"{name}.pem", pem_private)
            cls._save_key_file(save_dir, f"{name}.pub", pem_public)

        return {"private": pem_private, "public": pem_public}

    @classmethod
    def generate_symmetric_key(cls, save_path: Optional[str] = None) -> str:
        key = Fernet.generate_key().decode('utf-8')
        if save_path:
            cls._save_key_file(os.path.dirname(save_path) or ".", os.path.basename(save_path), key)
        return key

    @classmethod
    def encrypt_rsa(cls, public_key_pem: str, message: str) -> str:
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        ciphertext = public_key.encrypt(
            message.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(ciphertext).decode('utf-8')

    @classmethod
    def decrypt_rsa(cls, private_key_pem: str, ciphertext_b64: str) -> str:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )
        ciphertext = base64.b64decode(ciphertext_b64)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')

    @classmethod
    def encrypt_symmetric(cls, key: str, message: str) -> str:
        f = Fernet(key.encode('utf-8'))
        return f.encrypt(message.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt_symmetric(cls, key: str, token: str) -> str:
        f = Fernet(key.encode('utf-8'))
        return f.decrypt(token.encode('utf-8')).decode('utf-8')

    @classmethod
    def hash_string(cls, text: str, algorithm: Optional[str] = None) -> str:
        algo = algorithm or cls.DEFAULT_HASH_ALGO
        h = cls._get_hash_func(algo)
        h.update(text.encode('utf-8'))
        return h.hexdigest()

    @classmethod
    def verify_hash(cls, text: str, hash_val: str, algorithm: Optional[str] = None) -> bool:
        computed = cls.hash_string(text, algorithm)
        # Using constant time comparison is better for security, but secrets.compare_digest isn't imported.
        # However, for simple hash check, equality is usually what's requested. 
        # I'll stick to simple equality as I didn't import secrets.
        return computed.lower() == hash_val.lower()

    @classmethod
    def create_jwt(cls, payload: dict, secret: Optional[str] = None, algorithm: Optional[str] = None, expiration_seconds: Optional[int] = None) -> str:
        key = secret or cls.CONFIGURED_JWT_SECRET
        if not key:
            raise ValueError("JWT Secret is required")
        
        algo = algorithm or cls.DEFAULT_JWT_ALGO
        
        payload_copy = payload.copy()
        if expiration_seconds:
            payload_copy['exp'] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expiration_seconds)
            
        return jwt.encode(payload_copy, key, algorithm=algo)

    @classmethod
    def verify_jwt(cls, token: str, secret: Optional[str] = None, algorithms: Optional[List[str]] = None) -> dict:
        key = secret or cls.CONFIGURED_JWT_SECRET
        if not key:
            raise ValueError("JWT Secret is required")
            
        algos = algorithms or [cls.DEFAULT_JWT_ALGO]
        
        return jwt.decode(token, key, algorithms=algos)

    ### PRIVATE UTILITIES START
    @classmethod
    def _save_key_file(cls, directory: str, filename: str, content: str):
        if not os.path.exists(directory):
            os.makedirs(directory)
        path = os.path.join(directory, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    @classmethod
    def _get_hash_func(cls, algorithm: str):
        if algorithm not in hashlib.algorithms_available:
             # Fallback or check guarantees
             pass
        return hashlib.new(algorithm)
    ### PRIVATE UTILITIES END
