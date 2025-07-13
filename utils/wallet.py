import os
import sqlite3
import json
import hashlib
import base64
from typing import Optional, Dict, List, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
from eth_account import Account
from eth_account.messages import encode_defunct
import asyncio
import httpx
from datetime import datetime

# Ensure Account can generate private keys
Account.enable_unaudited_hdwallet_features()

class WalletManager:
    def __init__(self, db_path: str = "wallets.db"):
        self.db_path = db_path
        self.init_database()
        self._load_encryption_key()
    
    def _load_encryption_key(self):
        """Load or generate encryption key"""
        # First try to load from environment variable
        env_key = os.getenv('WALLET_ENCRYPTION_KEY')
        
        if env_key:
            try:
                # If the environment variable is base64 encoded, use directly
                if len(env_key) == 44:  # Standard length for Fernet key
                    self.encryption_key = env_key.encode()
                else:
                    # If not standard length, try base64 decode
                    self.encryption_key = base64.b64decode(env_key)
                
                # Validate key
                Fernet(self.encryption_key)
                print("✅ Using encryption key from environment variable")
                
            except Exception as e:
                print(f"⚠️ Invalid key in environment variable: {e}")
                print("Will use file-stored key or generate a new one")
                env_key = None
        
        # If environment variable is not set or invalid, use file
        if not env_key:
            key_file = "wallet_key.key"
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    self.encryption_key = f.read()
                print("✅ Using encryption key from file")
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(self.encryption_key)
                print("✅ Generated new encryption key and saved to file")
                print(f"💡 Tip: You can set the following key as WALLET_ENCRYPTION_KEY:")
                print(f"   {self.encryption_key.decode()}")
        
        self.cipher = Fernet(self.encryption_key)
    
    def _encrypt_private_key(self, private_key: str) -> str:
        """Encrypt private key"""
        return self.cipher.encrypt(private_key.encode()).decode()
    
    def _decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    def init_database(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wallet_name TEXT NOT NULL,
                address TEXT NOT NULL,
                encrypted_private_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, address)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_wallet(self, user_id: int, wallet_name: str = "Default") -> Dict[str, str]:
        """Generate a new wallet"""
        # Generate private key
        private_key = Account.create().key.hex()
        account = Account.from_key(private_key)
        address = account.address
        
        # Encrypt private key
        encrypted_key = self._encrypt_private_key(private_key)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_wallets (user_id, wallet_name, address, encrypted_private_key)
                VALUES (?, ?, ?, ?)
            ''', (user_id, wallet_name, address, encrypted_key))
            conn.commit()
            
            return {
                "address": address,
                "private_key": private_key,  # Only return once for user display
                "wallet_name": wallet_name
            }
        except sqlite3.IntegrityError:
            return {"error": "Wallet already exists for this user"}
        finally:
            conn.close()
    
    def import_wallet(self, user_id: int, private_key: str, wallet_name: str = "Imported") -> Dict[str, str]:
        """Import wallet"""
        try:
            # Validate private key
            account = Account.from_key(private_key)
            address = account.address
            
            # Encrypt private key
            encrypted_key = self._encrypt_private_key(private_key)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO user_wallets (user_id, wallet_name, address, encrypted_private_key)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, wallet_name, address, encrypted_key))
                conn.commit()
                
                return {
                    "address": address,
                    "wallet_name": wallet_name
                }
            except sqlite3.IntegrityError:
                return {"error": "Wallet already exists for this user"}
            finally:
                conn.close()
        except Exception as e:
            return {"error": f"Invalid private key: {str(e)}"}
    
    def delete_wallet(self, user_id: int, address: str) -> Dict[str, str]:
        """Delete wallet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_wallets 
            WHERE user_id = ? AND address = ?
        ''', (user_id, address))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            return {"success": f"Wallet {address} deleted successfully"}
        else:
            return {"error": "Wallet not found"}
    
    def get_user_wallets(self, user_id: int) -> List[Dict[str, str]]:
        """Get all wallets of the user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT wallet_name, address, created_at 
            FROM user_wallets 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        wallets = []
        for row in cursor.fetchall():
            wallets.append({
                "wallet_name": row[0],
                "address": row[1],
                "created_at": row[2]
            })
        
        conn.close()
        return wallets
    
    def get_wallet_private_key(self, user_id: int, address: str) -> Optional[str]:
        """Get the decrypted private key of the wallet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_private_key 
            FROM user_wallets 
            WHERE user_id = ? AND address = ?
        ''', (user_id, address))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return self._decrypt_private_key(result[0])
        return None

    def get_user_wallet(self, user_id: int) -> Optional[Dict[str, str]]:
        """Get the user's wallet (single-wallet logic)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT wallet_name, address, encrypted_private_key, created_at
            FROM user_wallets
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "wallet_name": row[0],
                "address": row[1],
                "encrypted_private_key": row[2],
                "created_at": row[3]
            }
        return None

# Global wallet manager instance
wallet_manager = WalletManager() 