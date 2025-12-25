#!/usr/bin/env python3
"""
SSH Host Selector
Select from saved SSH hosts and launch the directory browser
"""

import sys
import curses
from typing import List, Dict, Optional
from config_manager import ConfigManager
from ssh_handler import SSHHandler
from ssh_dir_browser import DirectoryBrowser


class HostSelector:
    """Interactive host selection UI"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.hosts = config_manager.get_hosts()
        self.selected_index = 0
        self.scroll_offset = 0
    
    def draw_ui(self, stdscr):
        """Draw the host selection UI"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Header
        header = "SSH Directory Browser - Select Host"
        stdscr.addstr(0, 0, header[:width-1], curses.A_REVERSE | curses.A_BOLD)
        
        # Info line
        if not self.hosts:
            info = "No saved hosts. Press 'n' to add a new host or 'q' to quit."
            stdscr.addstr(2, 2, info[:width-3])
        else:
            info = f"Select a host to connect ({len(self.hosts)} available)"
            stdscr.addstr(2, 2, info[:width-3], curses.A_DIM)
        
        # Help line
        help_text = "↑/↓: Navigate | Enter: Connect | 'n': New host | 'd': Delete | 'q': Quit"
        stdscr.addstr(3, 0, help_text[:width-1], curses.A_DIM)
        
        # Separator
        stdscr.addstr(4, 0, "─" * (width-1))
        
        # Host list
        if self.hosts:
            display_height = height - 7
            
            # Calculate visible range
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index
            elif self.selected_index >= self.scroll_offset + display_height:
                self.scroll_offset = self.selected_index - display_height + 1
            
            # Display hosts
            for i in range(self.scroll_offset, min(len(self.hosts), self.scroll_offset + display_height)):
                y = 5 + i - self.scroll_offset
                host = self.hosts[i]
                
                # Format display
                name = host['name']
                connection = f"{host['username']}@{host['hostname']}:{host.get('port', 22)}"
                display = f"  {name:20} → {connection}"
                
                # Add default path if exists
                if 'default_path' in host:
                    display += f" ({host['default_path']})"
                
                # Highlight selected
                attr = curses.A_REVERSE if i == self.selected_index else curses.A_NORMAL
                
                try:
                    stdscr.addstr(y, 0, display[:width-1], attr)
                except curses.error:
                    pass
        
        # Status bar
        status_y = height - 2
        stdscr.addstr(status_y, 0, "─" * (width-1))
        status = f"Hosts: {len(self.hosts)} | Selected: {self.selected_index + 1}/{len(self.hosts)}" if self.hosts else "No hosts configured"
        stdscr.addstr(status_y + 1, 0, status[:width-1])
        
        stdscr.refresh()
    
    def run(self, stdscr):
        """Main event loop"""
        curses.curs_set(0)
        stdscr.keypad(True)
        
        while True:
            self.draw_ui(stdscr)
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                return None
            elif key == curses.KEY_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1
            elif key == curses.KEY_DOWN:
                if self.selected_index < len(self.hosts) - 1:
                    self.selected_index += 1
            elif key == ord('\n') or key == curses.KEY_ENTER:
                if self.hosts and self.selected_index < len(self.hosts):
                    return self.hosts[self.selected_index]
            elif key == ord('n') or key == ord('N'):
                # Add new host (exit to command line for this)
                return 'NEW_HOST'
            elif key == ord('d') or key == ord('D'):
                # Delete selected host
                if self.hosts and self.selected_index < len(self.hosts):
                    host = self.hosts[self.selected_index]
                    self.config_manager.remove_host(host['name'])
                    self.hosts = self.config_manager.get_hosts()
                    if self.selected_index >= len(self.hosts) and self.selected_index > 0:
                        self.selected_index -= 1


def connect_to_host(host_config: Dict) -> bool:
    """Connect to a host and launch directory browser"""
    print(f"\nConnecting to {host_config['username']}@{host_config['hostname']}:{host_config.get('port', 22)}...")
    
    try:
        ssh = SSHHandler(
            hostname=host_config['hostname'],
            username=host_config['username'],
            port=host_config.get('port', 22),
            key_filename=host_config.get('key_file'),
            use_password=False
        )
        
        if not ssh.connect():
            print("Failed to connect to SSH server")
            return False
        
        print("Connected successfully!")
        
        # Determine start path
        start_path = host_config.get('default_path') or host_config.get('last_path') or '~'
        if start_path == '~':
            home_cmd = "echo $HOME"
            start_path = ssh.execute_command(home_cmd).strip() or "/"
        
        # Launch browser
        browser = DirectoryBrowser(ssh, start_path)
        curses.wrapper(browser.run)
        
        # Save last path
        config = ConfigManager()
        config.update_host_last_path(host_config['name'], browser.current_path)
        
        # Cleanup
        ssh.disconnect()
        print("\nDisconnected. Goodbye!")
        return True
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return False
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


def main():
    """Main entry point for host selector"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SSH Host Selector")
    parser.add_argument('host_name', nargs='?', help='Saved host name to connect to directly')
    args, remaining = parser.parse_known_args()
    
    config = ConfigManager()
    
    # If host name provided, connect directly
    if args.host_name:
        host_config = config.get_host(args.host_name)
        if host_config:
            print(f"Connecting to saved host: {args.host_name}")
            connect_to_host(host_config)
            return
        else:
            print(f"❌ Host '{args.host_name}' not found in saved configurations")
            print("\nAvailable hosts:")
            hosts = config.get_hosts()
            if hosts:
                for host in hosts:
                    print(f"  - {host['name']}")
            else:
                print("  (none)")
            print("\nAdd one with: python save_config.py add")
            sys.exit(1)
    
    # If no hosts configured, show help
    hosts = config.get_hosts()
    if not hosts:
        print("SSH Directory Browser - Host Selector")
        print("=" * 50)
        print("\nNo saved hosts found.")
        print("\nYou can:")
        print("  1. Use the direct connection mode:")
        print("     ./ssh-browse user@hostname")
        print("\n  2. Add a host to configuration:")
        print("     python save_config.py add")
        print("\n  3. Or use the quick add:")
        print("     python save_config.py quick myhost example.com user")
        print("\n  4. Edit the config file manually:")
        print(f"     {config.config_path}")
        sys.exit(0)
    
    # Show host selector
    try:
        selector = HostSelector(config)
        selected = curses.wrapper(selector.run)
        
        if selected is None:
            print("Cancelled.")
            sys.exit(0)
        elif selected == 'NEW_HOST':
            print("\nTo add a new host, use:")
            print("  python save_config.py add")
            print("Or edit the config file:")
            print(f"  {config.config_path}")
            sys.exit(0)
        else:
            # Connect to selected host
            connect_to_host(selected)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
