#!/usr/bin/env python3
"""
SSH Connection Handler
Manages SSH connections and remote command execution
"""

import paramiko
import getpass
import os
import sys
from typing import Optional


class SSHHandler:
    """Handle SSH connections and command execution"""
    
    def __init__(self, hostname: str, username: str, port: int = 22, 
                 key_filename: Optional[str] = None, use_password: bool = False,
                 key_passphrase: Optional[str] = None):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.key_filename = key_filename
        self.use_password = use_password
        self.key_passphrase = key_passphrase
        self.client: Optional[paramiko.SSHClient] = None
        self.connected = False
    
    def _load_private_key(self, key_path: str, passphrase: Optional[str] = None):
        """Load and decrypt private key file"""
        key_path = os.path.expanduser(key_path)
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Key file not found: {key_path}")
        
        # Try different key types (DSS removed in Paramiko 3.0+)
        key_types = [
            ('RSA', paramiko.RSAKey),
            ('Ed25519', paramiko.Ed25519Key),
            ('ECDSA', paramiko.ECDSAKey),
        ]
        
        # Add DSS support if available (Paramiko < 3.0)
        if hasattr(paramiko, 'DSSKey'):
            key_types.append(('DSS', paramiko.DSSKey))
        
        for key_name, key_class in key_types:
            try:
                # Try loading with passphrase if provided
                if passphrase:
                    return key_class.from_private_key_file(key_path, password=passphrase)
                else:
                    return key_class.from_private_key_file(key_path)
            except paramiko.ssh_exception.PasswordRequiredException:
                # Key is encrypted, need passphrase
                if passphrase is None:
                    # This is expected for encrypted keys without passphrase
                    raise
                # Continue to next key type if passphrase didn't work
                continue
            except paramiko.ssh_exception.SSHException:
                # Not this key type, try next
                continue
            except (AttributeError, Exception):
                # Other error (including missing key class), try next key type
                continue
        
        # If we get here, couldn't load the key
        raise paramiko.ssh_exception.SSHException(f"Unable to load key from {key_path}")
    
    def _try_key_authentication(self, connect_kwargs: dict, key_path: str) -> bool:
        """Try to authenticate with a key file, handling encrypted keys"""
        try:
            # First try without passphrase
            pkey = self._load_private_key(key_path)
            connect_kwargs['pkey'] = pkey
            return True
        except paramiko.ssh_exception.PasswordRequiredException:
            # Key is encrypted, prompt for passphrase
            print(f"\n🔐 Key file is encrypted: {key_path}")
            
            # Try up to 3 times
            for attempt in range(3):
                try:
                    passphrase = getpass.getpass(f"Enter passphrase for key (attempt {attempt + 1}/3): ")
                    
                    if not passphrase:
                        print("Passphrase cannot be empty for encrypted keys")
                        continue
                    
                    pkey = self._load_private_key(key_path, passphrase)
                    connect_kwargs['pkey'] = pkey
                    print("✓ Key decrypted successfully")
                    return True
                    
                except paramiko.ssh_exception.SSHException:
                    if attempt < 2:
                        print("✗ Incorrect passphrase, try again")
                    else:
                        print("✗ Failed to decrypt key after 3 attempts")
                        return False
            return False
        except Exception as e:
            print(f"Warning: Could not load key {key_path}: {str(e)}")
            return False
    
    def connect(self) -> bool:
        """Establish SSH connection with support for encrypted keys"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.hostname,
                'username': self.username,
                'port': self.port,
                'timeout': 10,
            }
            
            key_auth_success = False
            
            # Try key-based authentication first
            if self.key_filename:
                key_path = os.path.expanduser(self.key_filename)
                if not os.path.exists(key_path):
                    print(f"✗ Key file not found: {key_path}")
                    print("\nOptions:")
                    print("  1. Check the path to your PEM/key file")
                    print("  2. Use password authentication with --password flag")
                    print("  3. Use SSH agent authentication (ssh-add your key)")
                else:
                    print(f"🔑 Using key file: {key_path}")
                    key_auth_success = self._try_key_authentication(connect_kwargs, key_path)
                    
                    if not key_auth_success:
                        print("\n💡 Options:")
                        print("  1. Try password authentication (will prompt below)")
                        print("  2. Check if you have the correct passphrase")
                        print("  3. Add key to SSH agent: ssh-add", key_path)
            else:
                # Try default SSH keys
                default_keys = [
                    os.path.expanduser('~/.ssh/id_rsa'),
                    os.path.expanduser('~/.ssh/id_ed25519'),
                    os.path.expanduser('~/.ssh/id_ecdsa'),
                ]
                
                existing_keys = [k for k in default_keys if os.path.exists(k)]
                if existing_keys:
                    print(f"🔍 Trying default SSH keys...")
                    for key_path in existing_keys:
                        print(f"  Trying: {key_path}")
                        if self._try_key_authentication(connect_kwargs, key_path):
                            key_auth_success = True
                            break
                
                if not key_auth_success:
                    # Fall back to SSH agent
                    connect_kwargs['look_for_keys'] = False
                    connect_kwargs['allow_agent'] = True
            
            # Password authentication
            if self.use_password or (not key_auth_success and not connect_kwargs.get('pkey')):
                if not self.use_password:
                    print("\n🔐 Key authentication not available. Trying password authentication...")
                
                password = getpass.getpass(f"Password for {self.username}@{self.hostname}: ")
                connect_kwargs['password'] = password
                connect_kwargs['look_for_keys'] = False
                connect_kwargs['allow_agent'] = False
                # Remove pkey if we're using password
                connect_kwargs.pop('pkey', None)
            
            try:
                self.client.connect(**connect_kwargs)
                self.connected = True
                print("✓ Connected successfully!")
                return True
                
            except paramiko.AuthenticationException as e:
                print(f"\n✗ Authentication failed: {str(e)}")
                print("\n🔧 Troubleshooting:")
                print("  1. Check your username and hostname")
                print("  2. Verify key file has correct permissions (chmod 600)")
                print("  3. Ensure your key is authorized on the server")
                print("  4. Try: ssh -v " + f"{self.username}@{self.hostname}" + " (for debug info)")
                print("  5. Add key to SSH agent: ssh-add /path/to/key")
                return False
                    
        except paramiko.AuthenticationException as e:
            print(f"\n✗ Authentication failed: {str(e)}")
            return False
        except paramiko.SSHException as e:
            print(f"\n✗ SSH connection error: {str(e)}")
            return False
        except Exception as e:
            print(f"\n✗ Connection error: {str(e)}")
            return False
    
    def execute_command(self, command: str, timeout: int = 10) -> str:
        """Execute a command on the remote server and return output"""
        if not self.connected or not self.client:
            raise RuntimeError("Not connected to SSH server")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            if exit_code != 0 and error:
                raise RuntimeError(f"Command failed: {error}")
            
            return output
            
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {str(e)}")
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.connected = False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
