#!/usr/bin/env python3
"""
Utility script to generate wallet encryption key
"""

from cryptography.fernet import Fernet
import base64

def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    return key

def main():
    print("🔐 Wallet Encryption Key Generator")
    print("=" * 50)
    
    # Generate new key
    key = generate_encryption_key()
    
    print(f"✅ Generated key: {key.decode()}")
    print()
    print("📝 Usage:")
    print("1. Set this key as an environment variable:")
    print(f"   export WALLET_ENCRYPTION_KEY='{key.decode()}'")
    print()
    print("2. Or add to your .env file:")
    print(f"   WALLET_ENCRYPTION_KEY={key.decode()}")
    print()
    print("3. Windows PowerShell:")
    print(f"   $env:WALLET_ENCRYPTION_KEY='{key.decode()}'")
    print()
    print("⚠️  Important:")
    print("- Keep this key safe. If lost, you cannot decrypt stored wallets.")
    print("- It is recommended to store the key in a secure key management system.")
    print("- Do not commit the key to version control.")

if __name__ == "__main__":
    main() 