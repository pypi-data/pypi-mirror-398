#!/usr/bin/env python3
"""
SSH Directory Browser with VS Code Integration
Browse remote directories via SSH and open them in VS Code
"""

import curses
import sys
import subprocess
import os
from typing import List, Optional, Tuple
import argparse


class DirectoryBrowser:
    """Interactive terminal-based directory browser"""
    
    def __init__(self, ssh_handler, start_path: str = "/"):
        self.ssh_handler = ssh_handler
        self.current_path = start_path
        self.selected_index = 0
        self.scroll_offset = 0
        self.items: List[Tuple[str, str]] = []  # (name, type)
        self.status_message = ""
        
    def get_directory_contents(self) -> List[Tuple[str, str]]:
        """Get directory contents from remote server"""
        try:
            # List directory with details (-F adds indicators for file types)
            cmd = f"ls -1F '{self.current_path}'"
            output = self.ssh_handler.execute_command(cmd)
            
            if not output:
                return []
            
            items = []
            # Add parent directory option if not at root
            if self.current_path != "/":
                items.append(("..", "dir"))
            
            for line in output.strip().split('\n'):
                if not line:
                    continue
                    
                # Check file type indicator
                if line.endswith('/'):
                    items.append((line[:-1], "dir"))
                elif line.endswith('*'):
                    items.append((line[:-1], "exec"))
                elif line.endswith('@'):
                    items.append((line[:-1], "link"))
                else:
                    items.append((line, "file"))
            
            return items
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            return []
    
    def navigate_to(self, item_name: str):
        """Navigate to a directory"""
        if item_name == "..":
            # Go to parent directory
            self.current_path = os.path.dirname(self.current_path)
            if not self.current_path:
                self.current_path = "/"
        else:
            # Go to subdirectory
            if self.current_path == "/":
                self.current_path = f"/{item_name}"
            else:
                self.current_path = f"{self.current_path}/{item_name}"
        
        self.selected_index = 0
        self.scroll_offset = 0
        self.items = self.get_directory_contents()
    
    def create_folder(self, stdscr) -> Optional[str]:
        """Prompt user to create a new folder"""
        height, width = stdscr.getmaxyx()
        
        # Create input window
        input_win = curses.newwin(5, min(60, width - 4), height // 2 - 2, (width - min(60, width - 4)) // 2)
        input_win.box()
        input_win.addstr(1, 2, "Create New Folder:", curses.A_BOLD)
        input_win.addstr(2, 2, "Name: ")
        input_win.refresh()
        
        # Enable cursor for input
        curses.curs_set(1)
        curses.echo()
        
        # Get folder name
        folder_name = ""
        try:
            folder_name = input_win.getstr(2, 8, 40).decode('utf-8').strip()
        except:
            pass
        finally:
            curses.noecho()
            curses.curs_set(0)
        
        if not folder_name:
            return None
        
        # Validate folder name
        if '/' in folder_name or folder_name in ['.', '..']:
            return f"Invalid folder name: {folder_name}"
        
        # Create folder on remote server
        try:
            new_path = os.path.join(self.current_path, folder_name)
            cmd = f"mkdir -p '{new_path}'"
            self.ssh_handler.execute_command(cmd)
            return f"Created folder: {folder_name}"
        except Exception as e:
            return f"Error creating folder: {str(e)}"
    
    def open_in_vscode(self):
        """Open current directory in VS Code"""
        try:
            host = self.ssh_handler.hostname
            user = self.ssh_handler.username
            port = self.ssh_handler.port
            
            # VS Code Remote-SSH URI format
            # vscode://vscode-remote/ssh-remote+user@host:port/path
            remote_uri = f"vscode://vscode-remote/ssh-remote+{user}@{host}"
            if port != 22:
                remote_uri += f":{port}"
            remote_uri += self.current_path
            
            # Open VS Code
            subprocess.Popen(['code', '--remote', f'ssh-remote+{user}@{host}', self.current_path],
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            return True, f"Opening {self.current_path} in VS Code..."
        except Exception as e:
            return False, f"Error opening VS Code: {str(e)}"
    
    def draw_ui(self, stdscr):
        """Draw the terminal UI"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Header
        header = f"SSH Directory Browser - {self.ssh_handler.username}@{self.ssh_handler.hostname}"
        stdscr.addstr(0, 0, header[:width-1], curses.A_REVERSE)
        
        # Current path
        path_line = f"Path: {self.current_path}"
        stdscr.addstr(1, 0, path_line[:width-1], curses.A_BOLD)
        
        # Help line
        help_text = "↑/↓: Navigate | Enter: Open | 'o': VS Code | 'n': New Folder | 'r': Refresh | 'q': Quit"
        stdscr.addstr(2, 0, help_text[:width-1], curses.A_DIM)
        
        # Separator
        stdscr.addstr(3, 0, "─" * (width-1))
        
        # Directory contents
        display_height = height - 6  # Reserve space for header, footer, and status
        
        # Calculate visible range
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + display_height:
            self.scroll_offset = self.selected_index - display_height + 1
        
        # Display items
        for i in range(self.scroll_offset, min(len(self.items), self.scroll_offset + display_height)):
            y = 4 + i - self.scroll_offset
            name, item_type = self.items[i]
            
            # Format display
            if item_type == "dir":
                display = f"📁 {name}/"
                attr = curses.A_BOLD
            elif item_type == "exec":
                display = f"⚙️  {name}*"
                attr = curses.A_NORMAL
            elif item_type == "link":
                display = f"🔗 {name}@"
                attr = curses.A_DIM
            else:
                display = f"📄 {name}"
                attr = curses.A_NORMAL
            
            # Highlight selected item
            if i == self.selected_index:
                attr |= curses.A_REVERSE
            
            try:
                stdscr.addstr(y, 2, display[:width-3], attr)
            except curses.error:
                pass  # Ignore errors from writing to last line
        
        # Status bar
        status_y = height - 2
        stdscr.addstr(status_y, 0, "─" * (width-1))
        
        if self.status_message:
            status = self.status_message[:width-1]
            stdscr.addstr(status_y + 1, 0, status, curses.A_BOLD)
        else:
            info = f"Items: {len(self.items)} | Selected: {self.selected_index + 1}/{len(self.items)}"
            stdscr.addstr(status_y + 1, 0, info[:width-1])
        
        stdscr.refresh()
    
    def run(self, stdscr):
        """Main event loop"""
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)
        
        # Initialize colors if available
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        
        # Load initial directory
        self.items = self.get_directory_contents()
        
        while True:
            self.draw_ui(stdscr)
            
            # Get user input
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == curses.KEY_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    self.status_message = ""
            elif key == curses.KEY_DOWN:
                if self.selected_index < len(self.items) - 1:
                    self.selected_index += 1
                    self.status_message = ""
            elif key == ord('\n') or key == curses.KEY_ENTER:
                # Enter selected item
                if self.items and self.selected_index < len(self.items):
                    name, item_type = self.items[self.selected_index]
                    if item_type == "dir" or name == "..":
                        self.navigate_to(name)
                        self.status_message = ""
                    else:
                        self.status_message = f"'{name}' is not a directory"
            elif key == ord('o') or key == ord('O'):
                # Open in VS Code
                success, message = self.open_in_vscode()
                self.status_message = message
                if success:
                    # Wait a moment to show the message, then exit
                    stdscr.timeout(2000)
                    stdscr.getch()
                    break
            elif key == ord('h') or key == ord('H'):
                # Go to home directory
                home_cmd = "echo $HOME"
                home_path = self.ssh_handler.execute_command(home_cmd).strip()
                if home_path:
                    self.current_path = home_path
                    self.selected_index = 0
                    self.scroll_offset = 0
                    self.items = self.get_directory_contents()
                    self.status_message = f"Navigated to home: {home_path}"
            elif key == ord('r') or key == ord('R'):
                # Refresh
                self.items = self.get_directory_contents()
                self.status_message = "Refreshed"
            elif key == ord('n') or key == ord('N'):
                # Create new folder
                result = self.create_folder(stdscr)
                if result:
                    self.status_message = result
                    # Refresh directory listing
                    self.items = self.get_directory_contents()
                else:
                    self.status_message = "Folder creation cancelled"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SSH Directory Browser - Browse remote directories and open in VS Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s user@hostname
  %(prog)s user@hostname -p 2222
  %(prog)s user@hostname --start-path /var/www
  %(prog)s user@hostname -i ~/.ssh/id_rsa
        """
    )
    parser.add_argument('host', help='SSH host in format user@hostname')
    parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('-i', '--identity', help='SSH private key file')
    parser.add_argument('--start-path', default='~', help='Starting directory (default: ~)')
    parser.add_argument('--password', action='store_true', 
                       help='Prompt for password authentication')
    
    args = parser.parse_args()
    
    # Parse user@host
    if '@' not in args.host:
        print("Error: Host must be in format user@hostname")
        sys.exit(1)
    
    username, hostname = args.host.split('@', 1)
    
    # Import SSH handler
    try:
        from ssh_handler import SSHHandler
    except ImportError:
        print("Error: ssh_handler module not found")
        print("Make sure ssh_handler.py is in the same directory")
        sys.exit(1)
    
    # Connect to SSH
    print(f"Connecting to {username}@{hostname}:{args.port}...")
    
    try:
        ssh = SSHHandler(
            hostname=hostname,
            username=username,
            port=args.port,
            key_filename=args.identity,
            use_password=args.password
        )
        
        if not ssh.connect():
            print("Failed to connect to SSH server")
            sys.exit(1)
        
        print("Connected successfully!")
        
        # Resolve start path
        start_path = args.start_path
        if start_path == '~':
            home_cmd = "echo $HOME"
            start_path = ssh.execute_command(home_cmd).strip() or "/"
        
        # Start the browser
        browser = DirectoryBrowser(ssh, start_path)
        curses.wrapper(browser.run)
        
        # Cleanup
        ssh.disconnect()
        print("\nDisconnected. Goodbye!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
