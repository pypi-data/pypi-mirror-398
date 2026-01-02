#!/usr/bin/env python3
"""
STXDefender - Python Source Code Encryption Tool
A SourceDefender-like tool for protecting Python code with AES-256-GCM encryption
"""

import os
import sys
import json
import base64
import hashlib
import requests
import uuid
import platform
import socket
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# API Configuration
API_URL = os.environ.get('STXDEFENDER_API_URL', 'http://localhost:5000')

def get_system_id():
    """Generate a stable machine fingerprint"""
    data = f"{platform.node()}{platform.system()}{platform.processor()}{socket.gethostname()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

SYSTEM_ID = get_system_id()
LICENSE_FILE = os.path.expanduser("~/.stxdefender/license.json")

def activate_license(token):
    """Activate license with token"""
    try:
        resp = requests.post(f"{API_URL}/api/activate", json={
            "token": token,
            "system_id": SYSTEM_ID
        }, timeout=10)
        data = resp.json()
        if data.get("success"):
            license_data = {
                "account_id": data["account_id"],
                "email": data["email"],
                "system_id": SYSTEM_ID,
                "valid_until": data["valid_until"],
                "status": "active"
            }
            os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
            with open(LICENSE_FILE, "w") as f:
                json.dump(license_data, f)
            print("STXDEFENDER ACTIVATED")
            print(f"\nRegistration:\n")
            print(f" - Account Status  : {license_data['status'].title()}")
            print(f" - Email Address   : {license_data['email']}")
            print(f" - Account ID      : {license_data['account_id']}")
            print(f" - System ID       : {SYSTEM_ID}")
            print(f" - Valid Until     : {license_data['valid_until']}")
            return True
        else:
            print("Activation failed:", data.get("error", "Unknown"))
            return False
    except requests.exceptions.RequestException as e:
        print(f"Activation error (no internet?): {e}")
        return False
    except Exception as e:
        print(f"Activation error: {e}")
        return False

def validate_license():
    """Validate current license"""
    if not os.path.exists(LICENSE_FILE):
        print("No license found. Use 'stxdefender activate --token <your-token>'")
        return False
    try:
        with open(LICENSE_FILE) as f:
            lic = json.load(f)
        if lic["system_id"] != SYSTEM_ID:
            print("License bound to different machine")
            return False
        valid_until = datetime.fromisoformat(lic["valid_until"].replace("Z", "+00:00"))
        if datetime.utcnow() > valid_until:
            print("License expired")
            return False
        print("STXDEFENDER")
        print("\nRegistration:\n")
        print(f" - Account Status  : {lic['status'].title()}")
        print(f" - Email Address   : {lic.get('email', 'N/A')}")
        print(f" - Account ID      : {lic.get('account_id', 'N/A')}")
        print(f" - System ID       : {SYSTEM_ID}")
        print(f" - Valid Until     : {lic['valid_until']}")
        return True
    except Exception as e:
        print(f"License validation failed: {e}")
        return False

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using PBKDF2"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
    )
    return kdf.derive(password.encode())

def parse_ttl(ttl_str):
    """Parse TTL string like '24h', '7d', '30m' into seconds"""
    if not ttl_str:
        return None
    if ttl_str[-1].isdigit():
        return int(ttl_str)
    num = int(ttl_str[:-1])
    unit = ttl_str[-1].lower()
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
    return num * multipliers.get(unit, 1)

def encrypt_file(input_path, output_path=None, password=None, ttl=None, remove=False):
    """Encrypt Python file"""
    # Check license (trial mode allows 24h max)
    has_valid_license = validate_license()
    if not has_valid_license:
        print("[WARNING] Trial mode: encrypted files limited to 24 hours")
        if ttl:
            ttl_seconds = parse_ttl(ttl)
            if ttl_seconds > 86400:
                print("[WARNING] Trial mode TTL limited to 24h, using 24h instead")
                ttl = "24h"

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return False

    with open(input_path, 'rb') as f:
        source = f.read().decode('utf-8')

    # Generate or use provided password
    if password is None:
        password = os.getenv("STXDEFENDER_PASSWORD") or base64.b64encode(os.urandom(32)).decode()

    # Generate salt and nonce
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    
    # Encrypt
    ct = aesgcm.encrypt(nonce, source.encode(), None)

    # Base64 encode
    encrypted_b64 = base64.b64encode(ct).decode()
    salt_b64 = base64.b64encode(salt).decode()
    nonce_b64 = base64.b64encode(nonce).decode()

    # Generate expiry code if TTL specified
    expiry_code = ""
    if ttl:
        ttl_seconds = parse_ttl(ttl)
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        expiry_code = f"""
# EXPIRY CHECK
from datetime import datetime, timezone
expiry = datetime.fromisoformat("{expiry.isoformat()}Z".replace('Z', '+00:00'))
if datetime.now(timezone.utc) > expiry:
    print("[ERROR] This script has expired on", expiry.isoformat())
    sys.exit(1)
"""

    # Generate encrypted file stub (Python)
    stub = f"""# -*- coding: utf-8 -*-
# ---BEGIN PYE FILE---
# Encrypted with STXDefender
import os
import base64
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

encrypted = "{encrypted_b64}"
salt = base64.b64decode("{salt_b64}")
nonce = base64.b64decode("{nonce_b64}")

def derive_key(passwd, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
    )
    return kdf.derive(passwd.encode())

password = os.environ.get("STXDEFENDER_PASSWORD", "{password}")
key = derive_key(password, salt)

# AES-256-GCM: encrypted data from encrypt() already contains auth tag appended
encrypted_bytes = base64.b64decode(encrypted)

aesgcm = AESGCM(key)
try:
    # Decrypt (auth tag is already part of encrypted_bytes from encrypt())
    decrypted = aesgcm.decrypt(nonce, encrypted_bytes, None)
except Exception as e:
    print("[ERROR] Decryption failed - wrong password or corrupted file")
    sys.exit(1)

{expiry_code}

# Execute original code
exec(decrypted.decode('utf-8'))
"""

    # Determine output path
    if not output_path:
        # Remove extension and add .pye
        base_name = os.path.splitext(input_path)[0]
        output_path = base_name + '.pye'

    # Write encrypted file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(stub)

    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod(output_path, 0o755)

    print("STXDEFENDER")
    print(f"\nProcessing:\n\n  {input_path}\n")
    print(f"Encrypted → {output_path}")
    if ttl:
        print(f"TTL enforced: {ttl}")

    if remove:
        os.remove(input_path)
        print(f"Original {input_path} removed")

    return True

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("STXDefender - Python Source Code Encryption")
        print("\nUsage:")
        print("  stxdefender activate --token <token>")
        print("  stxdefender validate")
        print("  stxdefender encrypt [--remove] [--ttl=1h] [--password=xxx] <file>")
        print("\nExamples:")
        print("  stxdefender activate --token YOUR_TOKEN")
        print("  stxdefender encrypt --remove --ttl=24h myapp.py")
        print("  stxdefender encrypt --password=secret script.py")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "activate":
        token = None
        if "--token" in sys.argv:
            idx = sys.argv.index("--token")
            if idx + 1 < len(sys.argv):
                token = sys.argv[idx + 1]
        if not token:
            token = input("Token: ").strip()
        
        success = activate_license(token)
        sys.exit(0 if success else 1)

    elif cmd == "validate":
        success = validate_license()
        sys.exit(0 if success else 1)

    elif cmd == "encrypt":
        input_file = None
        password = None
        ttl = None
        remove = "--remove" in sys.argv
        
        # Find the input file (any file that's not a flag/option)
        for arg in sys.argv[2:]:
            if not arg.startswith("--") and os.path.isfile(arg):
                input_file = arg
            elif arg.startswith("--password="):
                password = arg.split("=", 1)[1]
            elif arg.startswith("--ttl="):
                ttl = arg.split("=", 1)[1]
        
        if not input_file:
            print("[ERROR] No input file specified")
            print("Usage: stxdefender encrypt [options] <file>")
            print("\nSupported file types: .py")
            sys.exit(1)
        
        success = encrypt_file(input_file, password=password, ttl=ttl, remove=remove)
        sys.exit(0 if success else 1)

    else:
        print(f"[ERROR] Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()

