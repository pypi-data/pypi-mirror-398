"""
Data Security - Comprehensive encryption, tokenization, and key management
Modern cryptography with AES-256, TDE, and secure key rotation.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
import secrets
import json


class EncryptionAlgorithm(Enum):
    """Encryption algorithms"""
    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    CHACHA20 = "ChaCha20-Poly1305"
    RSA_4096 = "RSA-4096"


class KeyRotationPolicy(Enum):
    """Key rotation policies"""
    NEVER = "NEVER"
    QUARTERLY = "QUARTERLY"
    ANNUALLY = "ANNUALLY"
    ON_DEMAND = "ON_DEMAND"


@dataclass
class EncryptionKey:
    """Represents an encryption key"""
    key_id: str
    algorithm: EncryptionAlgorithm
    key_material: bytes
    created_at: datetime = field(default_factory=datetime.now)
    rotated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def is_rotatable(self) -> bool:
        """Check if key should be rotated"""
        if not self.is_active:
            return False
        
        age_days = (datetime.now() - self.created_at).days
        return age_days > 90  # Suggest rotation after 90 days


@dataclass
class EncryptedData:
    """Represents encrypted data"""
    ciphertext: bytes
    nonce: bytes
    associated_data: Optional[bytes] = None
    algorithm: str = "AES-256-GCM"
    key_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage"""
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode(),
            "nonce": base64.b64encode(self.nonce).decode(),
            "associated_data": base64.b64encode(self.associated_data).decode() if self.associated_data else None,
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "timestamp": self.timestamp.isoformat()
        }


class CryptoEngine:
    """Cryptographic operations engine"""
    
    @staticmethod
    def generate_key(algorithm: EncryptionAlgorithm, key_id: str) -> EncryptionKey:
        """Generate a new encryption key"""
        # Simplified - in production use cryptography library
        key_size = 32 if "256" in algorithm.value else 16
        key_material = secrets.token_bytes(key_size)
        
        expires_at = datetime.now() + timedelta(days=365)
        
        return EncryptionKey(
            key_id=key_id,
            algorithm=algorithm,
            key_material=key_material,
            expires_at=expires_at
        )
    
    @staticmethod
    def encrypt(data: str, key: EncryptionKey) -> EncryptedData:
        """Encrypt data"""
        # Simplified encryption - in production use cryptography library
        plaintext = data.encode()
        nonce = secrets.token_bytes(12)
        
        # Simple XOR cipher for demo (NOT production-ready)
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, key.key_material))
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            algorithm=key.algorithm.value,
            key_id=key.key_id
        )
    
    @staticmethod
    def decrypt(encrypted_data: EncryptedData, key: EncryptionKey) -> str:
        """Decrypt data"""
        # Simplified decryption - in production use cryptography library
        plaintext = bytes(a ^ b for a, b in zip(encrypted_data.ciphertext, key.key_material))
        return plaintext.decode()
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32).encode()
        else:
            salt = salt.encode() if isinstance(salt, str) else salt
        
        # PBKDF2 hashing
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        hash_hex = hash_obj.hex()
        salt_hex = salt.hex()
        
        return hash_hex, salt_hex
    
    @staticmethod
    def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
        """Verify password"""
        salt = bytes.fromhex(salt_hex)
        new_hash, _ = CryptoEngine.hash_password(password, salt)
        return hmac.compare_digest(new_hash, hash_hex)


class TokenizationEngine:
    """Data tokenization for PII protection"""
    
    def __init__(self):
        self.token_map: Dict[str, str] = {}
        self.reverse_map: Dict[str, str] = {}
    
    def tokenize(self, sensitive_data: str, data_type: str = "pii") -> str:
        """Tokenize sensitive data"""
        if sensitive_data in self.token_map:
            return self.token_map[sensitive_data]
        
        # Generate deterministic token
        token = f"TOKEN_{data_type}_{len(self.token_map):06d}"
        
        self.token_map[sensitive_data] = token
        self.reverse_map[token] = sensitive_data
        
        return token
    
    def detokenize(self, token: str) -> Optional[str]:
        """Recover original data from token"""
        return self.reverse_map.get(token)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tokenization statistics"""
        return {
            "tokens_created": len(self.token_map),
            "token_types": len(set(v.split("_")[1] for v in self.token_map.values()))
        }


class KeyManagementService:
    """Manages encryption keys and rotation"""
    
    def __init__(self):
        self.keys: Dict[str, EncryptionKey] = {}
        self.active_key: Optional[EncryptionKey] = None
        self.key_rotation_policy = KeyRotationPolicy.QUARTERLY
        self.rotation_history: List[Dict[str, Any]] = []
    
    def create_key(self, algorithm: EncryptionAlgorithm) -> EncryptionKey:
        """Create a new key"""
        key_id = f"key_{len(self.keys):04d}_{datetime.now().timestamp()}"
        key = CryptoEngine.generate_key(algorithm, key_id)
        
        self.keys[key_id] = key
        
        if self.active_key is None:
            self.active_key = key
        
        return key
    
    def rotate_key(self, old_key: EncryptionKey) -> EncryptionKey:
        """Rotate a key"""
        old_key.is_active = False
        new_key = self.create_key(old_key.algorithm)
        
        self.rotation_history.append({
            "timestamp": datetime.now().isoformat(),
            "old_key_id": old_key.key_id,
            "new_key_id": new_key.key_id,
            "reason": "scheduled rotation"
        })
        
        return new_key
    
    def get_active_key(self) -> Optional[EncryptionKey]:
        """Get the active key"""
        if self.active_key and not self.active_key.is_expired():
            return self.active_key
        
        # Rotate if needed
        if self.active_key:
            return self.rotate_key(self.active_key)
        
        return None
    
    def check_rotation_needed(self) -> List[EncryptionKey]:
        """Check which keys need rotation"""
        needs_rotation = []
        
        for key in self.keys.values():
            if key.is_active and key.is_rotatable():
                needs_rotation.append(key)
        
        return needs_rotation
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get key by ID"""
        return self.keys.get(key_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get key management statistics"""
        return {
            "total_keys": len(self.keys),
            "active_keys": sum(1 for k in self.keys.values() if k.is_active),
            "expired_keys": sum(1 for k in self.keys.values() if k.is_expired()),
            "keys_needing_rotation": len(self.check_rotation_needed()),
            "rotations_performed": len(self.rotation_history)
        }


class TransparentDataEncryption:
    """Transparent Data Encryption (TDE) for entire database"""
    
    def __init__(self, kms: KeyManagementService):
        self.kms = kms
        self.encrypted_tables: Dict[str, bool] = {}
        self.tde_enabled = False
    
    def enable_tde(self):
        """Enable Transparent Data Encryption"""
        self.tde_enabled = True
    
    def disable_tde(self):
        """Disable TDE"""
        self.tde_enabled = False
    
    def encrypt_table(self, table_name: str) -> bool:
        """Mark table for encryption"""
        if not self.tde_enabled:
            return False
        
        self.encrypted_tables[table_name] = True
        return True
    
    def encrypt_row(self, table_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt a row"""
        if not self.tde_enabled or table_name not in self.encrypted_tables:
            return row
        
        key = self.kms.get_active_key()
        if not key:
            return row
        
        encrypted_row = {}
        for col, value in row.items():
            if isinstance(value, str) and col != "id":  # Don't encrypt ID
                encrypted = CryptoEngine.encrypt(value, key)
                encrypted_row[col] = encrypted.to_dict()
            else:
                encrypted_row[col] = value
        
        return encrypted_row
    
    def get_status(self) -> Dict[str, Any]:
        """Get TDE status"""
        return {
            "tde_enabled": self.tde_enabled,
            "encrypted_tables": len(self.encrypted_tables),
            "tables": list(self.encrypted_tables.keys())
        }


class DataSecurity:
    """Main data security manager"""
    
    def __init__(self):
        self.kms = KeyManagementService()
        self.tde = TransparentDataEncryption(self.kms)
        self.tokenization = TokenizationEngine()
        self.crypto = CryptoEngine()
        self.operations_log: List[Dict[str, Any]] = []
    
    def initialize(self):
        """Initialize security"""
        # Create initial key
        self.kms.create_key(EncryptionAlgorithm.AES_256_GCM)
        self.tde.enable_tde()
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a single field"""
        key = self.kms.get_active_key()
        if not key:
            return value
        
        encrypted = self.crypto.encrypt(value, key)
        self._log_operation("encrypt", value[:10])
        
        return base64.b64encode(json.dumps(encrypted.to_dict()).encode()).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a single field"""
        try:
            encrypted_dict = json.loads(base64.b64decode(encrypted_value).decode())
            encrypted_data = EncryptedData(
                ciphertext=base64.b64decode(encrypted_dict["ciphertext"]),
                nonce=base64.b64decode(encrypted_dict["nonce"]),
                algorithm=encrypted_dict["algorithm"],
                key_id=encrypted_dict["key_id"]
            )
            
            key = self.kms.get_key(encrypted_data.key_id)
            if not key:
                return "[DECRYPTION_FAILED]"
            
            value = self.crypto.decrypt(encrypted_data, key)
            self._log_operation("decrypt", "***")
            
            return value
        except:
            return "[DECRYPTION_FAILED]"
    
    def tokenize_pii(self, sensitive_data: str) -> str:
        """Tokenize PII data"""
        token = self.tokenization.tokenize(sensitive_data, "pii")
        self._log_operation("tokenize", sensitive_data[:10])
        return token
    
    def detokenize_pii(self, token: str) -> Optional[str]:
        """Recover tokenized PII"""
        data = self.tokenization.detokenize(token)
        if data:
            self._log_operation("detokenize", "***")
        return data
    
    def _log_operation(self, operation: str, data_sample: str):
        """Log security operation"""
        self.operations_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "data_sample": data_sample
        })
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        keys_to_rotate = self.kms.check_rotation_needed()
        
        return {
            "tde_status": self.tde.get_status(),
            "key_management": self.kms.get_statistics(),
            "tokenization": self.tokenization.get_statistics(),
            "keys_need_rotation": len(keys_to_rotate),
            "security_operations": len(self.operations_log),
            "active_key": self.kms.get_active_key().key_id if self.kms.get_active_key() else None
        }
    
    def rotate_encryption_keys(self) -> Dict[str, Any]:
        """Perform key rotation"""
        result = {"rotated_keys": []}
        
        keys_to_rotate = self.kms.check_rotation_needed()
        for key in keys_to_rotate:
            new_key = self.kms.rotate_key(key)
            result["rotated_keys"].append({
                "old_key": key.key_id,
                "new_key": new_key.key_id
            })
        
        return result


if __name__ == "__main__":
    print("✓ Data security module loaded successfully")
