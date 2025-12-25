#!/usr/bin/env python3
"""
ssh-channel-receive
Terminal proxy that intercepts OSC 52 sequences and routes by message name
"""

import sys
import os
import subprocess
import re
import select
import termios
import tty
import argparse
import base64
from pathlib import Path

class MessageRouter:
    
    def __init__(self, config_path=None):
        self.config_path = config_path or Path.home() / '.config' / 'ssh-channel.conf'
        self.handlers = {}
        self.load_config()
        
        # OSC 52 pattern only: ESC ] 52 ; c ; <base64_data> BEL|ST
        self.osc52_pattern = re.compile(rb'\x1b\]52;c;([^\x07\x1b]*?)(?:\x07|\x1b\\)', re.DOTALL)
    
    def load_config(self):
        """Load message name to handler mapping"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Format: message_name:command:passthrough
                            parts = line.split(':')
                            if len(parts) >= 2:
                                msg_name = parts[0]
                                command = parts[1]  
                                passthrough = parts[2].lower() == 'true' if len(parts) > 2 else False
                                self.handlers[msg_name] = {
                                    'command': command,
                                    'passthrough': passthrough
                                }
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
    
    def handle_named_message(self, msg_name, msg_data):
        """Handle a named message"""
        handler_config = self.handlers.get(msg_name, {})
        
        # Run handler command if configured
        if handler_config.get('command'):
            try:
                # Run as shell command to support pipes, redirects, etc.
                subprocess.run(
                    handler_config['command'],
                    input=msg_data,
                    text=True,
                    shell=True,
                    check=False
                )
            except Exception as e:
                print(f"Error running handler for {msg_name}: {e}", file=sys.stderr)
        else:
            # Default: just print to stderr  
            print(f"No handler for '{msg_name}': {msg_data}", file=sys.stderr)
        
        # Return whether to pass through to terminal (always false for OSC 52)
        return handler_config.get('passthrough', False)
    
    def process_output(self, data):
        """Process command output, intercepting OSC 52 sequences"""
        output = b''
        pos = 0
        
        for match in self.osc52_pattern.finditer(data):
            # Add everything before the OSC sequence
            output += data[pos:match.start()]
            
            # Decode the base64 data
            b64_data = match.group(1).decode('utf-8', errors='ignore')
            try:
                decoded = base64.b64decode(b64_data).decode('utf-8')
                
                # Parse message format: name:data
                if ':' in decoded:
                    msg_name, msg_data = decoded.split(':', 1)
                    passthrough = self.handle_named_message(msg_name, msg_data)
                else:
                    # No name prefix, treat as raw clipboard
                    passthrough = self.handle_named_message('clipboard', decoded)
                    
            except Exception as e:
                print(f"Error decoding OSC 52 data: {e}", file=sys.stderr)
                passthrough = True
            
            # Include sequence in output if passthrough is enabled
            if passthrough:
                output += match.group(0)
            
            pos = match.end()
        
        # Add any remaining data after last match
        output += data[pos:]
        return output
    
    def run_command(self, command):
        """Run command with OSC 52 message routing"""
        try:
            # Save original terminal settings
            old_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
            
            # Start the command
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            
            while True:
                # Use select to handle both stdin and process output
                ready, _, _ = select.select([sys.stdin, process.stdout], [], [], 0.1)
                
                # Forward input from stdin to process
                if sys.stdin in ready:
                    try:
                        char = os.read(sys.stdin.fileno(), 1)
                        process.stdin.write(char)
                        process.stdin.flush()
                    except:
                        break
                
                # Process output from command
                if process.stdout in ready:
                    data = process.stdout.read(4096)
                    if not data:
                        break
                    
                    # Intercept and route OSC 52 messages
                    processed_data = self.process_output(data)
                    
                    # Send to terminal
                    sys.stdout.buffer.write(processed_data)
                    sys.stdout.flush()
                
                # Check if process is still running
                if process.poll() is not None:
                    break
            
            # Clean up
            process.terminate()
            return process.wait()
            
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)

def main():
    parser = argparse.ArgumentParser(description='Run command with named message routing')
    parser.add_argument('command', nargs='+', help='Command to run')
    parser.add_argument('--config', help='Config file path')
    
    args = parser.parse_args()
    
    router = MessageRouter(args.config)
    exit_code = router.run_command(args.command)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()