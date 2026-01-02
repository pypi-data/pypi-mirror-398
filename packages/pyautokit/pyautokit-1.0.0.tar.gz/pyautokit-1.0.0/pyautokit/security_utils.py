"""Security utilities for encryption and hashing.

Features:
- File encryption/decryption (Fernet)
- Password-based key derivation (PBKDF2)
- Secure password generation
- Hashing utilities (MD5, SHA256, SHA512)
- Token generation
"""

import argparse
import sys
import hashlib
import secrets
import string
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
from .logger import setup_logger
from .config import Config

logger = setup_logger("SecurityUtils", level=Config.LOG_LEVEL)


class SecurityUtils:
    """Security utilities for encryption and hashing."""

    @staticmethod
    def generate_key() -> bytes:
        """Generate Fernet encryption key.
        
        Returns:
            Encryption key bytes
        """
        return Fernet.generate_key()

    @staticmethod
    def derive_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Derive key from password using PBKDF2.
        
        Args:
            password: Password string
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    @staticmethod
    def encrypt_file(
        input_path: Path,
        output_path: Path,
        key: bytes
    ) -> bool:
        """Encrypt file.
        
        Args:
            input_path: Input file path
            output_path: Output encrypted file path
            key: Encryption key
            
        Returns:
            True if successful
        """
        try:
            fernet = Fernet(key)
            
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted = fernet.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            logger.info(f"Encrypted: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return False

    @staticmethod
    def decrypt_file(
        input_path: Path,
        output_path: Path,
        key: bytes
    ) -> bool:
        """Decrypt file.
        
        Args:
            input_path: Input encrypted file path
            output_path: Output decrypted file path
            key: Decryption key
            
        Returns:
            True if successful
        """
        try:
            fernet = Fernet(key)
            
            with open(input_path, 'rb') as f:
                encrypted = f.read()
            
            decrypted = fernet.decrypt(encrypted)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            logger.info(f"Decrypted: {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return False

    @staticmethod
    def hash_text(text: str, algorithm: str = "sha256") -> str:
        """Hash text with specified algorithm.
        
        Args:
            text: Text to hash
            algorithm: Hash algorithm (md5, sha256, sha512)
            
        Returns:
            Hex digest string
        """
        if algorithm == "md5":
            h = hashlib.md5()
        elif algorithm == "sha256":
            h = hashlib.sha256()
        elif algorithm == "sha512":
            h = hashlib.sha512()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        h.update(text.encode())
        return h.hexdigest()

    @staticmethod
    def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
        """Hash file contents.
        
        Args:
            file_path: File to hash
            algorithm: Hash algorithm
            
        Returns:
            Hex digest string
        """
        if algorithm == "md5":
            h = hashlib.md5()
        elif algorithm == "sha256":
            h = hashlib.sha256()
        elif algorithm == "sha512":
            h = hashlib.sha512()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        
        return h.hexdigest()

    @staticmethod
    def generate_password(
        length: int = 16,
        use_special: bool = True,
        use_digits: bool = True,
        use_uppercase: bool = True
    ) -> str:
        """Generate secure random password.
        
        Args:
            length: Password length
            use_special: Include special characters
            use_digits: Include digits
            use_uppercase: Include uppercase letters
            
        Returns:
            Generated password
        """
        chars = string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_digits:
            chars += string.digits
        if use_special:
            chars += string.punctuation
        
        return ''.join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Hex token string
        """
        return secrets.token_hex(length)


def main() -> int:
    """CLI for security utilities."""
    parser = argparse.ArgumentParser(
        description="Security utilities for encryption and hashing",
        epilog="Examples:\n"
               "  %(prog)s encrypt file.txt file.enc --password mysecret\n"
               "  %(prog)s decrypt file.enc file.txt --password mysecret\n"
               "  %(prog)s hash file.txt --algorithm sha256\n"
               "  %(prog)s genpass --length 20\n"
               "  %(prog)s token --length 32\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt file")
    encrypt_parser.add_argument("input", help="Input file path")
    encrypt_parser.add_argument("output", help="Output encrypted file path")
    encrypt_parser.add_argument(
        "--password",
        "-p",
        help="Password for encryption (key derived from password)"
    )
    encrypt_parser.add_argument(
        "--key",
        "-k",
        help="Encryption key (base64 encoded)"
    )
    
    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt file")
    decrypt_parser.add_argument("input", help="Input encrypted file path")
    decrypt_parser.add_argument("output", help="Output decrypted file path")
    decrypt_parser.add_argument(
        "--password",
        "-p",
        help="Password for decryption"
    )
    decrypt_parser.add_argument(
        "--key",
        "-k",
        help="Decryption key (base64 encoded)"
    )
    
    # Hash command
    hash_parser = subparsers.add_parser("hash", help="Hash text or file")
    hash_parser.add_argument("input", help="Text or file path to hash")
    hash_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["md5", "sha256", "sha512"],
        default="sha256",
        help="Hash algorithm (default: sha256)"
    )
    hash_parser.add_argument(
        "--file",
        action="store_true",
        help="Input is a file path (not text)"
    )
    
    # Generate password
    genpass_parser = subparsers.add_parser("genpass", help="Generate password")
    genpass_parser.add_argument(
        "--length",
        "-l",
        type=int,
        default=16,
        help="Password length (default: 16)"
    )
    genpass_parser.add_argument(
        "--no-special",
        action="store_true",
        help="Exclude special characters"
    )
    genpass_parser.add_argument(
        "--no-digits",
        action="store_true",
        help="Exclude digits"
    )
    genpass_parser.add_argument(
        "--no-uppercase",
        action="store_true",
        help="Exclude uppercase letters"
    )
    
    # Generate token
    token_parser = subparsers.add_parser("token", help="Generate random token")
    token_parser.add_argument(
        "--length",
        "-l",
        type=int,
        default=32,
        help="Token length in bytes (default: 32)"
    )
    
    # Generate key
    subparsers.add_parser("genkey", help="Generate encryption key")
    
    # Global options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.verbose:
        logger.setLevel("DEBUG")
    
    utils = SecurityUtils()
    
    # Execute command
    if args.command == "encrypt":
        if args.key:
            key = args.key.encode()
        elif args.password:
            key, salt = utils.derive_key(args.password)
            # Save salt for decryption
            salt_file = Path(args.output).with_suffix('.salt')
            salt_file.write_bytes(salt)
            logger.info(f"Salt saved to {salt_file}")
        else:
            print("❌ Error: Provide --password or --key")
            return 1
        
        success = utils.encrypt_file(Path(args.input), Path(args.output), key)
        if success:
            print(f"✅ Encrypted: {args.output}")
            return 0
        return 1
    
    elif args.command == "decrypt":
        if args.key:
            key = args.key.encode()
        elif args.password:
            # Load salt
            salt_file = Path(args.input).with_suffix('.salt')
            if not salt_file.exists():
                print(f"❌ Salt file not found: {salt_file}")
                return 1
            salt = salt_file.read_bytes()
            key, _ = utils.derive_key(args.password, salt)
        else:
            print("❌ Error: Provide --password or --key")
            return 1
        
        success = utils.decrypt_file(Path(args.input), Path(args.output), key)
        if success:
            print(f"✅ Decrypted: {args.output}")
            return 0
        return 1
    
    elif args.command == "hash":
        if args.file:
            digest = utils.hash_file(Path(args.input), args.algorithm)
        else:
            digest = utils.hash_text(args.input, args.algorithm)
        
        print(f"{args.algorithm.upper()}: {digest}")
        return 0
    
    elif args.command == "genpass":
        password = utils.generate_password(
            length=args.length,
            use_special=not args.no_special,
            use_digits=not args.no_digits,
            use_uppercase=not args.no_uppercase
        )
        print(password)
        return 0
    
    elif args.command == "token":
        token = utils.generate_token(args.length)
        print(token)
        return 0
    
    elif args.command == "genkey":
        key = utils.generate_key()
        print(key.decode())
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
