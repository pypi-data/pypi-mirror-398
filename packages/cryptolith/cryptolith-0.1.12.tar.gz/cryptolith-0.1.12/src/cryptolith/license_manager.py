import os
import json
import base64
import hashlib
import uuid
import subprocess
import sys
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# In a real production scenario, this Public Key would be hardcoded here.
# For this implementation, we'll expose a way to generate/verify.

PUBLIC_KEY_B64 = "UCEk0hmv7niks3fhKIz2idTI5kprufLyTWsgKQ6YUdE="

class LicenseManager:
    """
    Handles offline license verification using ED25519 digital signatures.
    """
    def __init__(self, public_key_b64=None):
        self.public_key_b64 = public_key_b64 or PUBLIC_KEY_B64
        try:
            self.public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                base64.b64decode(self.public_key_b64)
            )
        except Exception:
            self.public_key = None

    def get_hardware_id(self):
        """
        Generates a unique hardware identifier for this machine.
        Uses MAC address + System UUID (Windows) for stability.
        Returns SHA256 hash of the identifier.
        """
        mac = uuid.getnode()
        sys_uuid = ""
        
        # Try to get system UUID on Windows
        if sys.platform == 'win32':
            try:
                cmd = "wmic csproduct get uuid"
                # Use shell=True to suppress window on some setups, verify output
                res = subprocess.check_output(cmd, shell=True).decode()
                # Output format:
                # UUID
                # XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
                lines = res.strip().split('\n')
                if len(lines) > 1:
                    sys_uuid = lines[1].strip()
            except Exception:
                pass
                
        raw_id = f"{mac}-{sys_uuid}"
        return hashlib.sha256(raw_id.encode()).hexdigest()

    def verify_license(self, license_path):
        """
        Verifies a license.dat file.
        Format: Base64(JSON_DATA) . Base64(SIGNATURE)
        """
        if not os.path.exists(license_path):
            return None
        
        try:
            with open(license_path, 'r') as f:
                content = f.read().strip()
            
            if '.' not in content:
                return None
            
            data_b64, sig_b64 = content.split('.')
            data_bytes = base64.b64decode(data_b64)
            sig_bytes = base64.b64decode(sig_b64)
            
            self.public_key.verify(sig_bytes, data_bytes)
            
            # If verification passes, decode data
            license_data = json.loads(data_bytes.decode('utf-8'))
            
            # Check Hardware ID if present
            if 'hardware_id' in license_data:
                current_hwid = self.get_hardware_id()
                if license_data['hardware_id'] != current_hwid:
                    print(f"[LICENSE] Hardware ID Mismatch! License: {license_data['hardware_id']} vs Machine: {current_hwid}")
                    return None

            return license_data # e.g. {"user": "John Doe", "tier": "Pro"}
        except Exception:
            return None

    @staticmethod
    def generate_keys():
        """
        Utility to generate a new key pair.
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return base64.b64encode(priv_bytes).decode('utf-8'), base64.b64encode(pub_bytes).decode('utf-8')

    @staticmethod
    def create_license(data_dict, private_key_b64):
        """
        Utility to create a signed license.dat.
        """
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(private_key_b64)
        )
        data_json = json.dumps(data_dict).encode('utf-8')
        signature = private_key.sign(data_json)
        
        data_b64 = base64.b64encode(data_json).decode('utf-8')
        sig_b64 = base64.b64encode(signature).decode('utf-8')
        
        return f"{data_b64}.{sig_b64}"
