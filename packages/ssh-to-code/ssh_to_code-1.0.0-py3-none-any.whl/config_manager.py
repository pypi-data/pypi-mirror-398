#!/usr/bin/env python3
"""
Configuration Manager
Handle loading and saving SSH host configurations
"""

import json
import os
from typing import Dict, List, Optional


class ConfigManager:
    """Manage SSH host configurations"""
    
    DEFAULT_CONFIG_PATH = os.path.expanduser('~/.ssh-dir-browser.json')
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            return {
                'version': '1.0',
                'hosts': [],
                'preferences': {
                    'default_start_path': '~',
                    'save_last_path': True,
                }
            }
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return {'version': '1.0', 'hosts': [], 'preferences': {}}
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            # Create directory if needed
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_hosts(self) -> List[Dict]:
        """Get list of configured hosts"""
        return self.config.get('hosts', [])
    
    def add_host(self, name: str, hostname: str, username: str, 
                 port: int = 22, key_file: Optional[str] = None,
                 default_path: Optional[str] = None) -> bool:
        """Add a new host configuration"""
        # Check if host already exists
        for host in self.config['hosts']:
            if host['name'] == name:
                print(f"Host '{name}' already exists")
                return False
        
        host_config = {
            'name': name,
            'hostname': hostname,
            'username': username,
            'port': port,
        }
        
        if key_file:
            host_config['key_file'] = key_file
        if default_path:
            host_config['default_path'] = default_path
        
        self.config['hosts'].append(host_config)
        return self.save_config()
    
    def remove_host(self, name: str) -> bool:
        """Remove a host configuration"""
        original_len = len(self.config['hosts'])
        self.config['hosts'] = [h for h in self.config['hosts'] if h['name'] != name]
        
        if len(self.config['hosts']) < original_len:
            return self.save_config()
        return False
    
    def get_host(self, name: str) -> Optional[Dict]:
        """Get a specific host configuration"""
        for host in self.config['hosts']:
            if host['name'] == name:
                return host
        return None
    
    def update_host_last_path(self, name: str, path: str) -> bool:
        """Update the last visited path for a host"""
        for host in self.config['hosts']:
            if host['name'] == name:
                host['last_path'] = path
                return self.save_config()
        return False
    
    def get_preference(self, key: str, default=None):
        """Get a preference value"""
        return self.config.get('preferences', {}).get(key, default)
    
    def set_preference(self, key: str, value) -> bool:
        """Set a preference value"""
        if 'preferences' not in self.config:
            self.config['preferences'] = {}
        self.config['preferences'][key] = value
        return self.save_config()


def main():
    """Test configuration manager"""
    config = ConfigManager()
    
    print("SSH Directory Browser - Configuration Manager")
    print("=" * 50)
    
    # List hosts
    hosts = config.get_hosts()
    print(f"\nConfigured hosts: {len(hosts)}")
    for host in hosts:
        print(f"  - {host['name']}: {host['username']}@{host['hostname']}:{host.get('port', 22)}")
    
    # Show preferences
    print(f"\nPreferences:")
    prefs = config.config.get('preferences', {})
    for key, value in prefs.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
