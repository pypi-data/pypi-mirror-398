#!/usr/bin/env python3
"""
VS Code Remote Integration
Helper functions for opening directories in VS Code via Remote-SSH
"""

import subprocess
import json
import os
from typing import Optional, Tuple


class VSCodeRemote:
    """Handle VS Code Remote-SSH integration"""
    
    @staticmethod
    def is_vscode_installed() -> bool:
        """Check if VS Code CLI is available"""
        try:
            result = subprocess.run(['code', '--version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def is_remote_ssh_installed() -> bool:
        """Check if Remote-SSH extension is installed"""
        try:
            result = subprocess.run(['code', '--list-extensions'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                extensions = result.stdout.lower()
                return 'ms-vscode-remote.remote-ssh' in extensions
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def get_ssh_config_hosts() -> list:
        """Get configured SSH hosts from ~/.ssh/config"""
        ssh_config_path = os.path.expanduser('~/.ssh/config')
        hosts = []
        
        if not os.path.exists(ssh_config_path):
            return hosts
        
        try:
            with open(ssh_config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('Host ') and not '*' in line:
                        host = line.split('Host ')[1].strip()
                        hosts.append(host)
        except Exception:
            pass
        
        return hosts
    
    @staticmethod
    def open_remote_directory(hostname: str, username: str, port: int, 
                             remote_path: str, new_window: bool = False) -> Tuple[bool, str]:
        """
        Open a remote directory in VS Code
        
        Args:
            hostname: SSH hostname
            username: SSH username
            port: SSH port
            remote_path: Remote directory path
            new_window: Open in new window
        
        Returns:
            Tuple of (success, message)
        """
        if not VSCodeRemote.is_vscode_installed():
            return False, "VS Code CLI not found. Make sure 'code' is in your PATH."
        
        if not VSCodeRemote.is_remote_ssh_installed():
            return False, "Remote-SSH extension not installed. Install it from VS Code marketplace."
        
        try:
            # Format: ssh-remote+user@host:port
            ssh_target = f"{username}@{hostname}"
            if port != 22:
                ssh_target += f":{port}"
            
            # Build command
            cmd = ['code']
            if new_window:
                cmd.append('--new-window')
            cmd.extend(['--remote', f'ssh-remote+{ssh_target}', remote_path])
            
            # Execute command
            subprocess.Popen(cmd, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
            
            return True, f"Opening {remote_path} on {ssh_target} in VS Code..."
            
        except Exception as e:
            return False, f"Failed to open VS Code: {str(e)}"
    
    @staticmethod
    def add_ssh_host_to_config(hostname: str, username: str, port: int = 22, 
                               key_file: Optional[str] = None, 
                               alias: Optional[str] = None) -> Tuple[bool, str]:
        """
        Add SSH host configuration to ~/.ssh/config
        
        Args:
            hostname: SSH hostname
            username: SSH username
            port: SSH port
            key_file: Path to private key file
            alias: Host alias (optional)
        
        Returns:
            Tuple of (success, message)
        """
        ssh_config_path = os.path.expanduser('~/.ssh/config')
        ssh_dir = os.path.dirname(ssh_config_path)
        
        # Create .ssh directory if it doesn't exist
        if not os.path.exists(ssh_dir):
            try:
                os.makedirs(ssh_dir, mode=0o700)
            except Exception as e:
                return False, f"Failed to create .ssh directory: {str(e)}"
        
        # Determine host alias
        host_alias = alias or f"{username}@{hostname}"
        
        # Build configuration entry
        config_entry = f"\n# Added by ssh-dir-browser\n"
        config_entry += f"Host {host_alias}\n"
        config_entry += f"    HostName {hostname}\n"
        config_entry += f"    User {username}\n"
        if port != 22:
            config_entry += f"    Port {port}\n"
        if key_file:
            config_entry += f"    IdentityFile {key_file}\n"
        config_entry += "\n"
        
        try:
            # Check if host already exists
            if os.path.exists(ssh_config_path):
                with open(ssh_config_path, 'r') as f:
                    content = f.read()
                    if f"Host {host_alias}" in content:
                        return False, f"Host '{host_alias}' already exists in SSH config"
            
            # Append configuration
            with open(ssh_config_path, 'a') as f:
                f.write(config_entry)
            
            return True, f"Added '{host_alias}' to SSH config"
            
        except Exception as e:
            return False, f"Failed to update SSH config: {str(e)}"


def main():
    """Test VS Code integration"""
    print("VS Code Remote Integration Test")
    print("=" * 50)
    
    print(f"VS Code installed: {VSCodeRemote.is_vscode_installed()}")
    print(f"Remote-SSH installed: {VSCodeRemote.is_remote_ssh_installed()}")
    
    hosts = VSCodeRemote.get_ssh_config_hosts()
    print(f"\nConfigured SSH hosts: {len(hosts)}")
    for host in hosts[:5]:  # Show first 5
        print(f"  - {host}")
    
    if len(hosts) > 5:
        print(f"  ... and {len(hosts) - 5} more")


if __name__ == "__main__":
    main()
