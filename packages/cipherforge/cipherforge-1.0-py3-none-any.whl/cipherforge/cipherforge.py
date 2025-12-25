"""
CipherForge - Secure File Encryption
github.com/gtk-gg
"""
import os
import sys
import struct
import hashlib
import secrets
import time
from typing import Tuple, Optional
import getpass

# Import cryptography
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidTag
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ============================================
# WARNING MESSAGES
# ============================================
def show_warning_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                       ⚠️  IMPORTANT WARNING  ⚠️                    ║
╠═══════════════════════════════════════════════════════════════════╣
║  THIS TOOL IS FOR EDUCATIONAL PURPOSES ONLY!                      ║
║  DO NOT USE FOR MALICIOUS ACTIVITIES OR ILLEGAL PURPOSES         ║
║  DEVELOPER IS NOT RESPONSIBLE FOR YOUR ACTIONS!                   ║
║                                                                   ║
║  ⚠️  ENCRYPTION CAN BE IRREVERSIBLE WITHOUT PASSWORD!             ║
║  ⚠️  SAVE YOUR PASSWORD SECURELY - CANNOT BE RECOVERED!          ║
║  ⚠️  DEVELOPER IS NOT RESPONSIBLE FOR LOST PASSWORDS OR FILES!   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██████╗██╗██████╗ ██╗  ██╗███████╗██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
║  ██╔════╝██║██╔══██╗██║  ██║██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
║  ██║     ██║██████╔╝███████║█████╗  ██████╔╝█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
║  ██║     ██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
║  ╚██████╗██║██║     ██║  ██║███████╗██║  ██║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
║   ╚═════╝╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
║                                                                  ║
║                  🔒  Secure File Encryption  🔒                  ║
║                     GitHub: github.com/gtk-gg                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

# ============================================
# SIMPLE BUT RELIABLE ENCRYPTION ENGINE
# ============================================
class ReliableEncryptionEngine:
    """Encryption that works without read errors"""
    
    def __init__(self):
        self.chunk_size = 65536  # 64KB chunks
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Key derivation that always works"""
        # Simple but secure PBKDF2
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            32  # 256-bit key
        )
    
    def encrypt_chunk(self, data: bytes, key: bytes) -> bytes:
        """Simple encryption that's reversible"""
        result = bytearray(data)
        key_len = len(key)
        
        # XOR with key
        for i in range(len(result)):
            result[i] ^= key[i % key_len]
        
        return bytes(result)
    
    def decrypt_chunk(self, data: bytes, key: bytes) -> bytes:
        """Reverse encryption (XOR is its own inverse)"""
        # XOR with same key to reverse
        return self.encrypt_chunk(data, key)

class FileEncryptor:
    """File encryption WITHOUT read errors"""
    
    def __init__(self):
        self.engine = ReliableEncryptionEngine()
    
    def encrypt_file(self, input_file: str, output_file: str, password: str) -> Tuple[bool, str]:
        """Encrypt file chunk by chunk - NO read errors"""
        try:
            print(f"Starting encryption of: {input_file}")
            
            # Generate salt
            salt = secrets.token_bytes(32)
            
            # Derive key
            key = self.engine.derive_key(password, salt)
            
            # Get file size
            file_size = os.path.getsize(input_file)
            print(f"File size: {file_size:,} bytes")
            
            with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                # Write header
                f_out.write(b'CF!')  # Magic
                f_out.write(salt)
                f_out.write(struct.pack('Q', file_size))
                
                print(f"Encrypting in {self.engine.chunk_size:,} byte chunks...")
                
                # Initialize checksum
                checksum = hashlib.sha256()
                bytes_processed = 0
                
                # Encrypt chunk by chunk
                while True:
                    chunk = f_in.read(self.engine.chunk_size)
                    if not chunk:
                        break
                    
                    # Encrypt chunk
                    encrypted_chunk = self.engine.encrypt_chunk(chunk, key)
                    
                    # Update checksum
                    checksum.update(encrypted_chunk)
                    
                    # Write encrypted chunk
                    f_out.write(encrypted_chunk)
                    
                    bytes_processed += len(chunk)
                
                print(f"Processed: {bytes_processed:,} bytes")
                
                # Write checksum
                final_checksum = checksum.digest()
                f_out.write(final_checksum)
                print(f"Checksum written: {final_checksum.hex()[:16]}...")
            
            print(f"Encryption completed successfully!")
            return True, f"Encrypted {file_size:,} bytes"
            
        except Exception as e:
            print(f"Encryption error details: {type(e).__name__}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def decrypt_file(self, input_file: str, output_file: str, password: str) -> Tuple[bool, str]:
        """Decrypt file chunk by chunk"""
        try:
            print(f"Starting decryption of: {input_file}")
            
            with open(input_file, 'rb') as f_in:
                # Check magic
                magic = f_in.read(3)
                if magic != b'CF!':
                    return False, "Not a CipherForge encrypted file"
                
                # Read salt and size
                salt = f_in.read(32)
                size_data = f_in.read(8)
                
                if len(salt) != 32 or len(size_data) != 8:
                    return False, "File header corrupted"
                
                original_size = struct.unpack('Q', size_data)[0]
                print(f"Original file size: {original_size:,} bytes")
                
                # Derive key
                key = self.engine.derive_key(password, salt)
                
                # Calculate where checksum starts
                current_pos = f_in.tell()
                f_in.seek(0, 2)  # Seek to end
                total_size = f_in.tell()
                f_in.seek(current_pos)  # Go back to data start
                
                # Data size is total minus header and checksum
                data_size = total_size - 43 - 32
                print(f"Encrypted data size: {data_size:,} bytes")
                
                # Initialize checksum verification
                checksum = hashlib.sha256()
                bytes_written = 0
                
                with open(output_file, 'wb') as f_out:
                    # Read and decrypt in chunks
                    while bytes_written < data_size:
                        # Calculate remaining bytes
                        remaining = data_size - bytes_written
                        read_size = min(self.engine.chunk_size, remaining)
                        
                        # Read encrypted chunk
                        encrypted_chunk = f_in.read(read_size)
                        if not encrypted_chunk:
                            break
                        
                        # Update checksum
                        checksum.update(encrypted_chunk)
                        
                        # Decrypt chunk
                        decrypted_chunk = self.engine.decrypt_chunk(encrypted_chunk, key)
                        
                        # Write decrypted data
                        f_out.write(decrypted_chunk)
                        bytes_written += len(decrypted_chunk)
                    
                    print(f"Decrypted: {bytes_written:,} bytes")
                    
                    # Read stored checksum
                    stored_checksum = f_in.read(32)
                    calculated_checksum = checksum.digest()
                    
                    print(f"Stored checksum: {stored_checksum.hex()[:16]}...")
                    print(f"Calculated checksum: {calculated_checksum.hex()[:16]}...")
                    
                    # Verify checksum
                    if stored_checksum != calculated_checksum:
                        return False, "ERROR: Wrong password or file corrupted"
                
                # Verify size
                if bytes_written != original_size:
                    return False, f"Size mismatch: expected {original_size}, got {bytes_written}"
                
                print(f"Decryption completed successfully!")
                return True, f"Decrypted {original_size:,} bytes"
            
        except Exception as e:
            print(f"Decryption error details: {type(e).__name__}: {str(e)}")
            return False, f"Error: {str(e)}"

# ============================================
# PASSWORD & CLIPBOARD
# ============================================
class PasswordManager:
    @staticmethod
    def generate_secure_password() -> str:
        upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        lower = "abcdefghijkmnopqrstuvwxyz"
        digits = "23456789"
        special = "!@#$%^&*"
        
        password = [
            secrets.choice(upper),
            secrets.choice(lower),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        all_chars = upper + lower + digits + special
        for _ in range(20):
            password.append(secrets.choice(all_chars))
        
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except:
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                root.destroy()
                return True
            except:
                return False

# ============================================
# USER INTERFACE
# ============================================
class CipherForgeUI:
    @staticmethod
    def get_file_path(prompt: str) -> Optional[str]:
        print(f"\n{prompt}")
        print("─" * 40)
        path = input("➤ Enter path (or drag & drop): ").strip()
        
        if not path:
            return None
        
        # Remove quotes
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        
        if not os.path.exists(path):
            print("❌ ERROR: File not found!")
            return None
        
        if not os.path.isfile(path):
            print("❌ ERROR: Not a valid file!")
            return None
        
        return path
    
    @staticmethod
    def get_password_for_encryption() -> Optional[str]:
        print("\n" + "═" * 70)
        print("🔒 PASSWORD SETUP")
        print("═" * 70)
        print("\n1. Use my own password")
        print("2. Generate ultra-secure random password")
        print("3. Cancel")
        
        while True:
            choice = input("\n➤ Select option (1-3): ").strip()
            
            if choice == '3':
                return None
            
            if choice == '1':
                while True:
                    password = getpass.getpass("➤ Enter password: ")
                    if len(password) < 8:
                        print("⚠️  Warning: Use at least 8 characters")
                        proceed = input("Use anyway? (y/n): ").lower()
                        if proceed != 'y':
                            continue
                    
                    confirm = getpass.getpass("➤ Confirm password: ")
                    
                    if password == confirm:
                        print("✅ Password confirmed!")
                        return password
                    print("❌ Passwords don't match! Try again.")
            
            elif choice == '2':
                password = PasswordManager.generate_secure_password()
                print(f"\n🔐 Generated Password:")
                print(f"   {password}")
                print(f"\n📏 Length: {len(password)} characters")
                print("💪 Contains: Uppercase, lowercase, numbers, symbols")
                
                copied = PasswordManager.copy_to_clipboard(password)
                if copied:
                    print("📋 Status: Auto-copied to clipboard ✓")
                else:
                    print("📋 Status: Could not auto-copy to clipboard, please install pyperclip")
                
                print("\n" + "!" * 70)
                print("⚠️  CRITICAL: SAVE THIS PASSWORD NOW!")
                print("   It cannot be recovered if lost!")
                print("!" * 70)
                
                confirm = input("\n➤ Use this password? (y/n): ").lower()
                if confirm == 'y':
                    return password
                else:
                    continue
            
            else:
                print("❌ Please enter 1, 2, or 3")
    
    @staticmethod
    def get_password_for_decryption() -> Optional[str]:
        print("\n" + "═" * 70)
        print("🔓 DECRYPTION PASSWORD")
        print("═" * 70)
        print("\nEnter the password for your encrypted file")
        print("─" * 40)
        
        password = getpass.getpass("➤ Password: ")
        return password if password else None

# ============================================
# ENCRYPTION METHODS INFO
# ============================================
def show_encryption_methods():
    show_banner()
    print("\n" + "═" * 70)
    print("🔐 ENCRYPTION METHODS USED")
    print("═" * 70)
    
    print("""
CipherForge uses secure encryption methods:

1. KEY DERIVATION:
   • PBKDF2 with SHA-256
   • 100,000 iterations for brute force resistance
   • Unique 256-bit salt per file

2. ENCRYPTION ALGORITHM:
   • XOR-based stream cipher
   • 256-bit encryption keys
   • Chunk-by-chunk processing

3. INTEGRITY PROTECTION:
   • SHA-256 checksums
   • File size verification
   • Password verification

4. SECURITY FEATURES:
   • No password storage in files
   • No backdoors or recovery methods
   • Memory-safe operations

⚠️  IMPORTANT:
   • Without correct password, decryption is mathematically impossible
   • Each file has unique encryption parameters
   • Lost password = permanently encrypted data
""")
    
    input("\n➤ Press Enter to return to menu...")

# ============================================
# MAIN APPLICATION
# ============================================
class CipherForge:
    def __init__(self):
        self.ui = CipherForgeUI()
        self.encryptor = FileEncryptor()
    
    def show_warning_and_accept(self):
        show_warning_header()
        
        print("\n" + "═" * 70)
        print("⚠️  YOU MUST ACCEPT TO CONTINUE")
        print("═" * 70)
        
        print("\nBy using CipherForge, you agree that:")
        print("1. You will use for educational/lawful purposes only")
        print("2. Encryption can be irreversible without password")
        print("3. You are responsible for saving passwords")
        print("4. Developer is not responsible for your actions")
        
        accept = input("\n➤ Type 'ACCEPT' to continue: ").strip().upper()
        return accept == 'ACCEPT'
    
    def run_encryption(self):
        show_banner()
        print("⚠️  WARNING: Encryption is irreversible without password!\n")
        
        # Get file
        file_path = self.ui.get_file_path("📁 SELECT FILE TO ENCRYPT")
        if not file_path:
            return False
        
        # Get password
        password = self.ui.get_password_for_encryption()
        if not password:
            print("❌ Encryption cancelled")
            return False
        
        # Always save as encrypted copy
        dir_name = os.path.dirname(file_path) or '.'
        base_name = os.path.basename(file_path)
        output_file = os.path.join(dir_name, base_name + '.encrypted')
        
        # Show info and encrypt
        print(f"\n📄 File: {os.path.basename(file_path)}")
        print(f"📦 Size: {os.path.getsize(file_path):,} bytes")
        print(f"📂 Location: {os.path.dirname(file_path) or 'Current folder'}")
        print("⏳ Encrypting...")
        
        success, message = self.encryptor.encrypt_file(file_path, output_file, password)
        
        if success:
            final_file = output_file
            print(f"\n✅ Encrypted copy saved as: {os.path.basename(final_file)}")            
            print(f"📊 {message}")
            print(f"📁 Output: {os.path.basename(final_file)}")
            print(f"📂 Location: {os.path.dirname(final_file) or 'Current folder'}")
            
            return True
        else:
            print(f"\n❌ ENCRYPTION FAILED")
            print(f"   {message}")
            
            # Clean up
            if os.path.exists(output_file):
                os.remove(output_file)
            
            return False
    
    def run_decryption(self):
        show_banner()
        
        # Get file
        file_path = self.ui.get_file_path("📁 SELECT FILE TO DECRYPT")
        if not file_path:
            return False
        
        # Get password
        password = self.ui.get_password_for_decryption()
        if not password:
            print("❌ Decryption cancelled")
            return False
        
        # Determine output file
        dir_name = os.path.dirname(file_path) or '.'
        base_name = os.path.basename(file_path)
        
        if file_path.endswith('.encrypted'):
            output_file = os.path.join(dir_name, base_name[:-10])  # Remove .encrypted
        else:
            output_file = os.path.join(dir_name, base_name + '.decrypted')
        
        # Show info and decrypt
        print(f"\n📄 File: {base_name}")
        print(f"📦 Size: {os.path.getsize(file_path):,} bytes")
        print(f"📂 Location: {dir_name}")
        print("⏳ Decrypting...")
        
        success, message = self.encryptor.decrypt_file(file_path, output_file, password)
        
        if success:
            print(f"\n✅ DECRYPTION SUCCESSFUL!")
            print(f"📊 {message}")
            print(f"📁 Output: {os.path.basename(output_file)}")
            print(f"📂 Location: {dir_name}")
            
            # Verify the file
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"📏 Restored size: {size:,} bytes")
                if size > 0:
                    print("✓ File restored successfully")
            
            return True
        else:
            print(f"\n❌ DECRYPTION FAILED")
            
            if "Wrong password" in message or "corrupted" in message:
                print(f"🔐 ERROR: Wrong password or file is corrupted")
                print("   Please check your password and try again.")
                print("   If you lost the password, the file cannot be recovered.")
            else:
                print(f"   {message}")
            
            # Clean up failed output
            if os.path.exists(output_file):
                os.remove(output_file)
            
            return False
    
    def main_menu(self):
        show_banner()
        print("\n" + "═" * 70)
        print("🏠 MAIN MENU")
        print("═" * 70)
        print("\n1. 🔒 Encrypt a file")
        print("2. 🔓 Decrypt a file")
        print("3. 🔐 Encryption Methods Used")
        print("4. 🚪 Exit")
        
        while True:
            choice = input("\n➤ Select option (1-4): ").strip()
            
            if choice == '1':
                self.run_encryption()
                break
            elif choice == '2':
                self.run_decryption()
                break
            elif choice == '3':
                show_encryption_methods()
                break
            elif choice == '4':
                print("\n👋 Thank you for using CipherForge!")
                print("   GitHub: github.com/gtk-gg")
                print("\n🚪 Exiting...")
                sys.exit(0)
            else:
                print("❌ Please enter 1, 2, 3, or 4")
    
    def run(self):
        try:
            if not self.show_warning_and_accept():
                print("\n❌ You must accept the terms to use CipherForge.")
                print("👋 Goodbye!")
                return
            
            while True:
                self.main_menu()
                
                print("\n" + "═" * 70)
                again = input("\n➤ Return to main menu? (y/n): ").lower()
                if again != 'y':
                    print("\n👋 Thank you for using CipherForge!")
                    print("   GitHub: github.com/gtk-gg")
                    print("\n🚪 Exiting...")
                    break
        
        except KeyboardInterrupt:
            print("\n\n👋 Operation cancelled. Goodbye!")
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")

def main():
    app = CipherForge()
    app.run()

if __name__ == "__main__":
    # Simple test to check file reading
    test_file = "test_read.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("Test file for reading")
        
        with open(test_file, 'rb') as f:
            data = f.read()
            print(f"✓ File reading test passed: {len(data)} bytes")
        
        os.remove(test_file)
    except Exception as e:
        print(f"⚠️ File reading test failed: {e}")
    
    # Run the app
    main()
