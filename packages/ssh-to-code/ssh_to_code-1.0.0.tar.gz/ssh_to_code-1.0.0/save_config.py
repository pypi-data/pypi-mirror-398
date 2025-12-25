#!/usr/bin/env python3
"""
Interactive SSH Configuration Manager
Easily save and manage frequently used SSH connections
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def add_host_interactive():
    """Interactive host addition"""
    print_header("Add New SSH Host Configuration")
    
    config = ConfigManager()
    
    # Get host details
    print("Enter the SSH connection details:\n")
    
    name = input("Host nickname (e.g., 'my-ec2', 'production'): ").strip()
    if not name:
        print("❌ Name is required")
        return False
    
    # Check if already exists
    existing = config.get_host(name)
    if existing:
        print(f"\n⚠️  Host '{name}' already exists!")
        print(f"   Current config: {existing['username']}@{existing['hostname']}")
        overwrite = input("   Overwrite? (yes/no): ").strip().lower()
        if overwrite != 'yes':
            print("Cancelled.")
            return False
        config.remove_host(name)
    
    hostname = input("Hostname or IP (e.g., 'example.com', '1.2.3.4'): ").strip()
    if not hostname:
        print("❌ Hostname is required")
        return False
    
    username = input("Username (e.g., 'ubuntu', 'ec2-user', 'root'): ").strip()
    if not username:
        print("❌ Username is required")
        return False
    
    port_input = input("Port (default: 22): ").strip()
    port = int(port_input) if port_input else 22
    
    key_file = input("Path to SSH key file (optional, press Enter to skip): ").strip()
    if key_file:
        key_file = os.path.expanduser(key_file)
        if not os.path.exists(key_file):
            print(f"⚠️  Warning: Key file not found: {key_file}")
            proceed = input("   Save anyway? (yes/no): ").strip().lower()
            if proceed != 'yes':
                return False
    else:
        key_file = None
    
    default_path = input("Default starting directory (optional, press Enter to skip): ").strip()
    if not default_path:
        default_path = None
    
    # Confirm
    print("\n" + "-" * 60)
    print("Configuration Summary:")
    print("-" * 60)
    print(f"  Name:         {name}")
    print(f"  Connection:   {username}@{hostname}:{port}")
    if key_file:
        print(f"  Key file:     {key_file}")
    if default_path:
        print(f"  Start path:   {default_path}")
    print("-" * 60)
    
    confirm = input("\nSave this configuration? (yes/no): ").strip().lower()
    if confirm == 'yes':
        success = config.add_host(
            name=name,
            hostname=hostname,
            username=username,
            port=port,
            key_file=key_file,
            default_path=default_path
        )
        
        if success:
            print(f"\n✅ Configuration '{name}' saved successfully!")
            print(f"\nYou can now connect with:")
            print(f"  ./ssh-browse {name}")
            print(f"  # or")
            print(f"  python ssh_dir_browser.py {username}@{hostname} -p {port}", end="")
            if key_file:
                print(f" -i {key_file}", end="")
            print()
            return True
        else:
            print("\n❌ Failed to save configuration")
            return False
    else:
        print("Cancelled.")
        return False


def list_hosts():
    """List all saved hosts"""
    print_header("Saved SSH Host Configurations")
    
    config = ConfigManager()
    hosts = config.get_hosts()
    
    if not hosts:
        print("No saved configurations found.\n")
        print("💡 Add one with: python save_config.py add")
        return
    
    print(f"Found {len(hosts)} saved configuration(s):\n")
    
    for i, host in enumerate(hosts, 1):
        print(f"{i}. {host['name']}")
        print(f"   Connection: {host['username']}@{host['hostname']}:{host.get('port', 22)}")
        if 'key_file' in host:
            print(f"   Key file:   {host['key_file']}")
        if 'default_path' in host:
            print(f"   Start path: {host['default_path']}")
        if 'last_path' in host:
            print(f"   Last used:  {host['last_path']}")
        print()
    
    print("Connect with: ./ssh-browse <name>")
    print(f"Config file: {config.config_path}\n")


def remove_host_interactive():
    """Interactive host removal"""
    print_header("Remove SSH Host Configuration")
    
    config = ConfigManager()
    hosts = config.get_hosts()
    
    if not hosts:
        print("No saved configurations found.\n")
        return
    
    print("Saved configurations:\n")
    for i, host in enumerate(hosts, 1):
        print(f"{i}. {host['name']} ({host['username']}@{host['hostname']})")
    
    print()
    choice = input("Enter name or number to remove (or 'cancel'): ").strip()
    
    if choice.lower() == 'cancel':
        print("Cancelled.")
        return
    
    # Try as number first
    host_to_remove = None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(hosts):
            host_to_remove = hosts[idx]['name']
    except ValueError:
        host_to_remove = choice
    
    if host_to_remove:
        confirm = input(f"Remove '{host_to_remove}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            if config.remove_host(host_to_remove):
                print(f"✅ Removed '{host_to_remove}'")
            else:
                print(f"❌ Host '{host_to_remove}' not found")
        else:
            print("Cancelled.")


def quick_add_from_command():
    """Quick add from command line arguments"""
    if len(sys.argv) < 4:
        print("Usage: python save_config.py quick <name> <user@host> [options]")
        print("\nOptions:")
        print("  -i <key_file>        Path to SSH key")
        print("  -p <port>            SSH port (default: 22)")
        print("  --path <dir>         Default starting directory")
        print("\nExample:")
        print("  python save_config.py quick myserver ubuntu@example.com -i ~/key.pem --path /var/www")
        return
    
    name = sys.argv[2]
    user_host = sys.argv[3]
    
    if '@' not in user_host:
        print("❌ Invalid format. Use: user@hostname")
        return
    
    username, hostname = user_host.split('@', 1)
    
    # Parse options
    port = 22
    key_file = None
    default_path = None
    
    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == '-i' and i + 1 < len(sys.argv):
            key_file = os.path.expanduser(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '-p' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--path' and i + 1 < len(sys.argv):
            default_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    config = ConfigManager()
    
    if config.add_host(name, hostname, username, port, key_file, default_path):
        print(f"✅ Configuration '{name}' saved!")
        print(f"\nConnect with: ./ssh-browse {name}")
    else:
        print(f"❌ Failed to save configuration")


def show_help():
    """Show help message"""
    print("""
SSH Directory Browser - Configuration Manager
==============================================

USAGE:
  python save_config.py [command]

COMMANDS:
  add, a              Add new host configuration (interactive)
  list, ls, l         List all saved configurations
  remove, rm, r       Remove a host configuration
  quick <name> ...    Quick add from command line
  help, h             Show this help message

EXAMPLES:

1. Interactive mode (recommended for first time):
   python save_config.py add

2. Quick add from command line:
   python save_config.py quick myec2 ubuntu@ec2-1-2-3-4.compute.amazonaws.com -i ~/aws-key.pem

3. List all saved hosts:
   python save_config.py list

4. Remove a host:
   python save_config.py remove

5. After saving, connect with:
   ./ssh-browse myec2

CONFIGURATION FILE:
  Location: ~/.ssh-dir-browser.json
  Format:   JSON

DIRECT EDITING:
  You can also edit the config file directly:
  nano ~/.ssh-dir-browser.json

  Example format:
  {
    "version": "1.0",
    "hosts": [
      {
        "name": "myserver",
        "hostname": "example.com",
        "username": "user",
        "port": 22,
        "key_file": "~/.ssh/id_rsa",
        "default_path": "/var/www"
      }
    ]
  }
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        # Interactive mode by default
        while True:
            print("\n" + "=" * 60)
            print("  SSH Directory Browser - Configuration Manager")
            print("=" * 60)
            print("\n1. Add new host")
            print("2. List saved hosts")
            print("3. Remove host")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                add_host_interactive()
            elif choice == '2':
                list_hosts()
            elif choice == '3':
                remove_host_interactive()
            elif choice == '4':
                print("\nGoodbye!")
                break
            else:
                print("Invalid option")
        return
    
    command = sys.argv[1].lower()
    
    if command in ['add', 'a']:
        add_host_interactive()
    elif command in ['list', 'ls', 'l']:
        list_hosts()
    elif command in ['remove', 'rm', 'r']:
        remove_host_interactive()
    elif command == 'quick':
        quick_add_from_command()
    elif command in ['help', 'h', '--help', '-h']:
        show_help()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python save_config.py help' for usage information")


if __name__ == "__main__":
    main()
