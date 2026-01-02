from cryptography.fernet import Fernet
import sys


def generate_key():
    key = Fernet.generate_key()
    print(key.decode('utf-8'))


def encrypt_value(key_str: str, value: str):
    from .types import set_encryption_key, encrypt_secret
    
    key = key_str.encode('utf-8')
    set_encryption_key(key)
    
    encrypted = encrypt_secret(value)
    print(f"ENC({encrypted})")


def decrypt_value(key_str: str, encrypted_value: str):
    from .types import set_encryption_key, decrypt_secret
    
    key = key_str.encode('utf-8')
    set_encryption_key(key)
    
    if encrypted_value.startswith("ENC(") and encrypted_value.endswith(")"):
        encrypted_value = encrypted_value[4:-1]
    
    decrypted = decrypt_secret(encrypted_value)
    print(decrypted)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m dotpop.crypto generate")
        print("  python -m dotpop.crypto encrypt <key> <value>")
        print("  python -m dotpop.crypto decrypt <key> <encrypted_value>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        generate_key()
    elif command == "encrypt":
        if len(sys.argv) != 4:
            print("Usage: python -m dotpop.crypto encrypt <key> <value>")
            sys.exit(1)
        encrypt_value(sys.argv[2], sys.argv[3])
    elif command == "decrypt":
        if len(sys.argv) != 4:
            print("Usage: python -m dotpop.crypto decrypt <key> <encrypted_value>")
            sys.exit(1)
        decrypt_value(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
