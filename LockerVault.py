from cryptography.fernet import Fernet
import os

class VaultManager:
    def __init__(self, key_file: str = "vault.key"):
        self.key_file = key_file
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
    def _load_or_create_key(self) -> bytes:
        #Loads existing key or creates a new one
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as file:
                return file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as file:
                file.write(key)
            return key

    def lock_data(self, data: str) -> bytes:
        #Encrypts the given string data.
        return self.cipher.encrypt(data.encode())
    
    def unlock_data(self, encrypted_data: bytes) -> str:
        #Decrypts the given encrypted bytes
        return self.cipher.decrypt(encrypted_data).decode()
    
    def lock_file(self, input_path: str, output_path: str):
        #Encrypts a file and saves the encrypted version
        with open(input_path, 'rb') as file:
            encrypted = self.cipher.encrypt(file.read())
        with open(output_path, 'wb') as file:
            file.write(encrypted)
            
    def unlock_file(self, input_path: str, output_path: str):
        #Decrypts a file and saves the plaintext version
        with open(input_path, 'rb') as file:
            decrypted = self.cipher.decrypt(file.read())
        with open(output_path, 'wb') as file:
            file.write(decrypted)
